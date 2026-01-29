from __future__ import annotations

import csv
import json
import os
import time
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import aiohttp
from pydantic import BaseModel, Field, ValidationError

from .agent_core.determinism import set_determinism
from .eval.rubric import evaluate_answer
from .tools.citation_validator import validate_citations


DEFAULT_MAX_QUESTIONS = 50


class EvalRequest(BaseModel):
    participants: dict[str, str]
    config: dict[str, Any] = Field(default_factory=dict)


@dataclass
class EvalConfig:
    allow_network: bool
    max_questions: int
    seed: int
    dataset_path: str
    timeout_seconds: float
    participant_role: str


@dataclass
class ParticipantAnswer:
    text: str
    raw: dict[str, Any] | None
    context_id: str | None
    error: str | None = None


def _get_config_value(config: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in config:
            return config[key]
    return default


def _resolve_dataset_path(config: dict[str, Any]) -> str:
    candidate = _get_config_value(config, "datasetPath", "dataset_path")
    if candidate:
        return os.path.abspath(candidate)
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "public.csv")
    )


def parse_eval_config(config: dict[str, Any]) -> EvalConfig:
    allow_network = bool(
        _get_config_value(config, "allowNetwork", "allow_network", default=False)
    )
    max_questions = int(
        _get_config_value(config, "maxQuestions", "max_questions", default=DEFAULT_MAX_QUESTIONS)
    )
    max_questions = max(1, min(max_questions, DEFAULT_MAX_QUESTIONS))
    seed = int(_get_config_value(config, "seed", default=42))
    timeout_seconds = float(
        _get_config_value(config, "timeoutSeconds", "timeout_seconds", default=120)
    )
    participant_role = str(
        _get_config_value(config, "participantRole", "participant_role", default="participant")
    )
    dataset_path = _resolve_dataset_path(config)
    return EvalConfig(
        allow_network=allow_network,
        max_questions=max_questions,
        seed=seed,
        dataset_path=dataset_path,
        timeout_seconds=timeout_seconds,
        participant_role=participant_role,
    )


def load_questions(csv_path: str) -> list[dict[str, Any]]:
    with open(csv_path, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [row for row in reader]


def merge_parts(parts: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        if "text" in part and isinstance(part["text"], str):
            chunks.append(part["text"])
            continue
        if "data" in part and isinstance(part["data"], dict):
            data_payload = part["data"].get("data", part["data"])
            try:
                chunks.append(json.dumps(data_payload, ensure_ascii=False))
            except TypeError:
                chunks.append(str(data_payload))
    return "\n".join(chunk for chunk in chunks if chunk).strip()


def extract_text_from_message(message: dict[str, Any]) -> str:
    if not isinstance(message, dict):
        return ""
    parts = message.get("content")
    if parts is None:
        parts = message.get("parts")
    return merge_parts(parts or [])


def extract_text_from_task(task: dict[str, Any]) -> str:
    if not isinstance(task, dict):
        return ""
    chunks: list[str] = []
    status_message = task.get("status", {}).get("message")
    if isinstance(status_message, dict):
        chunks.append(extract_text_from_message(status_message))
    for artifact in task.get("artifacts", []) or []:
        if isinstance(artifact, dict):
            chunks.append(merge_parts(artifact.get("parts", [])))
    return "\n".join(chunk for chunk in chunks if chunk).strip()


async def fetch_agent_card(
    session: aiohttp.ClientSession, base_url: str, timeout: float
) -> tuple[dict[str, Any], str]:
    card_url = base_url.rstrip("/") + "/.well-known/agent-card.json"
    async with session.get(card_url, timeout=timeout) as response:
        response.raise_for_status()
        card = await response.json()
    agent_url = str(card.get("url") or base_url).rstrip("/")
    return card, agent_url


async def send_message(
    session: aiohttp.ClientSession,
    agent_url: str,
    question: str,
    context_id: str,
    message_id: str,
    timeout: float,
) -> ParticipantAnswer:
    payload: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": uuid4().hex,
        "method": "message/send",
        "params": {
            "message": {
                "kind": "message",
                "messageId": message_id,
                "contextId": context_id,
                "role": "user",
                "parts": [{"kind": "text", "text": question}],
            },
            "configuration": {"acceptedOutputModes": ["text"]},
        },
    }
    try:
        async with session.post(
            agent_url.rstrip("/") + "/",
            json=payload,
            timeout=timeout,
        ) as response:
            response.raise_for_status()
            data = await response.json()
    except Exception as exc:  # noqa: BLE001 - capture transport errors
        return ParticipantAnswer(text="", raw=None, context_id=context_id, error=str(exc))

    payload_result = data.get("result") if isinstance(data, dict) else None
    if isinstance(payload_result, dict):
        envelope = payload_result
    else:
        envelope = data

    answer_text = ""
    response_context = None
    if isinstance(envelope, dict):
        if "message" in envelope and isinstance(envelope.get("message"), dict):
            answer_text = extract_text_from_message(envelope.get("message", {}))
            response_context = envelope["message"].get("contextId")
        elif "task" in envelope and isinstance(envelope.get("task"), dict):
            answer_text = extract_text_from_task(envelope.get("task", {}))
            response_context = envelope["task"].get("contextId")
        elif envelope.get("kind") == "message":
            answer_text = merge_parts(envelope.get("parts") or envelope.get("content") or [])
            response_context = envelope.get("contextId")
        elif envelope.get("kind") == "task":
            answer_text = extract_text_from_task(envelope)
            response_context = envelope.get("contextId")

    return ParticipantAnswer(
        text=answer_text,
        raw=data,
        context_id=response_context or context_id,
    )


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for item in results if item.get("score", {}).get("passed"))
    score_sum = sum(float(item.get("score", {}).get("score", 0.0)) for item in results)
    citation_valid = sum(
        1 for item in results if item.get("citations", {}).get("valid")
    )
    errors = sum(1 for item in results if item.get("error"))
    return {
        "total": total,
        "passed": passed,
        "average_score": score_sum / total if total else 0.0,
        "citation_valid": citation_valid,
        "errors": errors,
    }


async def evaluate_participant(
    role: str,
    url: str,
    questions: list[dict[str, Any]],
    config: EvalConfig,
) -> dict[str, Any]:
    set_determinism(config.seed)
    results: list[dict[str, Any]] = []
    start = time.perf_counter()

    async with aiohttp.ClientSession() as session:
        try:
            _, agent_url = await fetch_agent_card(
                session, url, config.timeout_seconds
            )
        except Exception as exc:  # noqa: BLE001 - surface connection errors
            summary = summarize_results([])
            summary["duration_seconds"] = round(time.perf_counter() - start, 3)
            summary["errors"] = 1
            return {
                "role": role,
                "url": url,
                "summary": summary,
                "results": [],
                "error": str(exc),
            }
        for idx, row in enumerate(questions):
            question = (row.get("Question") or "").strip()
            rubric = row.get("Rubric") or ""
            context_id = f"eval-{config.seed}-{role}-{idx}"
            message_id = f"msg-{config.seed}-{role}-{idx}"
            answer = await send_message(
                session,
                agent_url,
                question,
                context_id,
                message_id,
                config.timeout_seconds,
            )
            if answer.error:
                results.append(
                    {
                        "question": question,
                        "answer": "",
                        "score": {"passed": False, "score": 0.0, "details": []},
                        "citations": {"valid": False, "missing": [], "cited": []},
                        "error": answer.error,
                    }
                )
                continue

            citations = validate_citations(answer.text)
            scoring = evaluate_answer(answer.text, rubric)
            results.append(
                {
                    "question": question,
                    "answer": answer.text,
                    "score": scoring,
                    "citations": citations,
                    "error": None,
                }
            )

    summary = summarize_results(results)
    summary["duration_seconds"] = round(time.perf_counter() - start, 3)
    return {
        "role": role,
        "url": url,
        "summary": summary,
        "results": results,
    }


async def run_assessment(request_json: str) -> tuple[dict[str, Any], EvalConfig]:
    try:
        request = EvalRequest.model_validate_json(request_json)
    except ValidationError as exc:
        raise ValueError(exc.json()) from exc

    config = parse_eval_config(request.config)
    if config.participant_role not in request.participants:
        raise ValueError(
            f"Missing required participant role '{config.participant_role}'."
        )

    questions = load_questions(config.dataset_path)[: config.max_questions]
    participants = {}
    for role, url in request.participants.items():
        participants[role] = await evaluate_participant(
            role,
            url,
            questions,
            config,
        )

    winner = max(
        participants.values(),
        key=lambda item: item.get("summary", {}).get("average_score", 0.0),
    )

    result = {
        "winner": winner.get("role"),
        "participants": participants,
        "dataset": os.path.basename(config.dataset_path),
        "max_questions": config.max_questions,
        "seed": config.seed,
    }

    return result, config

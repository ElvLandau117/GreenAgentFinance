import argparse
import asyncio
import csv
import json
import os
from datetime import datetime

from ..agent_core.get_agent import Parameters, get_agent
from ..agent_core.determinism import set_determinism
from .rubric import evaluate_answer


def load_questions(csv_path: str) -> list[dict]:
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


async def run_eval(
    csv_path: str,
    output_path: str,
    model_name: str,
    max_turns: int,
    max_questions: int | None,
    seed: int,
):
    set_determinism(seed)
    questions = load_questions(csv_path)
    if max_questions:
        questions = questions[:max_questions]

    parameters = Parameters(
        model_name=model_name,
        max_turns=max_turns,
        tools=[
            "google_web_search",
            "retrieve_information",
            "parse_cached_html",
            "edgar_search",
        ],
        llm_config={"temperature": 0.0, "max_output_tokens": 4096},
    )
    agent = get_agent(parameters)

    results = []
    for row in questions:
        question = row.get("Question", "")
        rubric = row.get("Rubric", "")
        answer, metadata = await agent.run(question)
        scoring = evaluate_answer(answer, rubric)
        results.append(
            {
                "question": question,
                "answer": answer,
                "score": scoring,
                "metadata": metadata,
            }
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


def main():
    parser = argparse.ArgumentParser(description="Run offline public.csv evaluation")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to public.csv",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get(
            "FINANCE_GREEN_MODEL", "anthropic/claude-sonnet-4-5-20250929"
        ),
    )
    parser.add_argument("--max-turns", type=int, default=50)
    parser.add_argument("--max-questions", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    output_path = args.output or os.path.join(
        "results", f"public_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )

    asyncio.run(
        run_eval(
            csv_path=args.input,
            output_path=output_path,
            model_name=args.model,
            max_turns=args.max_turns,
            max_questions=args.max_questions,
            seed=args.seed,
        )
    )


if __name__ == "__main__":
    main()

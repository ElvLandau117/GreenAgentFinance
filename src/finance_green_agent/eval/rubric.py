import ast
from typing import Any

from ..tools.unit_normalizer import normalize_text


def _parse_rubric(rubric_str: str) -> list[dict[str, Any]]:
    if not rubric_str:
        return []
    try:
        data = ast.literal_eval(rubric_str)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def evaluate_answer(answer_text: str, rubric_str: str) -> dict[str, Any]:
    rubric_items = _parse_rubric(rubric_str)
    if not rubric_items:
        return {"passed": False, "score": 0.0, "details": []}

    normalized_answer = normalize_text(answer_text)
    details = []
    passes = []

    for item in rubric_items:
        operator = (item.get("operator") or "").lower()
        criteria = item.get("criteria") or ""
        normalized_criteria = normalize_text(criteria)

        if operator == "correctness":
            ok = normalized_criteria in normalized_answer
        elif operator == "contradiction":
            ok = normalized_criteria not in normalized_answer
        else:
            ok = False

        details.append(
            {
                "operator": operator,
                "criteria": criteria,
                "passed": ok,
            }
        )
        passes.append(ok)

    score = sum(1 for p in passes if p) / len(passes)
    return {"passed": all(passes), "score": score, "details": details}

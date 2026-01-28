import argparse
import json
import os
from datetime import datetime


def project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def default_prd() -> dict:
    return {
        "project": "finance-green-agent",
        "branchName": "ralph/finance-green-agent",
        "description": "Offline-first finance agent with manual A2A endpoints",
        "userStories": [
            {
                "id": "US-001",
                "title": "Manual A2A server",
                "description": "Implement /manifest, /start_task, /message in FastAPI.",
                "acceptanceCriteria": ["Endpoints exist", "Schemas validated"],
                "priority": 1,
                "passes": False,
                "notes": "",
            },
            {
                "id": "US-002",
                "title": "Offline tools",
                "description": "Cache-backed web + EDGAR search with graceful misses.",
                "acceptanceCriteria": ["Cache manifest loader", "Offline miss handling"],
                "priority": 2,
                "passes": False,
                "notes": "",
            },
            {
                "id": "US-003",
                "title": "Eval harness",
                "description": "Run public.csv with rubric scoring.",
                "acceptanceCriteria": ["public_eval.py exists", "rubric scoring works"],
                "priority": 3,
                "passes": False,
                "notes": "",
            },
        ],
    }


def load_or_init_prd(prd_path: str) -> dict:
    if os.path.exists(prd_path):
        with open(prd_path, "r", encoding="utf-8") as f:
            return json.load(f)
    prd = default_prd()
    with open(prd_path, "w", encoding="utf-8") as f:
        json.dump(prd, f, indent=2)
    return prd


def check_story(story_id: str, root: str) -> bool:
    if story_id == "US-001":
        return os.path.exists(os.path.join(root, "src", "finance_green_agent", "server.py"))
    if story_id == "US-002":
        return os.path.exists(os.path.join(root, "src", "finance_green_agent", "tools", "offline_web_search.py"))
    if story_id == "US-003":
        return os.path.exists(os.path.join(root, "src", "finance_green_agent", "eval", "public_eval.py"))
    return False


def append_progress(progress_path: str, message: str) -> None:
    with open(progress_path, "a", encoding="utf-8") as f:
        f.write(message + "\n")


def main():
    parser = argparse.ArgumentParser(description="Python Ralph gate runner")
    parser.add_argument("--max-iterations", type=int, default=16)
    args = parser.parse_args()

    root = project_root()
    prd_path = os.path.join(root, "prd.json")
    progress_path = os.path.join(root, "progress.txt")

    if not os.path.exists(progress_path):
        with open(progress_path, "w", encoding="utf-8") as f:
            f.write("# Ralph Progress Log\n")
            f.write(f"Started: {datetime.now().isoformat()}\n")
            f.write("---\n")

    prd = load_or_init_prd(prd_path)

    for iteration in range(1, args.max_iterations + 1):
        append_progress(progress_path, f"Iteration {iteration} @ {datetime.now().isoformat()}")
        updated = False
        for story in prd.get("userStories", []):
            if not story.get("passes", False):
                passes = check_story(story.get("id", ""), root)
                story["passes"] = passes
                story["notes"] = "Auto-check passed" if passes else "Pending"
                updated = True
        if updated:
            with open(prd_path, "w", encoding="utf-8") as f:
                json.dump(prd, f, indent=2)

    append_progress(progress_path, "Ralph gate completed.")


if __name__ == "__main__":
    main()

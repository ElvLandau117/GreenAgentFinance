import json
import re
from typing import Any

from .cache_manifest import CacheManifest


def extract_citations(answer_text: str) -> list[dict[str, Any]]:
    match = re.search(r"(\{\s*\"sources\".*\})", answer_text, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []
    sources = data.get("sources", []) if isinstance(data, dict) else []
    return sources if isinstance(sources, list) else []


def validate_citations(answer_text: str) -> dict[str, Any]:
    manifest = CacheManifest()
    cited = extract_citations(answer_text)
    manifest_ids = {entry.source_id for entry in manifest.entries}
    missing = []
    for source in cited:
        source_id = source.get("id") if isinstance(source, dict) else None
        if source_id and source_id not in manifest_ids:
            missing.append(source_id)
    return {"cited": cited, "missing": missing, "valid": len(missing) == 0}

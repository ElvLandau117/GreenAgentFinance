import json
import os
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    source_id: str
    source_type: str
    title: str | None
    url: str | None
    queries: list[str]
    local_path: str | None
    metadata: dict[str, Any]


class CacheManifest:
    def __init__(self, cache_dir: str | None = None):
        self.cache_dir = cache_dir or os.environ.get("FINANCE_GREEN_CACHE_DIR", "cache")
        self.manifest_path = os.path.join(self.cache_dir, "manifest.json")
        self.entries: list[CacheEntry] = []
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.manifest_path):
            self.entries = []
            return
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        entries = []
        for item in raw.get("entries", raw if isinstance(raw, list) else []):
            entries.append(
                CacheEntry(
                    source_id=item.get("source_id") or item.get("id") or "",
                    source_type=item.get("type") or item.get("source_type") or "",
                    title=item.get("title"),
                    url=item.get("url") or item.get("original_url"),
                    queries=item.get("queries") or item.get("query", []) or [],
                    local_path=item.get("local_path") or item.get("path"),
                    metadata=item.get("metadata") or {},
                )
            )
        self.entries = entries

    def search_web(self, query: str, top_n: int = 10) -> list[CacheEntry]:
        query_lower = query.lower()
        matches = []
        for entry in self.entries:
            if entry.source_type != "web":
                continue
            if query_lower in (entry.title or "").lower():
                matches.append(entry)
                continue
            if query_lower in (entry.url or "").lower():
                matches.append(entry)
                continue
            for q in entry.queries:
                if query_lower in str(q).lower():
                    matches.append(entry)
                    break
        return matches[:top_n]

    def search_sec(
        self,
        query: str,
        form_types: list[str] | None,
        ciks: list[str] | None,
        top_n: int = 10,
    ) -> list[CacheEntry]:
        query_lower = query.lower()
        matches = []
        for entry in self.entries:
            if entry.source_type != "sec":
                continue
            entry_meta = entry.metadata or {}
            entry_forms = [ft.lower() for ft in entry_meta.get("form_types", [])]
            entry_ciks = [str(cik) for cik in entry_meta.get("ciks", [])]

            if form_types:
                if not any(ft.lower() in entry_forms for ft in form_types):
                    continue
            if ciks:
                if not any(str(cik) in entry_ciks for cik in ciks):
                    continue

            if query_lower in (entry.title or "").lower():
                matches.append(entry)
                continue
            if query_lower in (entry.url or "").lower():
                matches.append(entry)
                continue
            for q in entry.queries:
                if query_lower in str(q).lower():
                    matches.append(entry)
                    break
        return matches[:top_n]

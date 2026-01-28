from ..agent_core.tools_base import Tool
from .cache_manifest import CacheManifest


class OfflineEdgarSearch(Tool):
    name: str = "edgar_search"
    description: str = "Offline cache-backed EDGAR search"
    input_arguments: dict = {
        "query": {
            "type": "string",
            "description": "Keyword or phrase to search",
        },
        "form_types": {
            "type": "array",
            "description": "SEC form types",
            "items": {"type": "string"},
        },
        "ciks": {
            "type": "array",
            "description": "CIKs to filter",
            "items": {"type": "string"},
        },
        "start_date": {
            "type": "string",
            "description": "Start date yyyy-mm-dd",
        },
        "end_date": {
            "type": "string",
            "description": "End date yyyy-mm-dd",
        },
        "page": {
            "type": "string",
            "description": "Page number",
        },
        "top_n_results": {
            "type": "integer",
            "description": "Max results",
        },
    }
    required_arguments: list[str] = [
        "query",
        "form_types",
        "ciks",
        "start_date",
        "end_date",
        "page",
        "top_n_results",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manifest = CacheManifest()

    async def call_tool(self, arguments: dict) -> list[dict]:
        query = arguments.get("query", "")
        form_types = arguments.get("form_types") or []
        ciks = arguments.get("ciks") or []
        top_n = int(arguments.get("top_n_results") or 10)

        results = self.manifest.search_sec(query, form_types, ciks, top_n=top_n)
        if not results:
            return [{"offline_miss": True, "query": query, "results": []}]

        formatted = []
        for entry in results:
            formatted.append(
                {
                    "source_id": entry.source_id,
                    "title": entry.title,
                    "url": entry.url,
                    "local_path": entry.local_path,
                    "metadata": entry.metadata,
                }
            )
        return formatted

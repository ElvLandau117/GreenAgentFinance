from ..agent_core.tools_base import Tool
from .cache_manifest import CacheManifest


class OfflineGoogleWebSearch(Tool):
    name: str = "google_web_search"
    description: str = "Offline cache-backed web search"
    input_arguments: dict = {
        "search_query": {
            "type": "string",
            "description": "The query to search for",
        },
        "top_n_results": {
            "type": "integer",
            "description": "Optional max results",
        },
    }
    required_arguments: list[str] = ["search_query"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manifest = CacheManifest()

    async def call_tool(self, arguments: dict) -> list[dict]:
        query = arguments.get("search_query", "")
        top_n = int(arguments.get("top_n_results") or 10)

        results = self.manifest.search_web(query, top_n=top_n)
        if not results:
            return [{"offline_miss": True, "query": query, "results": []}]

        formatted = []
        for entry in results:
            formatted.append(
                {
                    "title": entry.title,
                    "link": entry.url,
                    "source_id": entry.source_id,
                    "local_path": entry.local_path,
                    "metadata": entry.metadata,
                }
            )
        return formatted

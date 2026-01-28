import os
from bs4 import BeautifulSoup

from ..agent_core.tools_base import Tool
from .cache_manifest import CacheManifest


class ParseCachedHtml(Tool):
    name: str = "parse_cached_html"
    description: str = "Parse cached HTML/text from local cache and store in data_storage"
    input_arguments: dict = {
        "source_id": {"type": "string", "description": "Cache source ID"},
        "path": {"type": "string", "description": "Direct local path override"},
        "key": {"type": "string", "description": "Key to store in data_storage"},
    }
    required_arguments: list[str] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manifest = CacheManifest()

    async def call_tool(self, arguments: dict, data_storage: dict) -> list[str]:
        source_id = arguments.get("source_id")
        path = arguments.get("path")
        key = arguments.get("key")

        if not path and source_id:
            for entry in self.manifest.entries:
                if entry.source_id == source_id:
                    path = entry.local_path
                    break

        if not path:
            raise ValueError("No path or source_id provided for cached parsing")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Cached file not found: {path}")

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        text = content
        if "<html" in content.lower() or "<body" in content.lower():
            soup = BeautifulSoup(content, "html.parser")
            for script_or_style in soup(["script", "style"]):
                script_or_style.extract()
            text = "\n".join(
                chunk.strip()
                for line in soup.get_text().splitlines()
                for chunk in line.split("  ")
                if chunk.strip()
            )

        storage_key = key or source_id or os.path.basename(path)
        data_storage[storage_key] = text

        return [
            f"SUCCESS: Stored parsed content under key '{storage_key}'.",
            f"Keys available: {', '.join(data_storage.keys())}",
        ]

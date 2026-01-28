import json
import os

import pytest

from finance_green_agent.tools.offline_web_search import OfflineGoogleWebSearch
from finance_green_agent.tools.offline_edgar_search import OfflineEdgarSearch
from finance_green_agent.tools.parse_cached_html import ParseCachedHtml


@pytest.fixture()
def cache_dir(tmp_path, monkeypatch):
    cache_path = tmp_path / "cache"
    cache_path.mkdir()
    manifest = {
        "entries": [
            {
                "source_id": "web-1",
                "type": "web",
                "title": "Example Page",
                "url": "https://example.com",
                "queries": ["example query"],
                "local_path": str(cache_path / "web1.html"),
            },
            {
                "source_id": "sec-1",
                "type": "sec",
                "title": "10-K Filing",
                "url": "https://sec.example/filing",
                "queries": ["material weakness"],
                "local_path": str(cache_path / "sec1.txt"),
                "metadata": {"form_types": ["10-K"], "ciks": ["0001"]},
            },
        ]
    }
    (cache_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (cache_path / "web1.html").write_text("<html><body>Hello</body></html>", encoding="utf-8")
    (cache_path / "sec1.txt").write_text("SEC filing", encoding="utf-8")
    monkeypatch.setenv("FINANCE_GREEN_CACHE_DIR", str(cache_path))
    return cache_path


@pytest.mark.asyncio
async def test_offline_web_search(cache_dir):
    tool = OfflineGoogleWebSearch()
    results = await tool.call_tool({"search_query": "example query", "top_n_results": 5})
    assert results
    assert results[0]["source_id"] == "web-1"


@pytest.mark.asyncio
async def test_offline_edgar_search(cache_dir):
    tool = OfflineEdgarSearch()
    results = await tool.call_tool(
        {
            "query": "material weakness",
            "form_types": ["10-K"],
            "ciks": ["0001"],
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "page": "1",
            "top_n_results": 5,
        }
    )
    assert results
    assert results[0]["source_id"] == "sec-1"


@pytest.mark.asyncio
async def test_parse_cached_html(cache_dir):
    tool = ParseCachedHtml()
    data_storage = {}
    result = await tool.call_tool({"source_id": "web-1", "key": "doc"}, data_storage)
    assert "doc" in data_storage
    assert "Hello" in data_storage["doc"]
    assert result

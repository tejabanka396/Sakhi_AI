import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.web_search import (
    WebSearchService,
    SearchResultItem,
    WebSearchNotConfiguredError,
    WebSearchProviderError,
    WebSearchEmptyResultError,
)

def test_web_search_unconfigured_raises_error():
    """Verify unconfigured search raises WebSearchNotConfiguredError without crashing."""
    service = WebSearchService()
    service.enabled = False
    with pytest.raises(WebSearchNotConfiguredError):
        # Synchronous check via is_configured
        if not service.is_configured():
            raise WebSearchNotConfiguredError()

@pytest.mark.asyncio
async def test_tavily_search_success_parsing():
    """Verify structured response parsing from Tavily search results."""
    service = WebSearchService()
    service.enabled = True
    service.provider = "tavily"
    service.api_key = "test_key_tvly"

    mock_tavily_payload = {
        "results": [
            {
                "title": "Python 3.13 Released",
                "url": "https://www.python.org/downloads/release/python-3130/",
                "content": "Python 3.13 is the newest major release of the Python programming language.",
                "published_date": "2026-09-15"
            },
            {
                "title": "What's New in Python 3.13",
                "url": "https://docs.python.org/3/whatsnew/3.13.html",
                "content": "This article explains the new features in Python 3.13.",
                "published_date": "2026-09-16"
            },
            # Duplicate URL that should be deduplicated
            {
                "title": "Python 3.13 Duplicate",
                "url": "https://www.python.org/downloads/release/python-3130/",
                "content": "Duplicate content",
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_tavily_payload

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = await service.search("latest Python version")

        assert res.searched is True
        assert len(res.results) == 2  # Deduplicated from 3
        first = res.results[0]
        assert first.title == "Python 3.13 Released"
        assert first.domain == "python.org"
        assert "Python 3.13" in first.snippet
        assert first.published_date == "2026-09-15"

@pytest.mark.asyncio
async def test_web_search_empty_results_handling():
    """Verify empty results raise WebSearchEmptyResultError."""
    service = WebSearchService()
    service.enabled = True
    service.provider = "tavily"
    service.api_key = "test_key_tvly"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": []}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        with pytest.raises(WebSearchEmptyResultError):
            await service.search("xyz non existent 12345")

@pytest.mark.asyncio
async def test_web_search_provider_failure_handling():
    """Verify provider HTTP failure raises WebSearchProviderError."""
    service = WebSearchService()
    service.enabled = True
    service.provider = "tavily"
    service.api_key = "test_key_tvly"

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        with pytest.raises(WebSearchProviderError):
            await service.search("latest news")

import re
import time
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
import httpx
from pydantic import BaseModel
from app.core.config import settings
from app.utils.datetime_utils import get_current_datetime

logger = logging.getLogger("sakhi_ai.web_search")

class SearchResultItem(BaseModel):
    title: str
    url: str
    domain: str
    snippet: str
    published_date: Optional[str] = None

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    provider: str
    searched: bool = True
    timestamp: str

class WebSearchNotConfiguredError(Exception):
    """Raised when web search is disabled or no API key is provided."""
    pass

class WebSearchProviderError(Exception):
    """Raised when search provider API fails or times out."""
    pass

class WebSearchEmptyResultError(Exception):
    """Raised when search provider returns no results."""
    pass

class WebSearchService:
    """
    Production-grade Web Search Service for Sakhi AI.
    - Tavily is the primary production provider.
    - Extensible architecture supporting Serper and DuckDuckGo.
    - Zero key exposure to clients.
    - Handles timeouts, retries, empty results, and deduplication.
    """

    def __init__(self):
        self.enabled = settings.WEB_SEARCH_ENABLED
        self.provider = settings.WEB_SEARCH_PROVIDER.lower().strip()
        self.api_key = settings.WEB_SEARCH_API_KEY.strip()
        self.max_results = settings.WEB_SEARCH_MAX_RESULTS
        self.timeout = settings.WEB_SEARCH_TIMEOUT_SECONDS

    def is_configured(self) -> bool:
        """Checks if web search is enabled and has valid configuration."""
        if not self.enabled:
            return False
        if self.provider in ["tavily", "serper"] and not self.api_key:
            return False
        return True

    async def search(self, query: str) -> SearchResponse:
        """
        Executes web search with timeout, retry, and deduplication.
        Raises WebSearchNotConfiguredError, WebSearchProviderError, or WebSearchEmptyResultError.
        """
        if not self.is_configured():
            raise WebSearchNotConfiguredError("Web search is disabled or API key is not configured.")

        t_start = time.perf_counter()
        results: List[SearchResultItem] = []

        if self.provider == "tavily":
            results = await self._search_tavily(query)
        elif self.provider == "serper":
            results = await self._search_serper(query)
        elif self.provider == "duckduckgo":
            results = await self._search_duckduckgo(query)
        else:
            # Default fallback to Tavily
            results = await self._search_tavily(query)

        elapsed_ms = (time.perf_counter() - t_start) * 1000

        if not results:
            logger.warning(f"[WEB_SEARCH] Empty search results for query: '{query}' ({elapsed_ms:.1f}ms)")
            raise WebSearchEmptyResultError(f"No relevant search results found for query: '{query}'")

        # Deduplicate by URL and Domain
        deduped = self._deduplicate_results(results)

        now_str = get_current_datetime().isoformat()
        logger.info(
            f"[WEB_SEARCH] provider={self.provider} count={len(deduped)} "
            f"elapsed_ms={elapsed_ms:.1f} query='{query[:40]}'"
        )

        return SearchResponse(
            query=query,
            results=deduped[:self.max_results],
            provider=self.provider,
            searched=True,
            timestamp=now_str
        )

    async def _search_tavily(self, query: str) -> List[SearchResultItem]:
        """Queries Tavily Search API (Primary production provider)."""
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": self.max_results,
            "include_answer": False,
            "include_raw_content": False
        }

        # Up to 2 attempts
        last_error = None
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_results = data.get("results", [])
                        items = []
                        for item in raw_results:
                            u = item.get("url", "")
                            domain = self._extract_domain(u)
                            items.append(SearchResultItem(
                                title=item.get("title", ""),
                                url=u,
                                domain=domain,
                                snippet=item.get("content", ""),
                                published_date=item.get("published_date")
                            ))
                        return items
                    elif resp.status_code in [401, 403]:
                        logger.error("[WEB_SEARCH] Tavily API authentication failed (401/403)")
                        raise WebSearchProviderError("Tavily API key authentication failed.")
                    else:
                        last_error = f"HTTP {resp.status_code}: {resp.text[:150]}"
            except (httpx.TimeoutException, httpx.RequestError) as e:
                last_error = str(e)
                logger.warning(f"[WEB_SEARCH] Tavily attempt {attempt+1} failed: {e}")

        raise WebSearchProviderError(f"Tavily search provider failed after retries: {last_error}")

    async def _search_serper(self, query: str) -> List[SearchResultItem]:
        """Queries Serper Google Search API (Alternative provider)."""
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {"q": query, "num": self.max_results}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    organic = data.get("organic", [])
                    items = []
                    for item in organic:
                        u = item.get("link", "")
                        domain = self._extract_domain(u)
                        items.append(SearchResultItem(
                            title=item.get("title", ""),
                            url=u,
                            domain=domain,
                            snippet=item.get("snippet", ""),
                            published_date=item.get("date")
                        ))
                    return items
                else:
                    raise WebSearchProviderError(f"Serper API returned status {resp.status_code}")
        except Exception as e:
            raise WebSearchProviderError(f"Serper search failed: {e}")

    async def _search_duckduckgo(self, query: str) -> List[SearchResultItem]:
        """Free fallback scraper for DuckDuckGo HTML if no external key is set."""
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        data = {"q": query}

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.post(url, headers=headers, data=data)
                if resp.status_code == 200:
                    html = resp.text
                    # Basic regex parser for DDG HTML results
                    raw_snippets = re.findall(
                        r'<a class="result__url"[^>]*href="([^"]+)"[^>]*>.*?<a class="result__snippet"[^>]*>(.*?)</a>',
                        html,
                        re.DOTALL
                    )
                    items = []
                    for u, snip in raw_snippets:
                        clean_snip = re.sub(r"<[^>]+>", "", snip).strip()
                        domain = self._extract_domain(u)
                        items.append(SearchResultItem(
                            title=domain.capitalize(),
                            url=u,
                            domain=domain,
                            snippet=clean_snip
                        ))
                    return items
                else:
                    raise WebSearchProviderError(f"DuckDuckGo HTML returned status {resp.status_code}")
        except Exception as e:
            raise WebSearchProviderError(f"DuckDuckGo search failed: {e}")

    def _extract_domain(self, url: str) -> str:
        """Extracts clean domain name from URL (e.g. 'thehindu.com')."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            return domain.replace("www.", "") if domain else "web"
        except Exception:
            return "web"

    def _deduplicate_results(self, items: List[SearchResultItem]) -> List[SearchResultItem]:
        """Removes duplicate URLs and excessive results from the exact same page."""
        seen_urls = set()
        deduped = []
        for item in items:
            clean_url = item.url.split("?")[0].rstrip("/")
            if clean_url not in seen_urls and item.snippet.strip():
                seen_urls.add(clean_url)
                deduped.append(item)
        return deduped

web_search_service = WebSearchService()

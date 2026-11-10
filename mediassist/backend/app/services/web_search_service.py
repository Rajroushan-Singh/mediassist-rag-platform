import logging
import re

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Conservative filters: do not send first-person or identifiable-looking
# messages to an external search provider. These checks reduce risk; they are
# not a complete de-identification system, so web search remains opt-in.
_PERSONAL_OR_IDENTIFIER = re.compile(
    r"\b(i|me|my|mine|we|our|us|he|she|they|his|her|their|father|mother|"
    r"husband|wife|son|daughter|child|patient)\b|"
    r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\b\d{3,}\b|"
    r"\b(?:born|diagnosed|taking|prescribed|allergic|medical record)\b",
    re.IGNORECASE,
)


class WebSearchService:
    async def search_generic_health(self, query: str) -> list[dict]:
        if not settings.ENABLE_WEB_SEARCH or not settings.SERP_API_KEY:
            return []
        safe_query = " ".join(query.split())[:180]
        if not safe_query or _PERSONAL_OR_IDENTIFIER.search(safe_query):
            return []

        params = {
            "engine": "google",
            "q": safe_query,
            "api_key": settings.SERP_API_KEY,
            "num": 5,
        }
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(8.0)) as client:
                response = await client.get("https://serpapi.com/search.json", params=params)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Optional public search failed (%s)", type(exc).__name__)
            return []

        results = []
        for item in payload.get("organic_results", [])[:5]:
            title = str(item.get("title") or "").strip()
            snippet = str(item.get("snippet") or "").strip()
            link = str(item.get("link") or "").strip()
            if not title or not snippet or not link.startswith("https://"):
                continue
            results.append(
                {
                    "title": title[:300],
                    "source": "Public web search (supplemental; not clinical review)",
                    "url": link[:2000],
                    "content": snippet[:1200],
                    "kind": "web_search",
                }
            )
        return results


web_search_service = WebSearchService()

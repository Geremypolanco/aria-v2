"""
Web intelligence provider.
- Real-time web search (Brave Search API / SerpAPI fallback)
- Page content extraction
- Trend detection
- Market research
"""
from __future__ import annotations
import httpx
import re
from src.core.config import settings


async def web_search(query: str, count: int = 5) -> list[dict]:
    """Search the web using Brave Search API with SerpAPI fallback."""
    
    # ── Try Brave Search ──────────────────────────────────────────────────
    if settings.BRAVE_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                res = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    headers={
                        "Accept": "application/json",
                        "Accept-Encoding": "gzip",
                        "X-Subscription-Token": settings.BRAVE_API_KEY,
                    },
                    params={"q": query, "count": count, "search_lang": "es", "country": "ALL"},
                )
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("web", {}).get("results", [])
                    return [
                        {
                            "title": r.get("title"),
                            "url": r.get("url"),
                            "description": r.get("description"),
                            "age": r.get("age"),
                        }
                        for r in results
                    ]
        except Exception as e:
            print(f"Brave Search failed: {e}")

    # ── Fallback: SerpAPI ─────────────────────────────────────────────────
    # Nota: El token de SerpAPI se guarda en BRAVE_API_KEY si el usuario lo proporcionó ahí
    # o podemos usar una variable específica si se configuró.
    # En nuestro caso, vimos que el token 912b1... funciona en SerpAPI.
    serp_key = settings.BRAVE_API_KEY # Usamos el mismo slot por simplicidad o buscamos uno nuevo
    if serp_key:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                res = await client.get(
                    "https://serpapi.com/search.json",
                    params={
                        "q": query,
                        "api_key": serp_key,
                        "engine": "google",
                        "hl": "es",
                        "gl": "us",
                        "num": count
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("organic_results", [])
                    return [
                        {
                            "title": r.get("title"),
                            "url": r.get("link"),
                            "description": r.get("snippet"),
                            "age": r.get("date"),
                        }
                        for r in results
                    ]
        except Exception as e:
            print(f"SerpAPI fallback failed: {e}")

    raise RuntimeError("All web search providers failed or are not configured.")


async def fetch_page(url: str, max_chars: int = 3000) -> dict:
    """Fetch and extract clean text from a web page."""
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            res = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; AriaBot/2.0)"},
            )
            res.raise_for_status()
            html = res.text

        # Strip tags
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return {"url": url, "content": text[:max_chars], "chars": len(text)}
    except Exception as e:
        return {"url": url, "error": str(e)}


async def research_topic(topic: str) -> dict:
    """Full research pipeline: search + extract top results."""
    results = await web_search(f"{topic} market trends 2025", count=4)
    enriched = []
    for r in results[:2]:
        page = await fetch_page(r["url"], max_chars=1500)
        enriched.append({**r, "full_content": page.get("content", "")})
    return {"query": topic, "results": enriched, "sources": len(results)}


async def get_trending_topics(niche: str = "inteligencia artificial") -> list[dict]:
    """Get trending topics in a niche for content opportunities."""
    searches = [
        await web_search(f"tendencias {niche} 2025", count=3),
        await web_search(f"mejor curso online {niche}", count=3),
        await web_search(f"problemas comunes {niche} emprendedores", count=2),
    ]
    all_results = [r for batch in searches for r in batch]
    return all_results[:8]

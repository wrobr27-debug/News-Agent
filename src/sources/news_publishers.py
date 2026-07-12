import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
import feedparser

from src.sources.government import NewsItem


PUBLISHER_SOURCES = [
    {
        "name": "Haribhoomi",
        "url": "https://www.haribhoomi.com/",
        "rss": None,
    },
    {
        "name": "Patrika Bilaspur",
        "url": "https://www.patrika.com/bilaspur-news/",
        "rss": None,
    },
    {
        "name": "Dainik Bhaskar Bilaspur",
        "url": "https://www.bhaskar.com/chhattisgarh/bilaspur/",
        "rss": None,
    },
    {
        "name": "The Hitavada",
        "url": "https://www.thehitavada.com/",
        "rss": "https://www.thehitavada.com/rss.xml",
    },
]


def _parse_rss(url: str, source_name: str) -> list[NewsItem]:
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:20]:
        items.append(NewsItem(
            source=source_name,
            title=entry.get("title", ""),
            url=entry.get("link", ""),
            summary=entry.get("summary", "")[:300],
            published_at=entry.get("published", datetime.now().isoformat())[:10],
            category="news",
        ))
    return items


def _scrape_site(url: str) -> str | None:
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def _extract_article_links(html: str, base_url: str) -> list[NewsItem]:
    soup = BeautifulSoup(html, "lxml")
    items = []
    seen = set()

    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        a = tag.find("a") or (tag if tag.name == "a" else None)
        if not a or not a.get("href"):
            continue
        text = tag.get_text(strip=True)
        if not text or len(text) < 20:
            continue
        url = urljoin(base_url, a["href"])
        if url in seen:
            continue
        seen.add(url)

        items.append(NewsItem(
            source="",
            title=text[:200],
            url=url,
            category="news",
        ))

    return items


def scrape_all() -> list[NewsItem]:
    all_items = []
    for source in PUBLISHER_SOURCES:
        try:
            if source.get("rss"):
                items = _parse_rss(source["rss"], source["name"])
                if items:
                    all_items.extend(items)
                    continue

            html = _scrape_site(source["url"])
            if not html:
                continue
            items = _extract_article_links(html, source["url"])
            for item in items:
                item.source = source["name"]
            all_items.extend(items)
        except Exception:
            continue
    return all_items

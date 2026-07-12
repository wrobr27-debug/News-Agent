import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from src.sources.government import NewsItem


EVENT_SOURCES = [
    {
        "name": "Allevents.in Bilaspur",
        "url": "https://allevents.in/bilaspur",
    },
    {
        "name": "Townscript Bilaspur",
        "url": "https://www.townscript.com/explore/bilaspur",
    },
]


def _fetch(url: str) -> str | None:
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def scrape_all() -> list[NewsItem]:
    items = []
    for source in EVENT_SOURCES:
        try:
            html = _fetch(source["url"])
            if not html:
                continue
            soup = BeautifulSoup(html, "lxml")
            seen = set()
            for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
                a = tag.find("a") or (tag if tag.name == "a" else None)
                if not a or not a.get("href"):
                    continue
                text = tag.get_text(strip=True)
                if not text or len(text) < 15:
                    continue
                url = urljoin(source["url"], a["href"])
                if url in seen:
                    continue
                seen.add(url)
                items.append(NewsItem(
                    source=source["name"],
                    title=text[:200],
                    url=url,
                    category="events",
                ))
        except Exception:
            continue
    return items

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
    {
        "name": "Nai Dunia Bilaspur",
        "url": "https://www.naidunia.com/chhattisgarh/bilaspur",
        "rss": "https://rss.jagran.com/naidunia/chhattisgarh/bilaspur.xml",
    },
    {
        "name": "CG Wall",
        "url": "https://cgwall.in/category/bilaspur/",
        "rss": "https://cgwall.in/category/bilaspur/feed",
    },
    {
        "name": "Easy News",
        "url": "https://easynews.co.in/",
        "rss": "https://easynews.co.in/feed",
    },
    {
        "name": "Lokswar",
        "url": "https://www.lokswar.in/",
        "rss": "https://www.lokswar.in/feed",
    },
]


def _parse_rss(url: str, source_name: str) -> list[NewsItem]:
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:20]:
        img = ""
        # 1. Check enclosures
        if entry.get("enclosures"):
            for enc in entry.enclosures:
                if enc.get("type", "").startswith("image/") or enc.get("url"):
                    img = enc.url
                    break
        # 2. Check media:content
        if not img and "media_content" in entry:
            media = entry.media_content
            if isinstance(media, list) and len(media) > 0:
                img = media[0].get("url", "")
            elif isinstance(media, dict):
                img = media.get("url", "")
        # 3. Check description / summary HTML for img tag
        if not img and (entry.get("summary") or entry.get("description")):
            desc = entry.get("summary") or entry.get("description")
            try:
                soup = BeautifulSoup(desc, "lxml")
                img_tag = soup.find("img")
                if img_tag and img_tag.get("src"):
                    img = img_tag["src"]
            except Exception:
                pass

        items.append(NewsItem(
            source=source_name,
            title=entry.get("title", ""),
            url=entry.get("link", ""),
            summary=entry.get("summary", "")[:300],
            published_at=entry.get("published", datetime.now().isoformat())[:10],
            category="news",
            image_url=img,
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

        img_url = ""
        try:
            # Find image inside the heading, next siblings, or parent card
            img_tag = tag.find("img")
            if not img_tag:
                for sib in tag.next_siblings:
                    if sib.name == "img":
                        img_tag = sib
                        break
                    if sib.name in ["div", "span"]:
                        img_tag = sib.find("img")
                        if img_tag:
                            break
            if not img_tag and tag.parent:
                img_tag = tag.parent.find("img")
            
            if img_tag and img_tag.get("src"):
                img_url = urljoin(base_url, img_tag["src"])
        except Exception:
            pass

        items.append(NewsItem(
            source="",
            title=text[:200],
            url=url,
            category="news",
            image_url=img_url,
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

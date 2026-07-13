import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
import re
from typing import Generator

from pydantic import BaseModel


class NewsItem(BaseModel):
    source: str
    title: str
    url: str
    summary: str = ""
    published_at: str = ""
    category: str = "general"
    image_url: str = ""


GOVERNMENT_SOURCES = [
    {
        "key": "district_administration",
        "name": "District Administration Bilaspur",
        "url": "https://bilaspur.gov.in/en/",
        "notice_base": "https://bilaspur.gov.in/en/notice_category/",
        "notice_categories": ["announcements", "recruitment", "tenders", "others"],
    },
    {
        "key": "nagar_nigam",
        "name": "Nagar Nigam Bilaspur",
        "url": "https://nigambilaspur.com/",
    },
    {
        "key": "police",
        "name": "Bilaspur Police",
        "url": "https://bilaspur.cgpolice.gov.in/",
    },
    {
        "key": "smart_city",
        "name": "Bilaspur Smart City",
        "url": "https://www.icccbilaspur.in/",
    },
    {
        "key": "cmo",
        "name": "CMO Chhattisgarh",
        "url": "https://cmo.cg.gov.in/",
    },
    {
        "key": "railway",
        "name": "Bilaspur Railway Division",
        "url": "https://secr.indianrailways.gov.in/view_section.jsp?id=0,4,2212,2270&lang=0",
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


def _extract_notices_from_homepage(html: str, base_url: str) -> list[NewsItem]:
    """Extract notice/announcement links from homepage."""
    soup = BeautifulSoup(html, "lxml")
    items = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(strip=True)
        if not text or len(text) < 10:
            continue
        if href.startswith("javascript:") or href == "#":
            continue

        full_url = urljoin(base_url, href)

        keywords = ["notice", "announce", "tender", "recruit", "admit", "result",
                     "exam", "interview", "appoint", "award", "scheme", "yojana",
                     "press release", "pressrelease", "whats new", "whatsnew",
                     "circular", "order", "notification", "admission", "election",
                     "auction", "expression of interest", "eo i", "corrigendum"]
        text_lower = text.lower()
        if not any(k in text_lower for k in keywords):
            continue
        if full_url in seen:
            continue
        seen.add(full_url)

        items.append(NewsItem(
            source="",
            title=text[:200],
            url=full_url,
            published_at=datetime.now().isoformat()[:10],
        ))

    return items


def _extract_all_links(html: str, base_url: str) -> list[NewsItem]:
    """Fallback: extract all meaningful links."""
    soup = BeautifulSoup(html, "lxml")
    items = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(strip=True)
        if not text or len(text) < 20:
            continue
        if href.startswith("javascript:") or href == "#":
            continue
        full_url = urljoin(base_url, href)
        if full_url in seen:
            continue
        seen.add(full_url)

        items.append(NewsItem(
            source="",
            title=text[:200],
            url=full_url,
            published_at=datetime.now().isoformat()[:10],
        ))

    return items


def _scrape_with_playwright(url: str) -> list[NewsItem]:
    """Use Playwright for JS-heavy sites like CMO."""
    from playwright.sync_api import sync_playwright

    items = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=10000)
            page.wait_for_timeout(2000)

            links = page.evaluate("""() => {
                const results = [];
                const seen = new Set();
                const tags = document.querySelectorAll('a, h2, h3, h4');
                for (const t of tags) {
                    const text = t.innerText?.trim();
                    const href = t.tagName === 'A' ? (t.href || '') : (t.querySelector('a')?.href || '');
                    if (text && text.length > 15 && !seen.has(text)) {
                        seen.add(text);
                        results.push({ text: text.slice(0, 200), href: href.slice(0, 200) });
                    }
                }
                return results;
            }""")

            for link in links:
                items.append(NewsItem(
                    source="",
                    title=link["text"],
                    url=link["href"] or url,
                    published_at=datetime.now().isoformat()[:10],
                ))
        except Exception:
            pass
        finally:
            browser.close()

    return items


def scrape_source(source: dict) -> list[NewsItem]:
    html = _fetch(source["url"])
    items = []

    if html:
        items = _extract_notices_from_homepage(html, source["url"])
        if not items:
            items = _extract_all_links(html, source["url"])

    if not items and source["key"] != "cmo":
        items = _scrape_with_playwright(source["url"])

    for item in items:
        item.source = source["name"]

    return items


def scrape_all() -> list[NewsItem]:
    all_items = []
    for source in GOVERNMENT_SOURCES:
        try:
            items = scrape_source(source)
            all_items.extend(items)
        except Exception:
            continue
    return all_items

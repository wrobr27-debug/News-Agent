import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

from src.sources.government import NewsItem, _fetch, _extract_notices_from_homepage, _extract_all_links


EDUCATION_SOURCES = [
    {
        "key": "ggv",
        "name": "Guru Ghasidas Vishwavidyalaya",
        "url": "https://www.ggu.ac.in/",
    },
    {
        "key": "abu",
        "name": "Atal Bihari Vajpayee University",
        "url": "https://www.abu.ac.in/",
    },
    {
        "key": "gec",
        "name": "Government Engineering College Bilaspur",
        "url": "https://gecbsp.ac.in/",
    },
]


def scrape_all() -> list[NewsItem]:
    all_items = []
    for source in EDUCATION_SOURCES:
        try:
            html = _fetch(source["url"])
            if not html:
                continue
            items = _extract_notices_from_homepage(html, source["url"])
            if not items:
                items = _extract_all_links(html, source["url"])
            for item in items:
                item.source = source["name"]
            all_items.extend(items)
        except Exception:
            continue
    return all_items

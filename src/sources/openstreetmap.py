import httpx
from datetime import datetime
from src.sources.government import NewsItem


SEARCH_QUERIES = [
    ("restaurant", "New Restaurant"),
    ("cafe", "New Cafe"),
    ("hotel", "New Hotel"),
    ("hospital", "New Clinic/Hospital"),
    ("gym", "New Gym"),
    ("pharmacy", "New Pharmacy"),
    ("supermarket", "New Supermarket"),
]


def _search_osm(category: str, label: str) -> list[NewsItem]:
    items = []
    try:
        resp = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": f"{category} in Bilaspur Chhattisgarh",
                "format": "json",
                "limit": 5,
            },
            headers={"User-Agent": "BilaspurNewsAgent/0.1"},
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json()
        for r in results:
            name = r.get("name", "")
            if not name:
                continue
            lat, lon = r.get("lat", ""), r.get("lon", "")
            map_url = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}"
            display = r.get("display_name", "")[:150]
            items.append(NewsItem(
                source="OpenStreetMap",
                title=f"{label}: {name}",
                url=map_url,
                summary=display,
                published_at=datetime.now().isoformat()[:10],
                category="business",
            ))
    except Exception:
        pass
    return items


def scrape_all() -> list[NewsItem]:
    items = []
    for osm_tag, label in SEARCH_QUERIES:
        items += _search_osm(osm_tag, label)
    return items

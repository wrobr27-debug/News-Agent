from datetime import datetime
from pathlib import Path
from src.database import is_duplicate, mark_seen, get_todays_items
from src.sources.government import NewsItem
from src.sources import government, education, news_publishers, youtube_monitor, openstreetmap, events
from src.config import settings
from src.summarizer import summarize_items


def _safe_collect(name: str, fn, *args, **kwargs) -> list[NewsItem]:
    try:
        print(f"  {name}...", end=" ")
        items = fn(*args, **kwargs)
        print(f"{len(items)} items")
        return items
    except Exception as e:
        print(f"ERROR: {e}")
        return []


SOCIAL_SCRAPERS_ENABLED = False


def collect_all(social: bool = False) -> list[NewsItem]:
    items = []

    items += _safe_collect("Tier 1 — Govt sources", government.scrape_all)
    items += _safe_collect("Tier 3 — Education", education.scrape_all)
    items += _safe_collect("Tier 4 — Businesses (OSM)", openstreetmap.scrape_all)
    items += _safe_collect("Tier 5 — Events", events.scrape_all)
    items += _safe_collect("Tier 6 — News publishers", news_publishers.scrape_all)
    items += _safe_collect("Tier 7 — YouTube", youtube_monitor.scrape_all, settings.youtube_api_key)

    if social or SOCIAL_SCRAPERS_ENABLED:
        items += _safe_collect("Tier 11 — Twitter", _scrape_twitter)
        items += _safe_collect("Tier 8 — Instagram", _scrape_instagram)

    return items


def _scrape_twitter():
    from src.sources import twitter_scraper
    return twitter_scraper.scrape_all(settings.twitter_handle)


def _scrape_instagram():
    from src.sources import instagram_scraper
    return instagram_scraper.scrape_all()


def deduplicate(items: list[NewsItem]) -> list[NewsItem]:
    fresh = []
    for item in items:
        unique_id = item.url or item.title
        if not is_duplicate(item.source, unique_id, ttl_days=30):
            mark_seen(item.source, unique_id, item.title, item.url, item.published_at)
            fresh.append(item)
    return fresh


def run_pipeline(social: bool = False, log_file: str = "") -> list[NewsItem]:
    log_lines = []
    def log(msg):
        log_lines.append(msg)
        print(msg, flush=True)

    log(f"\n=== News Agent Pipeline — {datetime.now().isoformat()[:16]} ===\n")

    items = collect_all(social=social)
    log(f"\nTotal collected: {len(items)}")

    fresh = deduplicate(items)
    log(f"New items: {len(fresh)}")

    if not fresh:
        log("No new items.")
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            Path(log_file).write_text("\n".join(log_lines), encoding="utf-8")
        return []

    summarized = summarize_items(fresh)
    log(f"Summarized: {len(summarized)} items")

    if summarized:
        try:
            from src.notifier import send_notification
            send_notification(summarized)
        except Exception:
            pass

    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        Path(log_file).write_text("\n".join(log_lines), encoding="utf-8")

    return summarized


CATEGORY_SYMBOLS = {
    "government": "[GOV]", "police": "[POL]", "education": "[EDU]",
    "business": "[BIZ]", "event": "[EVT]", "health": "[HLT]",
    "railway": "[RAL]", "infrastructure": "[INF]", "news": "[NEW]",
    "social": "[SOC]", "video": "[VID]",
}


def _safe(text: str, maxlen: int = 80) -> str:
    s = text[:maxlen].encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    return s.replace("\ufffd", "?")


def print_digest(items: list[NewsItem]):
    if not items:
        print("\nNo news today.")
        return

    categories = {}
    for item in items:
        cat = item.category.split(":")[-1].strip()
        categories.setdefault(cat, []).append(item)

    print(f"\n{'='*60}")
    print(f"  BILASPUR NEWS DIGEST — {datetime.now().isoformat()[:10]}")
    print(f"{'='*60}\n")

    for cat, cat_items in sorted(categories.items()):
        sym = CATEGORY_SYMBOLS.get(cat, "[*]")
        print(f"  {sym} {cat.upper()} ({len(cat_items)})")
        print(f"  {'-'*50}")
        for item in cat_items[:5]:
            print(f"  * {_safe(item.title, 80)}")
            print(f"    [{item.source}] {_safe(item.url, 70)}")
            if item.summary:
                print(f"    {_safe(item.summary, 100)}")
            print()

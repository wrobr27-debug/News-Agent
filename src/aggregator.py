from datetime import datetime
from pathlib import Path
import math
import re
from src.database import is_duplicate, mark_seen, get_todays_items, update_item_details
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


STOP_WORDS = {
    'in', 'the', 'a', 'of', 'to', 'and', 'is', 'for', 'at', 'by', 'from', 'on', 'with', 'as', 'an', 'it', 'its', 'that', 'this', 'are', 'was', 'were', 'be', 'been', 'has', 'have', 'had', 'will', 'would', 'should', 'can', 'could', 'about', 'after', 'before', 'new', 'news'
}


def tokenize(text: str) -> list[str]:
    words = re.findall(r'[a-zA-Z0-9\u0900-\u097F]+', text.lower())
    return [w for w in words if w not in STOP_WORDS]


def cosine_similarity(vec1: dict[str, float], vec2: dict[str, float]) -> float:
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum(vec1[w] * vec2[w] for w in intersection)
    
    sum1 = sum(val ** 2 for val in vec1.values())
    sum2 = sum(val ** 2 for val in vec2.values())
    
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    if not denominator:
        return 0.0
    return numerator / denominator


def deduplicate_semantic(items: list[NewsItem], threshold: float = 0.4) -> list[NewsItem]:
    if len(items) <= 1:
        return items
        
    tokenized_docs = [tokenize(f"{item.title} {item.summary}") for item in items]
    
    # Calculate TF vectors
    tf_vectors = []
    for doc in tokenized_docs:
        tf = {}
        for word in doc:
            tf[word] = tf.get(word, 0) + 1
        tf_vectors.append(tf)
        
    keep_indices = []
    skipped = set()
    num_docs = len(items)
    
    for i in range(num_docs):
        if i in skipped:
            continue
        keep_indices.append(i)
        
        for j in range(i + 1, num_docs):
            if j in skipped:
                continue
            sim = cosine_similarity(tf_vectors[i], tf_vectors[j])
            if sim >= threshold:
                skipped.add(j)
                print(f"Skipping semantic duplicate:\n  Keep: [{items[i].source}] {_safe(items[i].title)}\n  Skip: [{items[j].source}] {_safe(items[j].title)} (Similarity: {sim:.2f})")
                
    return [items[i] for i in keep_indices]


def deduplicate(items: list[NewsItem]) -> list[NewsItem]:
    candidates = []
    seen_keys = set()
    for item in items:
        unique_id = item.url or item.title
        if not is_duplicate(item.source, unique_id, ttl_days=30):
            dup_key = (item.source, unique_id)
            if dup_key not in seen_keys:
                seen_keys.add(dup_key)
                candidates.append(item)
                
    unique_items = deduplicate_semantic(candidates, threshold=0.4)
    
    for item in unique_items:
        unique_id = item.url or item.title
        mark_seen(item.source, unique_id, item.title, item.url, item.published_at, item.image_url, item.image_url_2)
        
    return unique_items


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

    # Update database with summarized titles, categories, and summaries
    for item in summarized:
        unique_id = item.url or item.title
        try:
            update_item_details(item.source, unique_id, item.title, item.category, item.summary)
        except Exception as e:
            log(f"Failed to update item details in DB: {e}")

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
    import sys
    s = text[:maxlen]
    try:
        s.encode(sys.stdout.encoding or 'utf-8')
        return s
    except Exception:
        return s.encode('ascii', 'ignore').decode('ascii')


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

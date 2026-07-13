import os
from pathlib import Path
from datetime import datetime
import sys

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_todays_items, init_db
from src.dashboard import HEAD, _card, _section

def build():
    init_db()
    items = get_todays_items()

    from src.summarizer import _guess_category
    from src.sources.government import NewsItem

    cats = {}
    for item in items:
        source_lower = item[0].lower()
        cat = item[5]
        if source_lower.startswith("instagram"):
            cat = "instagram"
        elif source_lower in ["bilaspur grand news", "ibc24", "news18 chhattisgarh", "zee mpcg"] or cat == "video":
            cat = "youtube"
        elif not cat or cat == "general":
            temp_item = NewsItem(source=item[0], title=item[1], url=item[2], summary=item[6] or "")
            cat = _guess_category(temp_item)
            
        clean_cat = cat.replace("breaking:", "").strip()
        cats.setdefault(clean_cat, []).append(item)

    cards = "".join(_card(k, len(v)) for k, v in sorted(cats.items()))

    if cats:
        sections = "".join(_section(k, v) for k, v in sorted(cats.items()))
    else:
        sections = '<div class="empty"><h2>No news collected yet</h2><p>Check back later.</p></div>'

    now_utc = datetime.utcnow().isoformat()
    html = HEAD.replace("__DATE_UTC__", now_utc)
    html = html.replace("__TOTAL__", str(len(items)))
    html = html.replace("__CARDS__", cards)
    html = html.replace("__SECTIONS__", sections)
    
    # Remove the "Run Pipeline Now" button since it's hosted statically
    html = html.replace('<div><a href="/refresh" class="btn">Run Pipeline Now</a></div>', '')

    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)
    
    with open(dist_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Static dashboard built successfully in dist/index.html")

if __name__ == "__main__":
    build()

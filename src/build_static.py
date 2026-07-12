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

    cats = {}
    for item in items:
        # Group by category (which is at index 0 in get_todays_items output:
        # source_name is index 0, title is 1, url is 2, published_at is 3, first_seen_at is 4)
        # Wait, get_todays_items returns: (source_name, title, url, published_at, first_seen_at)
        # But wait! In src/dashboard.py:
        # cats.setdefault(item[0], []).append(item)
        # Wait! item[0] is the source_name!
        # Ah, yes. The current dashboard groups by source name, not category. Let's make sure it matches
        # dashboard.py exactly. Let's look at dashboard.py lines 85-88:
        # cats = {}
        # for item in items:
        #     cat = item[0] or "other"
        #     cats.setdefault(cat, []).append(item)
        # Yes, item[0] (source_name) is used as the key.
        cat = item[0] or "other"
        cats.setdefault(cat, []).append(item)

    cards = "".join(_card(k, len(v)) for k, v in sorted(cats.items()))

    if cats:
        sections = "".join(_section(k, v) for k, v in sorted(cats.items()))
    else:
        sections = '<div class="empty"><h2>No news collected yet</h2><p>Check back later.</p></div>'

    html = HEAD.replace("__DATE__", datetime.now().isoformat()[:10])
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

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
        cat = item[5] or "news"
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

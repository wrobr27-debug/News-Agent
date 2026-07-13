from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from datetime import datetime
from pathlib import Path
import sys
import logging
from apscheduler.schedulers.background import BackgroundScheduler

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_todays_items, init_db
from src.aggregator import run_pipeline

# Initialize database
init_db()

# Setup background scheduler
logging.getLogger('apscheduler').setLevel(logging.WARNING)
scheduler = BackgroundScheduler()

def scheduled_pipeline():
    print(f"[{datetime.now().isoformat()}] Running scheduled pipeline...")
    try:
        run_pipeline(social=False)
        print(f"[{datetime.now().isoformat()}] Scheduled pipeline finished successfully.")
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Scheduled pipeline failed: {e}", file=sys.stderr)

def scheduled_social_pipeline():
    print(f"[{datetime.now().isoformat()}] Running scheduled social pipeline...")
    try:
        run_pipeline(social=True)
        print(f"[{datetime.now().isoformat()}] Scheduled social pipeline finished successfully.")
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Scheduled social pipeline failed: {e}", file=sys.stderr)

# Schedule jobs
scheduler.add_job(scheduled_pipeline, 'interval', hours=2, id='hourly_news_job')
scheduler.add_job(scheduled_social_pipeline, 'cron', hour=8, minute=0, id='daily_social_job')

app = FastAPI(title="Bilaspur News Agent")

@app.on_event("startup")
def start_scheduler():
    scheduler.start()
    # Trigger one run immediately on startup in background
    scheduler.add_job(scheduled_pipeline, 'date', run_date=datetime.now(), id='startup_news_job')

@app.on_event("shutdown")
def stop_scheduler():
    scheduler.shutdown()

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bilaspur News Agent</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter', -apple-system, BlinkMacSystemFont, sans-serif;background:#f8f9fa;color:#212529;padding:24px;line-height:1.5}
.hdr{background:linear-gradient(135deg, #1a237e 0%, #303f9f 100%);color:#fff;padding:24px 32px;border-radius:16px;margin-bottom:30px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 4px 20px rgba(26, 35, 126, 0.15)}
.hdr h1{font-size:26px;font-weight:700;letter-spacing:-0.5px}
.hdr .meta{font-size:14px;opacity:.9;margin-top:4px}
.btn{background:rgba(255,255,255,0.15);color:#fff;border:none;padding:10px 20px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;text-decoration:none;display:inline-block;transition:all 0.2s;backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,0.25)}
.btn:hover{background:rgba(255,255,255,0.25);transform:translateY(-1px)}
.stats{display:flex;gap:16px;margin-bottom:30px;flex-wrap:wrap}
.sc-link{text-decoration:none;display:block;flex:1;min-width:140px;transition:all 0.2s}
.sc-link:hover{transform:translateY(-4px)}
.sc{background:#fff;padding:16px 20px;border-radius:12px;box-shadow:0 4px 6px rgba(0,0,0,.02), 0 1px 3px rgba(0,0,0,.05);text-align:center;border:1px solid #f1f3f5;height:100%}
.sc .n{font-size:32px;font-weight:800;color:#1a237e}
.sc .l{font-size:12px;color:#495057;margin-top:4px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px}
.sec{background:#fff;border-radius:12px;box-shadow:0 4px 6px rgba(0,0,0,.02), 0 1px 3px rgba(0,0,0,.05);margin-bottom:24px;overflow:hidden;border:1px solid #e9ecef;scroll-margin-top:24px}
.sh{padding:16px 24px;font-weight:700;font-size:18px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #f1f3f5;background:#f8f9fa;color:#1a237e}
.sh .c{background:#e8eaf6;color:#1a237e;padding:2px 12px;border-radius:20px;font-size:13px;font-weight:700}
.sb{padding:8px 0}
.sb.grid{display:grid;grid-template-columns:repeat(auto-fill, minmax(320px, 1fr));gap:24px;padding:24px;background:#fafafa}
.ni{padding:16px 24px;border-bottom:1px solid #f1f3f5;transition:background 0.2s}
.ni:hover{background:#f8f9fa}
.ni-content{display:flex;gap:16px;align-items:flex-start}
.ni-thumb{flex-shrink:0;width:95px;height:95px;border-radius:8px;overflow:hidden;border:1px solid #e9ecef}
.ni-thumb img{width:100%;height:100%;object-fit:cover;transition:transform 0.2s}
.ni-thumb img:hover{transform:scale(1.05)}
.ni-text{flex:1}
.ni-text .t{font-size:15px;font-weight:600;margin-bottom:6px;display:flex;align-items:center;flex-wrap:wrap;gap:8px}
.ni-text .t a{color:#1a237e;text-decoration:none;line-height:1.4}
.ni-text .t a:hover{color:#303f9f;text-decoration:underline}
.ni-text .s{font-size:12px;color:#6c757d;font-weight:500}
.ni-text .tm{color:#6c757d;font-weight:400;margin-left:4px}
.ni-text .summary{font-size:13.5px;color:#495057;margin-top:8px;line-height:1.5;background:#fdfdfd;padding:10px 14px;border-radius:6px;border-left:3px solid #3f51b5;border-right:1px solid #eee;border-top:1px solid #eee;border-bottom:1px solid #eee}
.badge{display:inline-block;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px}
.badge.breaking{background:#ff1744;color:#fff}
.empty{text-align:center;padding:60px 20px;color:#888}
.empty h2{margin-bottom:12px}

/* Social Card styling for Instagram/YouTube Grid */
.ni.soc-card{padding:0;border-radius:12px;border:1px solid #e9ecef;background:#fff;overflow:hidden;box-shadow:0 4px 10px rgba(0,0,0,0.03);display:flex;flex-direction:column;transition:all 0.2s}
.ni.soc-card:hover{transform:translateY(-3px);box-shadow:0 8px 16px rgba(0,0,0,0.06)}
.soc-banner{width:100%;height:220px;overflow:hidden;border-bottom:1px solid #f1f3f5;background:#eaeaea}
.soc-banner img{width:100%;height:100%;object-fit:cover;transition:transform 0.3s}
.soc-banner img:hover{transform:scale(1.03)}
.soc-body{padding:18px;flex:1;display:flex;flex-direction:column}
.soc-header{display:flex;align-items:center;gap:12px;margin-bottom:12px}
.soc-avatar{width:36px;height:36px;border-radius:50%;object-fit:cover;border:1.5px solid #1a237e;background:#fff;padding:1px}
.soc-meta{display:flex;flex-direction:column}
.soc-author{font-weight:700;font-size:13.5px;color:#212529}
.soc-time{font-size:11px;color:#868e96;margin-top:1px}
.soc-title{font-size:15px;font-weight:700;margin-bottom:10px;line-height:1.4}
.soc-title a{color:#1a237e;text-decoration:none}
.soc-title a:hover{color:#303f9f;text-decoration:underline}
.soc-desc{font-size:13px;color:#495057;line-height:1.5;background:#f8f9fa;padding:10px 12px;border-radius:8px;border-left:3px solid #ff4081;flex:1;white-space:pre-wrap}
</style>
<script>
document.addEventListener("DOMContentLoaded", () => {
  // Convert last updated time to local browser timezone
  const lastUpdatedEl = document.getElementById("last-updated-time");
  if (lastUpdatedEl) {
    const utcStr = lastUpdatedEl.getAttribute("data-utc");
    if (utcStr) {
      const date = new Date(utcStr.replace(" ", "T") + "Z");
      lastUpdatedEl.textContent = date.toLocaleString();
    }
  }
  
  // Convert news scraped time to local time (extracting just the hour:minute)
  document.querySelectorAll(".local-time").forEach(el => {
    const utcStr = el.getAttribute("data-utc");
    if (utcStr) {
      const date = new Date(utcStr.replace(" ", "T") + "Z");
      el.textContent = date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
  });
});
</script>
</head>
<body>
<div class="hdr">
<div><h1>Bilaspur News Agent</h1><div class="meta">Last updated: <span id="last-updated-time" data-utc="__DATE_UTC__">__DATE_UTC__</span> &middot; __TOTAL__ items today</div></div>
<div><a href="/refresh" class="btn">Run Pipeline Now</a></div>
</div>
<div class="stats">
__CARDS__
</div>
__SECTIONS__
</body>
</html>"""


def _e(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _card(name: str, count: int) -> str:
    clean_id = name.lower().strip()
    display_name = f"{name.upper()} NEWS" if name.lower() == "instagram" else (f"{name.upper()} VIDEOS" if name.lower() == "youtube" else name.upper())
    return f'<a href="#{clean_id}" class="sc-link"><div class="sc"><div class="n">{count}</div><div class="l">{_e(display_name)}</div></div></a>'


def _section(name: str, items: list) -> str:
    is_grid = name.lower() in ["instagram", "youtube"]
    sb_class = "sb grid" if is_grid else "sb"
    
    rows = ""
    for item in items[:20]:
        # item[0] = source_name, item[1] = title, item[2] = url, item[3] = published_at, item[4] = first_seen_at, item[5] = category, item[6] = summary, item[7] = image_url, item[8] = image_url_2
        pub_time = item[3] or ""
        scraped_time = item[4] or ""
        
        time_display = ""
        if pub_time:
            time_display += f'Published: {pub_time}'
        if scraped_time:
            if time_display:
                time_display += " &middot; "
            time_display += f'Scraped: <span class="local-time" data-utc="{scraped_time}">{scraped_time}</span>'
            
        if is_grid:
            img_url = item[7] or "https://cdn-icons-png.flaticon.com/512/120/120084.png"
            img_url_2 = item[8] or "https://cdn-icons-png.flaticon.com/512/174/174855.png"
            summary_text = item[6] or ""
            
            rows += f"""<div class="ni soc-card">
<div class="soc-banner">
<a href="{_e(item[2])}" target="_blank" rel="noopener"><img src="{_e(img_url)}" alt="Featured Image" /></a>
</div>
<div class="soc-body">
<div class="soc-header">
<img class="soc-avatar" src="{_e(img_url_2)}" alt="Avatar" />
<div class="soc-meta">
<span class="soc-author">{_e(item[0])}</span>
<span class="soc-time">{time_display}</span>
</div>
</div>
<div class="soc-title"><a href="{_e(item[2])}" target="_blank" rel="noopener">{_e(item[1])}</a></div>
<div class="soc-desc">{_e(summary_text)}</div>
</div>
</div>"""
        else:
            is_breaking = "breaking:" in (item[5] or "")
            breaking_badge = '<span class="badge breaking">BREAKING</span>' if is_breaking else ''
            summary_html = f'<div class="summary">{_e(item[6])}</div>' if item[6] else ''
            
            thumb_html = ""
            if len(item) > 7 and item[7]:
                thumb_html = f"""<div class="ni-thumb">
<a href="{_e(item[2])}" target="_blank" rel="noopener"><img src="{_e(item[7])}" alt="Cover Image" /></a>
</div>"""

            rows += f"""<div class="ni">
<div class="ni-content">
{thumb_html}
<div class="ni-text">
<div class="t">{breaking_badge}<a href="{_e(item[2])}" target="_blank" rel="noopener">{_e(item[1])}</a></div>
<div class="s">{_e(item[0])} &middot; <span class="tm">{time_display}</span></div>
{summary_html}
</div>
</div>
</div>"""
    
    clean_id = name.lower().strip()
    display_name = f"{name.upper()} NEWS" if name.lower() == "instagram" else (f"{name.upper()} VIDEOS" if name.lower() == "youtube" else name.upper())
    return f"""<div class="sec" id="{clean_id}">
<div class="sh"><span>{_e(display_name)}</span><span class="c">{len(items)}</span></div>
<div class="{sb_class}">{rows}</div>
</div>"""


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    items = get_todays_items()

    from src.summarizer import _guess_category
    from src.sources.government import NewsItem

    cats = {}
    for item in items:
        # Override grouping for social sources to map to dedicated categories
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
        sections = '<div class="empty"><h2>No news collected yet</h2><p><a href="/refresh" class="btn">Run Pipeline</a></p></div>'

    now_utc = datetime.utcnow().isoformat()
    html = HEAD.replace("__DATE_UTC__", now_utc)
    html = html.replace("__TOTAL__", str(len(items)))
    html = html.replace("__CARDS__", cards)
    html = html.replace("__SECTIONS__", sections)

    return HTMLResponse(html)


@app.get("/refresh", response_class=HTMLResponse)
async def refresh():
    items = run_pipeline()
    return HTMLResponse(
        f"<html><body><h2>Pipeline complete</h2><p>{len(items)} new items.</p>"
        '<script>setTimeout(()=>window.location="/",1000)</script></body></html>'
    )

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
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f5;color:#333;padding:20px}
.hdr{background:#1a237e;color:#fff;padding:20px 30px;border-radius:12px;margin-bottom:24px;display:flex;justify-content:space-between;align-items:center}
.hdr h1{font-size:24px}
.hdr .meta{font-size:14px;opacity:.8}
.btn{background:#3949ab;color:#fff;border:none;padding:10px 20px;border-radius:8px;font-size:14px;cursor:pointer;text-decoration:none;display:inline-block;margin:2px}
.btn:hover{background:#303f9f}
.stats{display:flex;gap:16px;margin-bottom:24px;flex-wrap:wrap}
.sc{background:#fff;padding:16px 24px;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,.1);flex:1;min-width:120px;text-align:center}
.sc .n{font-size:28px;font-weight:700;color:#1a237e}
.sc .l{font-size:12px;color:#666;margin-top:4px}
.sec{background:#fff;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,.1);margin-bottom:16px;overflow:hidden}
.sh{padding:14px 20px;font-weight:600;font-size:16px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #eee}
.sh .c{background:#e8eaf6;color:#1a237e;padding:2px 10px;border-radius:12px;font-size:13px}
.sb{padding:8px 0}
.ni{padding:10px 20px;border-bottom:1px solid #f0f0f0}
.ni:hover{background:#fafafa}
.ni .t{font-size:14px;font-weight:500;margin-bottom:4px}
.ni .t a{color:#1a237e;text-decoration:none}
.ni .t a:hover{text-decoration:underline}
.ni .s{font-size:12px;color:#888}
.ni .tm{font-size:11px;color:#aaa;margin-left:8px}
.empty{text-align:center;padding:60px 20px;color:#888}
.empty h2{margin-bottom:12px}
</style>
</head>
<body>
<div class="hdr">
<div><h1>Bilaspur News Agent</h1><div class="meta">__DATE__ &middot; __TOTAL__ items today</div></div>
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
    return f'<div class="sc"><div class="n">{count}</div><div class="l">{_e(name)}</div></div>'


def _section(name: str, items: list) -> str:
    rows = ""
    for item in items[:20]:
        rows += f"""<div class="ni">
<div class="t"><a href="{_e(item[2])}" target="_blank" rel="noopener">{_e(item[1])}</a></div>
<div class="s">{_e(item[0])}<span class="tm">{item[3] or ""}</span></div>
</div>"""
    return f"""<div class="sec">
<div class="sh"><span>{_e(name.upper())}</span><span class="c">{len(items)}</span></div>
<div class="sb">{rows}</div>
</div>"""


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    items = get_todays_items()

    cats = {}
    for item in items:
        cat = item[0] or "other"
        cats.setdefault(cat, []).append(item)

    cards = "".join(_card(k, len(v)) for k, v in sorted(cats.items()))

    if cats:
        sections = "".join(_section(k, v) for k, v in sorted(cats.items()))
    else:
        sections = '<div class="empty"><h2>No news collected yet</h2><p><a href="/refresh" class="btn">Run Pipeline</a></p></div>'

    html = HEAD.replace("__DATE__", datetime.now().isoformat()[:10])
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

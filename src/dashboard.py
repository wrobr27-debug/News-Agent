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
<title>Bilaspur News Hub</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {
    --bg-deep: #080c14;
    --card-bg: rgba(18, 25, 41, 0.7);
    --border-glow: rgba(139, 92, 246, 0.35);
    --primary-purple: #8b5cf6;
    --primary-blue: #3b82f6;
    --accent-red: #ff3366;
    --accent-green: #10b981;
    --text-light: #f3f4f6;
    --text-muted: #9ca3af;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

body {
    background-color: var(--bg-deep);
    color: var(--text-light);
    min-height: 100vh;
    padding: 2.5rem 1.5rem;
    line-height: 1.6;
    background-image: radial-gradient(circle at 5% 10%, rgba(139, 92, 246, 0.15) 0%, transparent 40%),
                      radial-gradient(circle at 95% 85%, rgba(59, 130, 246, 0.15) 0%, transparent 40%);
    background-attachment: fixed;
}

.container {
    max-width: 1250px;
    margin: 0 auto;
}

/* Header */
.hdr {
    background: var(--card-bg);
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(16px);
    padding: 1.75rem 2.5rem;
    border-radius: 1.25rem;
    margin-bottom: 2.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}

.hdr h1 {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #c084fc 0%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -1px;
}

.hdr .meta {
    font-size: 0.9rem;
    color: var(--text-muted);
    margin-top: 0.25rem;
}

.btn {
    background: rgba(255, 255, 255, 0.07);
    color: var(--text-light);
    border: 1px solid rgba(255, 255, 255, 0.12);
    padding: 0.7rem 1.3rem;
    border-radius: 0.6rem;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
    transition: all 0.2s;
    backdrop-filter: blur(8px);
}

.btn:hover {
    background: rgba(255, 255, 255, 0.15);
    border-color: rgba(255, 255, 255, 0.2);
    transform: translateY(-1px);
}

/* Top Toolbar: Search & Categories */
.toolbar {
    margin-bottom: 2.5rem;
}

.search-wrapper {
    margin-bottom: 1.5rem;
    position: relative;
}

.search-input {
    width: 100%;
    background: var(--card-bg);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: var(--text-light);
    padding: 1.1rem 1.5rem 1.1rem 3rem;
    border-radius: 1rem;
    font-size: 1rem;
    backdrop-filter: blur(12px);
    transition: all 0.3s ease;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.search-input:focus {
    outline: none;
    border-color: var(--primary-purple);
    box-shadow: 0 0 15px rgba(139, 92, 246, 0.25);
}

.search-icon {
    position: absolute;
    left: 1.1rem;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
    font-size: 1.1rem;
    pointer-events: none;
}

/* Category Filter Tabs */
.tabs {
    display: flex;
    gap: 0.6rem;
    overflow-x: auto;
    padding-bottom: 0.5rem;
    margin-bottom: 2rem;
}

.tabs::-webkit-scrollbar {
    height: 4px;
}

.tabs::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
}

.tab-btn {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.06);
    color: var(--text-muted);
    padding: 0.6rem 1.3rem;
    border-radius: 50px;
    cursor: pointer;
    font-weight: 600;
    font-size: 0.85rem;
    transition: all 0.25s ease;
    white-space: nowrap;
}

.tab-btn.active, .tab-btn:hover {
    background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-blue) 100%);
    color: var(--text-light);
    border-color: transparent;
    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
}

/* Stats Cards */
.stats {
    display: flex;
    gap: 1.25rem;
    margin-bottom: 2.5rem;
    flex-wrap: wrap;
}

.sc-link {
    text-decoration: none;
    display: block;
    flex: 1;
    min-width: 150px;
    transition: transform 0.2s ease;
}

.sc-link:hover {
    transform: translateY(-3px);
}

.sc {
    background: var(--card-bg);
    border: 1px solid rgba(255, 255, 255, 0.06);
    padding: 1.25rem;
    border-radius: 1rem;
    text-align: center;
    backdrop-filter: blur(12px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
}

.sc .n {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.sc .l {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 0.25rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Grid & Section layouts */
.sec {
    margin-bottom: 3rem;
    scroll-margin-top: 2rem;
}

.sh {
    font-size: 1.4rem;
    font-weight: 800;
    margin-bottom: 1.25rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.sh .c {
    background: rgba(139, 92, 246, 0.15);
    color: #c084fc;
    padding: 0.2rem 0.75rem;
    border-radius: 50px;
    font-size: 0.85rem;
    font-weight: 700;
    border: 1px solid rgba(139, 92, 246, 0.25);
}

.sb {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
}

.sb.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.75rem;
}

/* Standard News Item */
.ni {
    background: var(--card-bg);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 1.25rem;
    padding: 1.5rem;
    backdrop-filter: blur(12px);
    transition: all 0.25s ease;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}

.ni:hover {
    border-color: rgba(139, 92, 246, 0.3);
    box-shadow: 0 8px 25px rgba(139, 92, 246, 0.1);
    transform: scale(1.005);
}

.ni-content {
    display: flex;
    gap: 1.5rem;
    align-items: flex-start;
}

.ni-thumb {
    flex-shrink: 0;
    width: 100px;
    height: 100px;
    border-radius: 0.75rem;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.08);
    cursor: pointer;
}

.ni-thumb img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s ease;
}

.ni-thumb img:hover {
    transform: scale(1.05);
}

.ni-text {
    flex: 1;
}

.ni-text .t {
    font-size: 1.15rem;
    font-weight: 700;
    margin-bottom: 0.4rem;
    line-height: 1.35;
}

.ni-text .t a {
    color: #ffffff;
    text-decoration: none;
    cursor: pointer;
}

.ni-text .t a:hover {
    color: #c084fc;
}

.ni-text .s {
    font-size: 0.85rem;
    color: var(--text-muted);
    font-weight: 600;
}

.ni-text .tm {
    font-weight: 400;
    opacity: 0.85;
}

.ni-text .summary {
    font-size: 0.9rem;
    color: #d1d5db;
    margin-top: 0.75rem;
    line-height: 1.5;
    background: rgba(0, 0, 0, 0.15);
    padding: 0.75rem 1rem;
    border-radius: 0.6rem;
    border-left: 3px solid var(--primary-purple);
    cursor: pointer;
}

.ni-text .summary:hover {
    background: rgba(0, 0, 0, 0.25);
}

.badge {
    display: inline-block;
    padding: 0.2rem 0.5rem;
    border-radius: 0.35rem;
    font-size: 0.65rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-right: 0.5rem;
    vertical-align: middle;
}

.badge.breaking {
    background: var(--accent-red);
    color: #fff;
    box-shadow: 0 0 10px rgba(255, 23, 68, 0.3);
}

/* Social Media Card */
.ni.soc-card {
    padding: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.ni.soc-card:hover {
    transform: translateY(-4px);
    border-color: rgba(139, 92, 246, 0.3);
}

.soc-banner {
    width: 100%;
    height: 200px;
    overflow: hidden;
    position: relative;
    cursor: pointer;
    background: #111827;
}

.soc-banner img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s ease;
}

.soc-banner img:hover {
    transform: scale(1.02);
}

.soc-banner::after {
    content: "▶";
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    background: rgba(0, 0, 0, 0.6);
    color: #fff;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    border: 2px solid #fff;
    opacity: 0.85;
    transition: all 0.2s ease;
}

.soc-banner:hover::after {
    transform: translate(-50%, -50%) scale(1.1);
    background: var(--primary-purple);
    opacity: 1;
}

.soc-body {
    padding: 1.25rem;
    flex: 1;
    display: flex;
    flex-direction: column;
}

.soc-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
}

.soc-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    object-fit: cover;
    border: 1.5px solid var(--primary-purple);
}

.soc-meta {
    display: flex;
    flex-direction: column;
}

.soc-author {
    font-weight: 700;
    font-size: 0.85rem;
    color: #ffffff;
}

.soc-time {
    font-size: 0.7rem;
    color: var(--text-muted);
}

.soc-title {
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 0.75rem;
    line-height: 1.35;
}

.soc-title a {
    color: #ffffff;
    text-decoration: none;
}

.soc-title a:hover {
    color: #cbd5e1;
}

.soc-desc {
    font-size: 0.85rem;
    color: #d1d5db;
    line-height: 1.45;
    background: rgba(0, 0, 0, 0.15);
    padding: 0.75rem;
    border-radius: 0.6rem;
    border-left: 3px solid #ff4081;
    flex: 1;
    white-space: pre-wrap;
    cursor: pointer;
}

.soc-desc:hover {
    background: rgba(0, 0, 0, 0.25);
}

/* Modal details popup */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.3s ease;
}

.modal-overlay.active {
    opacity: 1;
    pointer-events: auto;
}

.modal-content {
    background: #0f172a;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 1.5rem;
    max-width: 650px;
    width: 90%;
    padding: 2rem;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
    transform: translateY(20px);
    transition: transform 0.3s ease;
    position: relative;
}

.modal-overlay.active .modal-content {
    transform: translateY(0);
}

.modal-close {
    position: absolute;
    top: 1rem;
    right: 1.25rem;
    font-size: 1.5rem;
    background: none;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    transition: color 0.2s;
}

.modal-close:hover {
    color: #fff;
}

.modal-source {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--primary-purple);
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.modal-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: #fff;
    margin-bottom: 1rem;
    line-height: 1.35;
}

.modal-time {
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-bottom: 1.25rem;
}

.modal-body {
    font-size: 0.95rem;
    color: #cbd5e1;
    line-height: 1.6;
    margin-bottom: 1.5rem;
    white-space: pre-wrap;
    background: rgba(0,0,0,0.2);
    padding: 1.25rem;
    border-radius: 0.75rem;
    border: 1px solid rgba(255,255,255,0.03);
}

.modal-footer {
    display: flex;
    justify-content: flex-end;
}

.empty {
    text-align: center;
    padding: 5rem 2rem;
    background: var(--card-bg);
    border-radius: 1.25rem;
    border: 1px dashed rgba(255, 255, 255, 0.1);
}

.empty h2 {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}

.empty p {
    color: var(--text-muted);
}
</style>
<script>
document.addEventListener("DOMContentLoaded", () => {
  // Convert timestamps to local browser timezone
  const lastUpdatedEl = document.getElementById("last-updated-time");
  if (lastUpdatedEl) {
    const utcStr = lastUpdatedEl.getAttribute("data-utc");
    if (utcStr) {
      const date = new Date(utcStr.replace(" ", "T") + "Z");
      lastUpdatedEl.textContent = date.toLocaleString();
    }
  }
  
  document.querySelectorAll(".local-time").forEach(el => {
    const utcStr = el.getAttribute("data-utc");
    if (utcStr) {
      const date = new Date(utcStr.replace(" ", "T") + "Z");
      el.textContent = date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
  });

  // Client-side search and category filtering
  const searchInput = document.getElementById("search-box");
  const tabButtons = document.querySelectorAll(".tab-btn");
  let activeCategory = "all";

  function filterNews() {
    const query = searchInput.value.toLowerCase().strip ? searchInput.value.toLowerCase().trim() : "";
    const items = document.querySelectorAll(".news-item-wrapper");

    items.forEach(item => {
      const category = item.getAttribute("data-category");
      const title = item.getAttribute("data-title").toLowerCase();
      const summary = item.getAttribute("data-summary").toLowerCase();
      const source = item.getAttribute("data-source").toLowerCase();

      const matchesCategory = (activeCategory === "all" || category === activeCategory);
      const matchesSearch = (!query || title.includes(query) || summary.includes(query) || source.includes(query));

      if (matchesCategory && matchesSearch) {
        item.style.display = "";
      } else {
        item.style.display = "none";
      }
    });

    // Hide empty section headers dynamically
    const sections = document.querySelectorAll(".sec");
    sections.forEach(sec => {
      const visibleItems = sec.querySelectorAll(".news-item-wrapper[style='']");
      if (visibleItems.length === 0 && query !== "") {
        sec.style.display = "none";
      } else {
        sec.style.display = "";
      }
    });
  }

  if (searchInput) {
    searchInput.addEventListener("input", filterNews);
  }

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      tabButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeCategory = btn.getAttribute("data-tab");
      
      // Scroll to category section if filtering specifically
      if (activeCategory !== "all") {
        const targetSec = document.getElementById(activeCategory);
        if (targetSec) {
          targetSec.scrollIntoView({ behavior: "smooth" });
        }
      }
      filterNews();
    });
  });
});

// Modal Detail Popup Handlers
function openReaderModal(title, source, time, summary, url) {
  document.getElementById("modal-source").textContent = source;
  document.getElementById("modal-title").textContent = title;
  document.getElementById("modal-time").textContent = time;
  document.getElementById("modal-body").textContent = summary;
  
  const linkBtn = document.getElementById("modal-link-btn");
  if (url && url !== "#") {
    linkBtn.href = url;
    linkBtn.style.display = "inline-block";
  } else {
    linkBtn.style.display = "none";
  }
  
  document.getElementById("reader-modal").classList.add("active");
}

function closeReaderModal() {
  document.getElementById("reader-modal").classList.remove("active");
}
</script>
</head>
<body>
<div class="container">
    <div class="hdr">
        <div>
            <h1>Bilaspur News Hub</h1>
            <div class="meta">Last updated: <span id="last-updated-time" data-utc="__DATE_UTC__">__DATE_UTC__</span> &middot; __TOTAL__ items today</div>
        </div>
        <div><a href="/refresh" class="btn">Run Pipeline Now</a></div>
    </div>

    <!-- Search & Filters Toolbar -->
    <div class="toolbar">
        <div class="search-wrapper">
            <span class="search-icon">🔍</span>
            <input type="text" id="search-box" class="search-input" placeholder="Search news titles, summaries, or publishers...">
        </div>
        
        <div class="tabs">
            <button class="tab-btn active" data-tab="all">All News</button>
            <button class="tab-btn" data-tab="government">Government</button>
            <button class="tab-btn" data-tab="police">Police</button>
            <button class="tab-btn" data-tab="education">Education</button>
            <button class="tab-btn" data-tab="business">Business</button>
            <button class="tab-btn" data-tab="news">Publishers</button>
            <button class="tab-btn" data-tab="instagram">Instagram</button>
            <button class="tab-btn" data-tab="youtube">YouTube</button>
            <button class="tab-btn" data-tab="general">General</button>
        </div>
    </div>

    <div class="stats">
    __CARDS__
    </div>

    <div id="news-container">
    __SECTIONS__
    </div>
</div>

<!-- Details Reader Modal -->
<div id="reader-modal" class="modal-overlay" onclick="if(event.target === this) closeReaderModal()">
    <div class="modal-content">
        <button class="modal-close" onclick="closeReaderModal()">&times;</button>
        <div id="modal-source" class="modal-source">Government</div>
        <h2 id="modal-title" class="modal-title">Custom Title</h2>
        <div id="modal-time" class="modal-time">scraped...</div>
        <div id="modal-body" class="modal-body">summary details...</div>
        <div class="modal-footer">
            <a id="modal-link-btn" href="#" target="_blank" class="btn" style="background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-blue) 100%); border-color: transparent;">Read Full Story on Source</a>
        </div>
    </div>
</div>
</body>
</html>"""


def _e(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _js_e(text: str) -> str:
    """Escape text for safe usage in inline javascript function arguments."""
    return _e(text).replace("'", "\\'").replace('"', '\\"').replace("\n", " ").replace("\r", " ")


def _card(name: str, count: int) -> str:
    clean_id = name.lower().strip()
    display_name = f"{name.upper()} NEWS" if name.lower() == "instagram" else (f"{name.upper()} VIDEOS" if name.lower() == "youtube" else name.upper())
    return f'<a href="#{clean_id}" class="sc-link"><div class="sc"><div class="n">{count}</div><div class="l">{_e(display_name)}</div></div></a>'


def _section(name: str, items: list) -> str:
    is_grid = name.lower() in ["instagram", "youtube"]
    sb_class = "sb grid" if is_grid else "sb"
    clean_cat = name.lower().strip()
    
    rows = ""
    for item in items[:20]:
        pub_time = item[3] or ""
        scraped_time = item[4] or ""
        
        time_display = ""
        if pub_time:
            time_display += f'Published: {pub_time}'
        if scraped_time:
            if time_display:
                time_display += " | "
            time_display += f'Scraped: <span class="local-time" data-utc="{scraped_time}">{scraped_time}</span>'
            
        summary_text = item[6] or ""
        
        # JS arguments for details modal
        js_title = _js_e(item[1])
        js_source = _js_e(item[0])
        js_time = _js_e(time_display)
        js_summary = _js_e(summary_text)
        js_url = _js_e(item[2])
        
        click_handler = f"openReaderModal('{js_title}', '{js_source}', '{js_time}', '{js_summary}', '{js_url}')"
        
        if is_grid:
            if name.lower() == "youtube":
                default_banner = "https://cdn-icons-png.flaticon.com/512/1384/1384060.png"
                default_avatar = "https://cdn-icons-png.flaticon.com/512/1384/1384060.png"
            else:
                default_banner = "https://cdn-icons-png.flaticon.com/512/120/120084.png"
                default_avatar = "https://cdn-icons-png.flaticon.com/512/174/174855.png"
                
            img_url = item[7] or default_banner
            img_url_2 = item[8] or default_avatar
            
            rows += f"""<div class="ni soc-card news-item-wrapper" data-category="{clean_cat}" data-title="{_e(item[1])}" data-summary="{_e(summary_text)}" data-source="{_e(item[0])}">
<div class="soc-banner" onclick="{click_handler}">
<img src="{_e(img_url)}" alt="Featured Image" />
</div>
<div class="soc-body">
<div class="soc-header">
<img class="soc-avatar" src="{_e(img_url_2)}" alt="Avatar" />
<div class="soc-meta">
<span class="soc-author">{_e(item[0])}</span>
<span class="soc-time">{time_display}</span>
</div>
</div>
<div class="soc-title"><a onclick="{click_handler}">{_e(item[1])}</a></div>
<div class="soc-desc" onclick="{click_handler}">{_e(summary_text)}</div>
</div>
</div>"""
        else:
            is_breaking = "breaking:" in (item[5] or "")
            breaking_badge = '<span class="badge breaking">BREAKING</span>' if is_breaking else ''
            summary_html = f'<div class="summary" onclick="{click_handler}">{_e(item[6])}</div>' if item[6] else ''
            
            thumb_html = ""
            if len(item) > 7 and item[7]:
                thumb_html = f"""<div class="ni-thumb" onclick="{click_handler}">
<img src="{_e(item[7])}" alt="Cover Image" />
</div>"""

            rows += f"""<div class="ni news-item-wrapper" data-category="{clean_cat}" data-title="{_e(item[1])}" data-summary="{_e(summary_text)}" data-source="{_e(item[0])}">
<div class="ni-content">
{thumb_html}
<div class="ni-text">
<div class="t">{breaking_badge}<a onclick="{click_handler}">{_e(item[1])}</a></div>
<div class="s">{_e(item[0])} &middot; <span class="tm">{time_display}</span></div>
{summary_html}
</div>
</div>
</div>"""
    
    display_name = f"{name.upper()} NEWS" if name.lower() == "instagram" else (f"{name.upper()} VIDEOS" if name.lower() == "youtube" else name.upper())
    return f"""<div class="sec" id="{clean_cat}">
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

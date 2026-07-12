# Bilaspur News Agent — Core Architecture & Blueprint Guide

> **Version:** 0.1.0  
> **Date:** July 12, 2026  
> **Author:** Developer Bilaspur Editorial Engineering  
> **Project Root:** `D:\Developer Bilaspur\news agent\`

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Directory Structure & File Map](#3-directory-structure--file-map)
4. [Configuration System](#4-configuration-system)
5. [Source Modules (Tiers 1–11)](#5-source-modules-tiers-111)
   - 5.1 Tier 1–2: Government & Departments (`government.py`)
   - 5.2 Tier 3: Education (`education.py`)
   - 5.3 Tier 4: Business / OpenStreetMap (`openstreetmap.py`)
   - 5.4 Tier 5: Events (`events.py`)
   - 5.5 Tier 6: News Publishers (`news_publishers.py`)
   - 5.6 Tier 7: YouTube (`youtube_monitor.py`)
   - 5.7 Tier 8: Instagram (`instagram_scraper.py`)
   - 5.8 Tier 11: Twitter (`twitter_scraper.py`)
6. [Deduplication Engine (SQLite Database)](#6-deduplication-engine-sqlite)
7. [Pipeline Orchestration (Aggregator)](#7-pipeline-orchestration-aggregator)
8. [LLM Summarization & Categorization](#8-llm-summarization--categorization)
9. [Desktop Notifications](#9-desktop-notifications)
10. [Dashboard (FastAPI Web UI)](#10-dashboard-fastapi-web-ui)
11. [Entry Point & CLI](#11-entry-point--cli)
12. [Deployment & Scheduling](#12-deployment--scheduling)
13. [Data Flow Diagram](#13-data-flow-diagram)
14. [Design Decisions](#14-design-decisions)
15. [Limitations & Known Issues](#15-limitations--known-issues)
16. [Future Roadmap](#16-future-roadmap)
17. [Quick Reference](#17-quick-reference)

---

## 1. Project Overview

**Goal:** Build an AI-powered news intelligence agent that monitors **11 tiers** of local sources in and around Bilaspur, Chhattisgarh, aggregates findings, deduplicates, categorizes using a free LLM (OpenCode Zen), and presents a curated daily digest via both CLI and a FastAPI web dashboard.

**Key Metrics (verified in production):**
- **Source modules:** 9 active modules covering government, education, business, events, news publishers, YouTube, Instagram, Twitter, and OpenStreetMap
- **Items collected per run:** ~196–201 on first run; later runs collect only new items
- **Pipeline runtime:** ~2.5 minutes for 200 items (on Windows 11, 16GB RAM)
- **Cost:** ₹0 — all APIs used are free-tier or browser-scraped
- **LLM model:** `north-mini-code-free` via OpenCode Zen endpoint at `https://opencode.ai/zen/v1`

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    .env (API Keys & Config)                       │
│  OPENCODE_API_KEY | YOUTUBE_API_KEY | TWITTER_HANDLE | ...       │
└──────────┬───────────────────────────────────────────────────────┘
           │ loads
           ▼
┌──────────────────┐     ┌─────────────────────────────────────────┐
│   src/config.py  │────▶│            Pipeline Core                 │
│   (Settings)     │     │                                         │
└──────────────────┘     │  ┌──────────────────────────────────┐   │
                         │  │    src/aggregator.py             │   │
                         │  │    - collect_all()               │   │
                         │  │    - deduplicate()               │   │
                         │  │    - run_pipeline()              │   │
                         │  │    - print_digest()              │   │
                         │  └──────────────────────────────────┘   │
                         └──────────┬──────────────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────────┐
           ▼                        ▼                            ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│   Source Modules  │     │  src/database.py  │     │  src/summarizer.py   │
│   (9 modules)     │     │  (SQLite Dedup)   │     │  (OpenCode LLM)      │
└──────────────────┘     └──────────────────┘     └──────────────────────┘
           │                                                    │
           ▼                                                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Output Layer                                    │
│  ┌─────────────────────┐   ┌────────────────────────────────┐    │
│  │  CLI Print Digest   │   │  FastAPI Dashboard (port 8000) │    │
│  │  + Windows Toast    │   │  + /refresh endpoint           │    │
│  └─────────────────────┘   └────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Directory Structure & File Map

```
news agent/
├── .env                          # Actual API keys (git-ignored)
├── .env.example                  # Template for API keys
├── .gitignore                    # Git ignore file for security
├── pyproject.toml                # Python project metadata & dependencies
├── execution plan.md             # Original design plan (Phase 1–5)
├── run.bat                      # Quick launcher (chcp 65001 + python src\main.py)
├── setup_scheduler.bat          # Windows Task Scheduler installer (batch)
├── setup_scheduler.ps1          # Windows Task Scheduler installer (PowerShell)
├── report.md                    # ← THIS FILE (architecture blueprint)
│
├── .github/
│   └── workflows/
│       └── scrape.yml            # GitHub Actions 2-hourly workflow
│
├── data/                        # Runtime data directory
│   ├── news_agent.db            # SQLite database (seen items)
│   └── pipeline.log             # Last pipeline run log
│
├── dist/                        # Public build directory
│   └── index.html               # Compiled static HTML dashboard
│
├── src/                         # All source code
│   ├── __init__.py              # Package marker (empty)
│   │
│   ├── config.py                # Settings class, loads .env
│   ├── database.py              # SQLite dedup engine (init_db, is_duplicate,
│   │                            #   mark_seen, get_todays_items)
│   ├── aggregator.py            # Pipeline orchestration: collect → dedup →
│   │                            #   summarize → notify → print
│   ├── build_static.py          # Static HTML compiler for GitHub Pages
│   ├── summarizer.py            # LLM categorization via OpenCode Zen API
│   ├── dashboard.py             # FastAPI web UI (inline HTML/CSS, no Jinja2)
│   ├── notifier.py              # Windows toast notification via winotify
│   ├── main.py                  # CLI entry point
│   │
│   ├── sources/                 # One module per data source tier
│   │   ├── __init__.py          # Package marker (empty)
│   │   ├── government.py        # Tiers 1-2 (also defines NewsItem model)
│   │   ├── education.py         # Tier 3
│   │   ├── openstreetmap.py     # Tie 4
│   │   ├── events.py            # Tier 5
│   │   ├── news_publishers.py   # Tier 6
│   │   ├── youtube_monitor.py   # Tier 7
│   │   ├── instagram_scraper.py # Tier 8 (opt-in via --social flag)
│   │   └── twitter_scraper.py   # Tier 11 (opt-in via --social flag)
│   │
│   └── __pycache__/             # Python bytecode cache (auto, git-ignored)
│
└── tests/                       # Empty — no tests yet
```

### 3.1 File-by-File Responsibilities

| File | Lines | Role |
|------|-------|------|
| `src/sources/government.py` | 201 | Defines `NewsItem` Pydantic model; scrapes 6 govt URLs with HTTP + Playwright fallback |
| `src/sources/education.py` | 43 | Scrapes 3 university/college websites |
| `src/sources/openstreetmap.py` | 56 | Nominatim search for 7 business categories |
| `src/sources/events.py` | 59 | Scrapes allevents.in + townscript |
| `src/sources/news_publishers.py` | 106 | Scrapes 4 news sites with RSS + HTML fallback |
| `src/sources/youtube_monitor.py` | 52 | YouTube Data API v3 — 4 channels |
| `src/sources/instagram_scraper.py` | 68 | Playwright browser scrape — 3 accounts (opt-in) |
| `src/sources/twitter_scraper.py` | 64 | Playwright browser search — queries + public figures (opt-in) |
| `src/database.py` | 72 | SQLite dedup: SHA-256 hashing, 30-day TTL |
| `src/summarizer.py` | 104 | OpenCode LLM batch categorization + keyword fallback |
| `src/aggregator.py` | 135 | Pipeline orchestration, digest print, safe helpers |
| `src/build_static.py` | 38 | Compiles Today's SQLite DB rows into static `dist/index.html` |
| `src/dashboard.py` | 111 | FastAPI app, inline HTML/CSS, / and /refresh routes |
| `src/notifier.py` | 42 | Windows toast via winotify, fallback to PowerShell |
| `src/config.py` | 20 | Loads .env → Settings singleton |
| `src/main.py` | 42 | CLI: `python src/main.py` or `python src/main.py dashboard [--social]` |
| `pyproject.toml` | 27 | 11 dependencies, Python ≥3.11 |
| `.github/workflows/scrape.yml` | 70 | Runs scraper, updates DB, compiles static site and deploys to GitHub Pages |

---

## 4. Configuration System

### 4.1 `.env` File (Actual Values)

```
OPENCODE_API_KEY=sk-hAgFKTp6ALFyfEZkL2tfw8dYFDk4t7QrZjgofA1hq1fX4sgl25yOkdSE77yF4fu2
TWITTER_HANDLE=ashish331248986
YOUTUBE_API_KEY=AIzaSyB9zLK2CeRrgJx00tbyyViwO5flRNmVfyI
```

### 4.2 `.env.example` (Template)

```
OPENCODE_API_KEY=your_opencode_api_key_here
TWITTER_HANDLE=your_twitter_handle_here
YOUTUBE_API_KEY=your_youtube_api_key_here
INSTAGRAM_USERNAME=your_instagram_username_here
INSTAGRAM_PASSWORD=your_instagram_password_here
```

### 4.3 `src/config.py` — Settings Class

```python
class Settings:
    opencode_api_key: str      # from OPENCODE_API_KEY
    opencode_api_base: str     # defaults to "https://opencode.ai/zen/v1"
    opencode_model: str        # defaults to "north-mini-code-free"
    twitter_handle: str        # from TWITTER_HANDLE
    youtube_api_key: str       # from YOUTUBE_API_KEY
    instagram_username: str    # from INSTAGRAM_USERNAME (optional)
    instagram_password: str    # from INSTAGRAM_PASSWORD (optional)
    data_dir: str              # defaults to "data"
```

All values are loaded via `python-dotenv` → `os.getenv()` at module import time. The module instantiates a **singleton** `settings = Settings()` at line 20.

### 4.4 `pyproject.toml` — Dependencies

```toml
dependencies = [
    "httpx>=0.27",              # HTTP client for all web scraping
    "beautifulsoup4>=4.12",     # HTML parsing
    "lxml>=5.1",                # XML/HTML parser (faster than html.parser)
    "playwright>=1.44",         # Browser automation (Twitter, Instagram, JS sites)
    "google-api-python-client>=2.130",  # YouTube Data API v3
    "openai>=1.30",             # OpenCode API (OpenAI-compatible endpoint)
    "apscheduler>=3.10",        # (declared but not used — Task Scheduler used instead)
    "fastapi>=0.111",           # Web dashboard framework
    "uvicorn>=0.29",            # ASGI server for FastAPI
    "jinja2>=3.1",              # (declared but not used — inline HTML instead)
    "pydantic>=2.7",            # Data validation for NewsItem
    "python-dotenv>=1.0",       # .env file loading
    "feedparser>=6.0",          # RSS feed parsing (The Hitavada)
]
```

**Note:** `apscheduler` and `jinja2` are declared but **not actually used**. Scheduling is done via Windows Task Scheduler, and the dashboard uses inline string templates to avoid Jinja2 `{`/`}` conflicts with Python `.format()`.

---

## 5. Source Modules (Tiers 1–11)

### 5.1 Tier 1–2: Government & Departments (`government.py`)

**File:** `src/sources/government.py` (201 lines)

#### `NewsItem` Pydantic Model (line 11–17)

The **single data model** used project-wide:

```python
class NewsItem(BaseModel):
    source: str          # Human-readable source name (e.g., "Bilaspur Police")
    title: str           # Headline / link text (max 200 chars)
    url: str             # Full URL to the source item
    summary: str = ""    # Short description (empty unless RSS/YT provides it)
    published_at: str = ""  # ISO date string (YYYY-MM-DD)
    category: str = "general"  # Set by summarizer; initial = "general"
```

#### Source Configuration (line 20–53)

6 government URLs defined as a list of dicts:

| Key | Name | URL | Notes |
|-----|------|-----|-------|
| `district_administration` | District Administration Bilaspur | `https://bilaspur.gov.in/en/` | Has notice categories sub-URLs |
| `nagar_nigam` | Nagar Nigam Bilaspur | `https://nigambilaspur.com/` | Static site |
| `police` | Bilaspur Police | `https://bilaspur.cgpolice.gov.in/` | Government portal |
| `smart_city` | Bilaspur Smart City | `https://www.icccbilaspur.in/` | May have JS |
| `cmo` | CMO Chhattisgarh | `https://cmo.cg.gov.in/` | JS-heavy, Playwright only |
| `railway` | Bilaspur Railway Division | `https://secr.indianrailways.gov.in/view_section.jsp?id=0,4,2212,2270&lang=0` | JSP page |

#### Scraping Strategy (3-tier fallback)

1. **`_fetch()`** (line 56–65): `httpx.get()` with 30s timeout and Chrome UA. Returns raw HTML string or `None`.
2. **`_extract_notices_from_homepage()`** (line 67–102): Parse HTML with BeautifulSoup, find all `<a>` tags, filter by keyword list (26 keywords: "notice", "tender", "recruit", "scheme", "yojana", "circular", etc.), dedup by URL. Returns `NewsItem[]`.
3. **`_extract_all_links()`** (line 105–130): Fallback — all `<a>` tags with text ≥20 chars.
4. **`_scrape_with_playwright()`** (line 133–172): For JS-heavy sites (CMO). Launches headless Chromium, waits for DOM content + 2s idle, evaluates JavaScript to extract all `<a>` and `<h2>`–`<h4>` elements with text. Returns `NewsItem[]`.

#### `scrape_source()` (line 175–190)

Per-source entry point: try HTTP → notice extraction → link extraction → Playwright fallback. Sets `item.source = source["name"]`.

#### `scrape_all()` (line 193–201)

Iterates all 6 sources, catches exceptions per source (isolated failure).

---

### 5.2 Tier 3: Education (`education.py`)

**File:** `src/sources/education.py` (43 lines)

#### Sources (line 9–25)

| Key | Name | URL |
|-----|------|-----|
| `ggv` | Guru Ghasidas Vishwavidyalaya | `https://www.ggu.ac.in/` |
| `abu` | Atal Bihari Vajpayee University | `https://www.abu.ac.in/` |
| `gec` | Government Engineering College Bilaspur | `https://gecbsp.ac.in/` |

**Design:** Reuses `_fetch()`, `_extract_notices_from_homepage()`, `_extract_all_links()` from `government.py` via direct import. No Playwright fallback. Simpler than government module.

#### `scrape_all()` (line 28–43)

For each source: fetch HTML → try notice extraction → fallback to all links → set source name.

---

### 5.3 Tier 4: Business / OpenStreetMap (`openstreetmap.py`)

**File:** `src/sources/openstreetmap.py` (56 lines)

#### Search Queries (line 6–14)

7 OSM amenity categories:

| OSM Tag | Label | Purpose |
|---------|-------|---------|
| `restaurant` | New Restaurant | Detect new eateries |
| `cafe` | New Cafe | Coffee shops, tea stalls |
| `hotel` | New Hotel | Accommodation |
| `hospital` | New Clinic/Hospital | Healthcare facilities |
| `gym` | New Gym | Fitness centers |
| `pharmacy` | New Pharmacy | Medical stores |
| `supermarket` | New Supermarket | Grocery/retail |

#### Scraping Strategy

Uses **Nominatim API** (free, no key needed):
`GET https://nominatim.openstreetmap.org/search?q={category}+in+Bilaspur+Chhattisgarh&format=json&limit=5`

- **User-Agent:** `BilaspurNewsAgent/0.1` (required by Nominatim ToS)
- **Timeout:** 15s
- **Returns:** Each result → `NewsItem(category="business")` with OSM map URL

**Important:** Nominatim has a rate limit of 1 request/second. Our 7 queries run sequentially, which is acceptable for a once-daily pipeline.

---

### 5.4 Tier 5: Events (`events.py`)

**File:** `src/sources/events.py` (59 lines)

#### Sources (line 8–17)

| Name | URL |
|------|-----|
| Allevents.in Bilaspur | `https://allevents.in/bilaspur` |
| Townscript Bilaspur | `https://www.townscript.com/explore/bilaspur` |

#### Scraping Strategy

1. `_fetch()` similar to government.py — httpx with Chrome UA
2. Parse with BeautifulSoup
3. Find all `<h1>`–`<h4>` tags containing an `<a>` link
4. Filter: text ≥ 15 chars, dedup by URL
5. Set category to `"events"`

**Note:** No Playwright fallback. If site is JS-heavy, no items are collected.

---

### 5.5 Tier 6: News Publishers (`news_publishers.py`)

**File:** `src/sources/news_publishers.py` (106 lines)

#### Sources (line 10–31)

| Name | URL | RSS Feed |
|------|-----|----------|
| Haribhoomi | `https://www.haribhoomi.com/` | None |
| Patrika Bilaspur | `https://www.patrika.com/bilaspur-news/` | None |
| Dainik Bhaskar Bilaspur | `https://www.bhaskar.com/chhattisgarh/bilaspur/` | None |
| The Hitavada | `https://www.thehitavada.com/` | `https://www.thehitavada.com/rss.xml` |

#### Scraping Strategy

**RSS path** (for The Hitavada only):
- `_parse_rss()` uses `feedparser` library
- Extracts title, link, summary (first 300 chars), published date
- Category set to `"news"`

**HTML path** (fallback + all other publishers):
- `_scrape_site()` — httpx GET
- `_extract_article_links()` — find all `<h1>`–`<h4>` with `<a>` links, text ≥ 20 chars
- Dedup by URL

**Priority:** RSS is tried first for The Hitavada; if RSS returns items, HTML scrape is skipped. For others, HTML is the only path.

---

### 5.6 Tier 7: YouTube (`youtube_monitor.py`)

**File:** `src/sources/youtube_monitor.py` (52 lines)

#### Channels (line 10–15)

| Channel Name | Channel ID |
|-------------|------------|
| Bilaspur Grand News | `UCsyOylo4H11EvJO2aj8ZZTQ` |
| IBC24 | `UCEXw0LZRKl9J4w65JPFvT_g` |
| News18 Chhattisgarh | `UCx2Q2Id9Q0uykQAqB4be7yQ` |
| Zee MPCG | `UC_SR1NuYftrRGIkCfP4uTiQ` |

#### Scraping Strategy

Uses **YouTube Data API v3** (`google-api-python-client`):
- `youtube.search().list(part="snippet", channelId=..., order="date", maxResults=5)`
- Fetches latest 5 videos per channel
- Extracts: title, video URL (`https://youtube.com/watch?v={id}`), description (first 200 chars), published date (ISO format)
- Category set to `"video"`

**Important:** Requires a Google Cloud project with YouTube Data API v3 enabled. API key is in `.env` as `YOUTUBE_API_KEY`. Free tier = 10,000 quota units/day. Each search() call costs 100 units. 4 channels × 1 call each = 400 units/day (well within limits).

**Graceful degradation:** If `googleapiclient` is not installed (ImportError), returns empty list. If API key is empty, returns empty list. Per-channel exception handling.

---

### 5.7 Tier 8: Instagram (`instagram_scraper.py`)

**File:** `src/sources/instagram_scraper.py` (68 lines)

**Status:** Opt-in only (disabled by default unless `--social` flag is passed).

#### Accounts (line 5–9)

| Username |
|----------|
| `bilaspurgrandnews` |
| `bilaspurdiaries` |
| `bilaspur_times` |

#### Scraping Strategy

Uses **Playwright** (headless Chromium):
1. Launch browser
2. **Optional login** (if `INSTAGRAM_USERNAME` and `INSTAGRAM_PASSWORD` set in `.env`):
   - Navigate to `https://www.instagram.com/accounts/login/`
   - Fill username/password fields
   - Click submit button
   - Wait 5s for login to complete
3. For each account:
   - Navigate to `https://www.instagram.com/{username}/`
   - Wait 3s for page load
   - Evaluate JavaScript to find all `<a href*="/p/">` links
   - Extract `<img alt>` text as post description (first 200 chars)
   - Max 4 posts per account
4. Category set to `"social"`

**Important:** Without login, Instagram shows a login wall after a few requests. Login credentials are optional — if not provided, the scraper attempts to browse publicly, which may fail.

---

### 5.8 Tier 11: Twitter (`twitter_scraper.py`)

**File:** `src/sources/twitter_scraper.py` (64 lines)

**Status:** Opt-in only (disabled by default unless `--social` flag is passed).

#### Public Figures Searched (line 4–6)

```python
PUBLIC_FIGURES = [
    "BilaspurPolice", "CGCMOffice", "railway_bilaspur",
]
```

#### Search Queries (line 17–23)

Generated dynamically:
1. `"Bilaspur news"`
2. `"Bilaspur police"`
3. `"Bilaspur from:{twitter_handle}"` (e.g., `Bilaspur from:ashish331248986`)
4. `"from:BilaspurPolice"`
5. `"from:CGCMOffice"`
6. `"from:railway_bilaspur"`

#### Scraping Strategy

Uses **Playwright** (headless Chromium with `--no-sandbox`):
1. For each query:
   - Navigate to `https://twitter.com/search?q={query}&src=typed_query&f=live`
   - Wait 2s for tweets to render
   - Evaluate JavaScript to extract `article[data-testid="tweet"]` elements
   - Get `[data-testid="tweetText"]` for text content
   - Get `a[href*="/status/"]` for tweet URL
   - Max 3 tweets per query
   - Dedup within session (JavaScript-side `some()` check)
2. Category set to `"social"`
3. All queries run sequentially; per-query exception handling

**Important:** Twitter/X may show a login wall after several requests. The scraper does not attempt login. Success rate depends on current Twitter anti-scraping measures.

---

## 6. Deduplication Engine (SQLite)

**File:** `src/database.py` (72 lines)

### Database Schema

```sql
CREATE TABLE IF NOT EXISTS seen_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_hash TEXT UNIQUE NOT NULL,          -- SHA-256(source + ":" + unique_id)
    source_name TEXT NOT NULL,                  -- e.g., "Bilaspur Police"
    title TEXT,                                 -- item title
    url TEXT,                                   -- item URL
    published_at TEXT,                          -- original publish date
    first_seen_at TEXT DEFAULT (datetime('now'))  -- when we first saw it
);

CREATE INDEX IF NOT EXISTS idx_seen_hash ON seen_items(source_hash);
```

### Key Functions

#### `make_hash(source, unique_id) -> str`
SHA-256 hash of `"{source}:{unique_id}"`. The `unique_id` is the item's URL or title (used in aggregator.py line 54: `unique_id = item.url or item.title`).

#### `is_duplicate(source, unique_id, ttl_days=30) -> bool`
1. Compute hash
2. Query: `SELECT 1 FROM seen_items WHERE source_hash = ? AND first_seen_at > ?`
3. The cutoff is `utcnow - ttl_days` — items older than 30 days are considered "new" again
4. Returns `True` if row exists (i.e., seen within TTL)

#### `mark_seen(source, unique_id, title, url, published_at)`
INSERT OR IGNORE into `seen_items`. Ignores if hash already exists (duplicate).

#### `get_todays_items() -> list[tuples]`
Returns all items seen today (UTC date):
```sql
SELECT source_name, title, url, published_at, first_seen_at
FROM seen_items
WHERE date(first_seen_at) = ?
ORDER BY first_seen_at DESC
```
Returns a list of 5-element tuples `(source_name, title, url, published_at, first_seen_at)`.

#### WAL Mode
```sql
PRAGMA journal_mode=WAL
```
Enabled at connection time for better concurrent read/write performance.

### Database File
Located at `data/news_agent.db` relative to working directory. Size after 196 items: ~108 KB.

---

## 7. Pipeline Orchestration (Aggregator)

**File:** `src/aggregator.py` (135 lines)

### Safe Collection Helper (line 10–18)

```python
def _safe_collect(name: str, fn, *args, **kwargs) -> list[NewsItem]:
```
Wraps every source module call in try/except. Prints progress to stdout. Returns `[]` on exception — **no single source failure crashes the pipeline**.

### `collect_all(social=False) -> list[NewsItem]` (line 24–38)

Order of collection (deterministic, always in this sequence):

| Order | Tier | Source Module | Guard |
|-------|------|--------------|-------|
| 1 | 1–2 | `government.scrape_all()` | Always |
| 2 | 3 | `education.scrape_all()` | Always |
| 3 | 4 | `openstreetmap.scrape_all()` | Always |
| 4 | 5 | `events.scrape_all()` | Always |
| 5 | 6 | `news_publishers.scrape_all()` | Always |
| 6 | 7 | `youtube_monitor.scrape_all(api_key)` | Always |
| 7 | 11 | `twitter_scraper.scrape_all(handle)` | Only if `social=True` |
| 8 | 8 | `instagram_scraper.scrape_all()` | Only if `social=True` |

### `deduplicate(items) -> list[NewsItem]` (line 51–58)

For each item:
1. Compute unique_id = `item.url or item.title`
2. Check `is_duplicate(item.source, unique_id, ttl_days=30)`
3. If not duplicate: call `mark_seen(...)`, add to fresh list
4. Return fresh items (newly seen items)

### `run_pipeline(social=False, log_file="") -> list[NewsItem]` (line 61–96)

The **main orchestrator**:

```
1. Log start timestamp        → "=== News Agent Pipeline — 2026-07-12T19:38 ==="
2. collect_all(social)        → raw list (e.g., 196 items)
3. deduplicate(raw)           → fresh list (first run = all 196 are new)
4. If fresh > 0:
   a. summarize_items(fresh)  → LLM categorization (batch of 30 max)
   b. send_notification()     → Windows toast
5. Write log file              → data/pipeline.log
6. Return summarized items
```

### `print_digest(items)` (line 112–135)

CLI digest output:

```
============================================================
  BILASPUR NEWS DIGEST — 2026-07-12
============================================================

  [POL] POLICE (12)
  --------------------------------------------------
  * Title of police news item...
    [Bilaspur Police] https://example.com/...
    Summary text...

  [GOV] GOVERNMENT (25)
  ...
```

**Category symbols and their mapping:**

| Symbol | Category |
|--------|----------|
| `[GOV]` | government |
| `[POL]` | police |
| `[EDU]` | education |
| `[BIZ]` | business |
| `[EVT]` | event |
| `[HLT]` | health |
| `[RAL]` | railway |
| `[INF]` | infrastructure |
| `[NEW]` | news |
| `[SOC]` | social |
| `[VID]` | video |
| `[*]` | (any other) |

**`_safe()` function (line 107–109):** Protects against Windows console Unicode crashes by encoding to `utf-8` (errors='replace') and decoding back. Replaces remaining `\ufffd` replacement characters with `?`.

### Social Scrapers Feature Flag

```python
SOCIAL_SCRAPERS_ENABLED = False   # line 21
```

Scrapers are enabled if **either**:
1. `social=True` passed to `collect_all()` (i.e., `--social` CLI flag), **or**
2. `SOCIAL_SCRAPERS_ENABLED` constant is changed to `True`

This is a safety measure: Twitter and Instagram scrapers use Playwright which is slow, resource-intensive, and may trigger anti-bot measures. They are kept opt-in.

---

## 8. LLM Summarization & Categorization

**File:** `src/summarizer.py` (104 lines)

### Architecture

Uses the **OpenAI Python SDK** (`openai` package) to call the **OpenCode Zen API** — a free, OpenAI-compatible endpoint.

```python
client = OpenAI(
    api_key=settings.opencode_api_key,
    base_url=settings.opencode_api_base,  # "https://opencode.ai/zen/v1"
)
```

### Model

`north-mini-code-free` — a free model provided by OpenCode. Configured via `.env` → `config.py`.

### Batch Processing Strategy

**Problem:** LLM API calls have token limits and may be slow for large numbers of items.  
**Solution:** Process in batches of 5, up to a maximum of 30 items total.

```python
max_to_summarize = 30
batch_size = 5
for i in range(0, len(to_process), batch_size):
    batch = to_process[i:i + batch_size]
    _process_batch(client, batch)
```

**Remaining items (after 30):** Categorized using keyword-based fallback (`_guess_category()`).

### LLM Prompt (line 47–59)

**System message:**
```
You categorize Bilaspur news. Return a JSON array.
Each object: category (government/police/education/business/event/news/social/infrastructure/health/railway/other),
headline (max 60 chars), importance (1-5). ONLY valid JSON.
```

**User message:**
```
Categorize:
1. [source] title | summary (first 100 chars)
2. [source] title | summary (first 100 chars)
...
```

LLM Parameters:
- `temperature=0.1` — low variation for deterministic categorization
- `max_tokens=3000` — sufficient for 5 items × ~3 JSON objects each

### Response Parsing (line 69–84)

1. Strip whitespace from response
2. Regex search for `\[.*?\]` (JSON array) — handles case where LLM wraps in markdown
3. `json.loads()` the matched array
4. For each result (up to batch size):
   - Set `batch[j].category = result["category"]`
   - If item has no summary, use LLM-generated `headline` as summary
   - If `importance >= 4`, prepend `"breaking:"` to category

**Fail-safe:** If any exception occurs during batch processing (API error, JSON parse error), all items in that batch fall back to `_guess_category()`.

### Keyword Fallback (`_guess_category`, line 99–104)

```python
CATEGORY_KEYWORDS = {
    "government":     ["collector", "district", "administration", "cm", "chief minister", "cmo", "yojana", "scheme"],
    "police":         ["police", "crime", "arrest", "traffic", "missing", "safety"],
    "education":      ["school", "college", "university", "exam", "result", "admission", "student"],
    "business":       ["restaurant", "cafe", "hotel", "shop", "store", "mall", "startup", "business"],
    "event":          ["fest", "festival", "event", "marathon", "exhibition", "fair", "competition"],
    "health":         ["hospital", "clinic", "health", "disease", "camp", "doctor"],
    "railway":        ["train", "railway", "rail", "platform", "station"],
    "infrastructure": ["road", "flyover", "bridge", "construction", "pwd", "smart city", "project"],
}
```

Algorithm:
1. Combine `title + " " + summary + " " + source` into lowercase text
2. For each category, check if any keyword appears in text
3. Return **first match** (order of dict — government checked first, news last)
4. If no match, return `"news"` as default

### Full Pipeline with Summarizer

```
items[:30] ──► LLM batch (5 items each) ──► categorized + summarized
items[30:] ──► keyword fallback ──► categorized (no summary)
```

---

## 9. Desktop Notifications

**File:** `src/notifier.py` (42 lines)

### Primary Method: `winotify`

```python
from winotify import Notification
toast = Notification(
    app_id="Bilaspur News Agent",
    title=f"{len(items)} new news items",
    msg=summary[:200],            # "government: 12 | police: 5 | education: 3 | ..."
    duration="short",
)
toast.show()
```

### Fallback Method: PowerShell

If `winotify` is not installed, falls back to a PowerShell script that uses the Windows Runtime API directly:

```powershell
[Windows.UI.Notifications.ToastNotificationManager, ...] > $null
$template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
...
```

### Item Summary Format

Before sending notification, items are grouped by category:
```
government: 12 | police: 5 | education: 3 | news: 2 | ...
```

---

## 10. Dashboard (FastAPI Web UI)

**File:** `src/dashboard.py` (111 lines)

### Framework

FastAPI application served by Uvicorn on `0.0.0.0:8000`.

### Template System

**Design decision:** Instead of Jinja2, uses a single Python string constant `HEAD` with placeholder tokens:
- `__DATE__` → today's date
- `__TOTAL__` → total item count
- `__CARDS__` → stat cards HTML
- `__SECTIONS__` → category sections HTML

This avoids Jinja2 `{`/`}` template syntax conflicting with Python `.format()` strings.

### HTML Structure (lines 14–57)

```html
<div class="hdr">
  <h1>Bilaspur News Agent</h1>
  <div class="meta">DATE · TOTAL items today</div>
  <a href="/refresh" class="btn">Run Pipeline Now</a>
</div>

<div class="stats">
  <!-- Stat cards: one per category -->
  <div class="sc"><div class="n">12</div><div class="l">Police</div></div>
  ...
</div>

<!-- Category sections -->
<div class="sec">
  <div class="sh"><span>POLICE</span><span class="c">12</span></div>
  <div class="sb">
    <div class="ni">
      <div class="t"><a href="url">Title</a></div>
      <div class="s">Bilaspur Police<span class="tm">2026-07-12</span></div>
    </div>
    ...
  </div>
</div>
```

CSS is inline within `<style>` tags (no external files). Responsive, uses system fonts, clean Material Design-inspired color scheme (`#1a237e` = indigo 900).

### Helper Functions

- **`_e(text)`** (line 60–61): HTML-entity escape (`&`, `<`, `>`, `"`)
- **`_card(name, count)`** (line 64–65): Generates stat card HTML
- **`_section(name, items)`** (line 68–78): Generates category section with max 20 items

### Routes

#### `GET /` (line 81–102)

1. Fetch today's items from `get_todays_items()`
2. Group by source_name (`item[0]`) — note: groups by **source name**, not LLM category
3. Build stat cards + category sections
4. Replace placeholders → return `HTMLResponse`

#### `GET /refresh` (line 105–111)

1. Call `run_pipeline()` (without `social=True`)
2. Return simple HTML page: "Pipeline complete — X new items"
3. Auto-redirect to `/` after 1 second via `<script>setTimeout(...)</script>`

### How Dashboard is Served

Via `main.py` → `run_dashboard()`:
```python
def run_dashboard():
    import uvicorn
    init_db()
    from src.dashboard import app
    print("Dashboard: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
```

---

## 11. Entry Point & CLI

**File:** `src/main.py` (42 lines)

### CLI Interface

```
python src/main.py              → Run pipeline once, print CLI digest
python src/main.py dashboard    → Start FastAPI dashboard at :8000
python src/main.py --social     → Run pipeline WITH Twitter + Instagram scrapers
python src/main.py -s           → Short form of --social
```

### Startup Banner

```
Bilaspur News Agent v0.1
Twitter handle: ashish331248986
OpenCode API: configured
YouTube API: configured
Social scrapers: ENABLED / disabled
```

Also provided: `run.bat` — a convenience wrapper that sets console codepage to UTF-8 and runs `python src\main.py %*`.

---

## 12. Deployment & Scheduling

### 12.1 `setup_scheduler.bat` (28 lines)

Windows batch script that creates two scheduled tasks:

| Task Name | Schedule | Command |
|-----------|----------|---------|
| `BilaspurNewsAgent` | Daily at 8:00 AM | `python src\main.py --social` |
| `BilaspurNewsDashboard` | Daily at 9:00 AM | `python src\main.py dashboard` |

Both run with highest privileges (`/rl HIGHEST`) and interactive (`/it`).

**Usage:** Right-click → Run as Administrator.

### 12.2 `setup_scheduler.ps1` (42 lines)

PowerShell equivalent using `New-ScheduledTaskAction` / `Register-ScheduledTask` cmdlets. Same two tasks. Uses `NT AUTHORITY\SYSTEM` as principal.

**Usage:** Right-click → Run with PowerShell (as Admin).

### 12.3 Manual Testing Commands

```powershell
Start-ScheduledTask -TaskName "BilaspurNewsAgent"
Start-ScheduledTask -TaskName "BilaspurNewsDashboard"
Get-ScheduledTask -TaskName "BilaspurNewsAgent", "BilaspurNewsDashboard"
```

### 12.4 Quick Launch

`run.bat` — double-click to run pipeline:
```batch
chcp 65001 >nul
cd /d "%~dp0"
python src\main.py %*
```

### 12.5 GitHub Actions & GitHub Pages (24/7 Serverless Live Setup)

To run continuously and completely for free, the project uses **GitHub Actions** as the execution runner and scheduler, and **GitHub Pages** as the web host.

* **Workflow (`.github/workflows/scrape.yml`):** Runs every 2 hours on a cron schedule (`0 */2 * * *`) on a headless Ubuntu runner. It configures Python, installs dependencies, downloads Playwright webkit, and executes:
  1. `python src/main.py --social` (runs the scraper and updates `data/news_agent.db`).
  2. `python src/build_static.py` (compiles the daily items into `dist/index.html`).
  3. Git commits the updated database and index file back to the repository (using the `[skip ci]` flag to avoid build loops).
  4. Deploys the static `dist/` folder directly to GitHub Pages.

---

## 13. Data Flow Diagram

```
                         ┌──────────────────────┐
                         │    .env + config.py   │
                         │  (API keys & settings)│
                         └──────────┬───────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
            ▼                       ▼                       ▼
┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐
│  government.py     │  │  education.py      │  │  news_publishers   │
│  (Tier 1-2: 6 src) │  │  (Tier 3: 3 src)   │  │  (Tier 6: 4 src)   │
│  HTTP + Playwright │  │  HTTP only          │  │  RSS + HTTP        │
└─────────┬──────────┘  └─────────┬──────────┘  └─────────┬──────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐
│  openstreetmap.py  │  │  events.py         │  │  youtube_monitor   │
│  (Tier 4: 7 cats)  │  │  (Tier 5: 2 src)   │  │  (Tier 7: 4 ch)   │
│  Nominatim API     │  │  HTTP              │  │  YT Data API v3    │
└─────────┬──────────┘  └─────────┬──────────┘  └─────────┬──────────┘
          │                       │                       │
          │         ┌─────────────┼─────────────┐         │
          │         │             │             │         │
          │         ▼             ▼             ▼         │
          │  ┌─────────────┐ ┌──────────────┐ ┌──────────┴───┐
          │  │twitter_scra │ │instagram_sc  │ │  (social=    │
          │  │(Tier 11)    │ │(Tier 8)      │ │   False by   │
          │  │Playwright   │ │Playwright+   │ │   default)   │
          │  │opt-in       │ │login opt-in  │ │              │
          │  └─────────────┘ └──────────────┘ └──────────────┘
          │                       │
          └───────────┬───────────┘
                      │
                      ▼
            ┌─────────────────┐
            │  aggregator.py  │
            │  collect_all()  │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │  database.py    │
            │  deduplicate()  │
            │  SQLite TTL=30d │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │  summarizer.py  │
            │  OpenCode LLM   │
            │  (batch=5, max30)│
            │  + keyword fallb│
            └────────┬────────┘
                     │
          ┌──────────┼──────────┐
          │          │          │
          ▼          ▼          ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ notifier │ │ CLI      │ │dashboard │
  │ winotify │ │ print    │ │ FastAPI  │
  │ toast    │ │ digest   │ │ :8000    │
  └──────────┘ └──────────┘ └──────────┘
```

---

## 14. Design Decisions

### 14.1 Why not use APScheduler for scheduling?

APScheduler is declared in `pyproject.toml` but **not used**. Instead, the project uses **Windows Task Scheduler** because:
- The app runs on a local Windows machine
- Task Scheduler survives reboots, user logouts, and crashes
- It provides a GUI for monitoring/editing tasks
- No need to keep a Python process running 24/7

### 14.2 Why inline HTML instead of Jinja2?

Jinja2 is declared in `pyproject.toml` but **not used** because:
- Jinja2's `{{ }}` syntax conflicts with Python's `.format()` method
- The template is small (~50 lines) — Jinja2 adds unnecessary complexity
- No user-submitted content — XSS is handled via simple escaping (`_e()`)
- Faster page load — no template engine overhead

### 14.3 Why 30-item limit for LLM summarization?

- **Token limits:** Each batch of 5 items sends ~1000 tokens. 30 items = 6 batches = ~6000 tokens
- **Pipeline speed:** LLM calls take ~5–10 seconds each. 6 calls ≈ 30–60 seconds total, keeping the full pipeline under ~3 minutes
- **Cost efficiency:** Even though the API is free, excessive calls may be rate-limited
- **Quality:** The keyword fallback (`_guess_category()`) is surprisingly accurate for simple categorization

### 14.4 Why SHA-256 hashing for dedup?

- Simple, deterministic, no external dependencies
- Handles Unicode/emoji in titles reliably
- 64-character hex string fits SQLite index efficiently
- Combined with TTL = 30 days, old items naturally expire from consideration

### 14.5 Why `_safe()` for CLI output?

Windows PowerShell/CMD has notorious issues with Unicode characters (especially emoji and non-BMP characters). `_safe()` uses `encode('utf-8', errors='replace').decode('utf-8', errors='replace')` to catch any problematic characters before printing. Any remaining replacement character `\ufffd` is manually replaced with `?`.

### 14.6 Why is `social=False` by default?

- Twitter and Instagram scrapers use Playwright (headless browser), which is:
  - **Slow:** Browser launch takes 3–5 seconds each
  - **Resource-heavy:** Each headless browser uses ~200-400MB RAM
  - **Fragile:** Anti-bot measures may break the scraper
- Social media content is often lower priority for the editorial team
- The `--social` flag makes the decision explicit

### 14.7 Why Nominatim instead of Google Maps API?

- **Cost:** Google Maps Places API costs money beyond free tier
- **No API key needed:** Nominatim is free with User-Agent identification
- **Sufficient for Bilaspur:** For a city with ~5000 mapped businesses, Nominatim's limit of 1 req/s is adequate for daily checks

---

## 15. Limitations & Known Issues

### 15.1 Source Coverage Gaps

The following tiers from the original plan are **not implemented**:

| Tier | Source | Reason |
|------|--------|--------|
| 2 | Electricity board, Water supply, Forest dept, Tourism, RTO, District court, Fire dept | No reliable public URLs found, or low editorial priority |
| 5 (partial) | Facebook Events | Facebook anti-scraping is aggressive; Playwright login flow is complex |
| 9 | Facebook community groups | Not implemented (requires Facebook login + Graph API) |
| 10 | Overpass API (OSM history) | Not implemented — Nominatim used instead (simpler) |

### 15.2 LLM Limitations

- **Max 30 items:** Items beyond 30 use keyword fallback, which is less nuanced than LLM
- **No Hindi support:** LLM prompt is in English; summaries are English-only
- **No bilingual output:** Headlines are English; no Hindi/Chhattisgarhi translation
- **No entity extraction:** LLM prompt doesn't ask for people/places/dates extraction

### 15.3 Technical Issues

- **Twitter scraper may fail:** Twitter/X frequently changes its DOM structure. The `article[data-testid="tweet"]` selector may break with UI updates
- **Instagram scraper may fail:** Without login, Instagram shows login walls. With login, it may trigger security challenges
- **No proxy support:** All scraping is from a single IP; aggressive scraping may trigger rate limits
- **Dashboard does not persist:** The FastAPI dashboard is in-memory; restart loses the current display (though DB persists)
- **No authentication:** Dashboard is accessible to anyone on the network (bound to `0.0.0.0`)
- **First run is slow:** Playwright downloads Chromium on first launch (~150MB)

### 15.4 Configuration Issues

- **.env in repo:** The `.env` file with real API keys is stored in the project directory. It should not be committed to version control
- **No .gitignore:** The project has no `.gitignore` file — `data/`, `__pycache__/`, and `.env` should be excluded

### 15.5 Coverage Quality

- **Duplicate items across sources:** Same news may appear on multiple sites (e.g., Patrika and Bhaskar covering the same event). Dedup is by URL/title hash, not semantic similarity
- **No relevance scoring:** Items are not scored by importance; LLM `importance` field is used only for "breaking" tag
- **No location filtering:** OpenStreetMap searches for "Bilaspur" may include results from other districts

---

## 16. Future Roadmap

### Short-term (Next 1–2 weeks)

- [ ] Add `.gitignore` (exclude `data/`, `__pycache__/`, `.env`)
- [ ] Implement Overpass API for OSM history diff (detect "recently added" businesses)
- [ ] Add Facebook public page scraping via Playwright
- [ ] Add bilingual (Hindi + English) headline generation in LLM prompt
- [ ] Add source freshness tracking in dashboard (show "last updated" time per source)
- [ ] Add `/api/items.json` endpoint for programmatic access
- [ ] Add `--once` flag for single-run mode (already default behavior)

### Medium-term (1–2 months)

- [ ] Implement intelligent dedup using text similarity (e.g., TF-IDF or embeddings)
- [ ] Add email digest (SMTP) for remote access
- [ ] Add Telegram bot integration for instant breaking news
- [ ] Implement entity extraction (people, places, organizations) via LLM
- [ ] Add search/filter functionality in dashboard
- [ ] Add charts/trends page showing news volume by category over time

### Long-term (3+ months)

- [ ] CMS integration — API endpoint to push directly to Developer Bilaspur website
- [ ] Multi-city support — add Korba, Raigarh, Ambikapur as additional regions
- [ ] Machine learning-based relevance scoring instead of keyword matching
- [ ] Mobile push notifications
- [ ] Auto-generated "article draft" with AI-written intro paragraph
- [ ] Sentiment analysis — track positive/negative news trends

---

## 17. Quick Reference

### Commands

```powershell
# Run pipeline once (CLI output)
cd "D:\Developer Bilaspur\news agent"
python src\main.py

# Start dashboard
python src\main.py dashboard

# Run with social scrapers
python src\main.py --social

# Quick launch (double-click)
run.bat
run.bat dashboard
run.bat --social
```

### Key Files

| Action | File |
|--------|------|
| Add new source | `src/sources/` — create new module, register in `aggregator.py` line 5 |
| Change LLM model | Edit `.env` → `OPENCODE_MODEL` |
| Change API endpoint | Edit `.env` → `OPENCODE_API_BASE` |
| Change TTL | `database.py` line 39 — `ttl_days=30` |
| Change max summarized items | `summarizer.py` line 19 — `max_to_summarize = 30` |
| Change batch size | `summarizer.py` line 22 — `batch_size = 5` |
| Enable social by default | `aggregator.py` line 21 — `SOCIAL_SCRAPERS_ENABLED = True` |
| Change dashboard port | `main.py` line 30 — `port=8000` |
| Add YouTube channel | `youtube_monitor.py` — add to `CHANNELS` list |
| Add Instagram account | `instagram_scraper.py` — add to `INSTAGRAM_ACCOUNTS` list |
| Add Twitter search query | `twitter_scraper.py` — add to `queries` list (line 17) |
| Add government source | `government.py` — add to `GOVERNMENT_SOURCES` list (line 20) |
| Add category keyword | `summarizer.py` — add to `CATEGORY_KEYWORDS` dict (line 87) |

### Database

```powershell
# Location
D:\Developer Bilaspur\news agent\data\news_agent.db

# Inspect via SQLite CLI
sqlite3 data\news_agent.db
.tables
SELECT source_name, count(*) as cnt FROM seen_items GROUP BY source_name ORDER BY cnt DESC;
SELECT count(*) FROM seen_items WHERE date(first_seen_at) = date('now');
```

### Known URLs (all sources)

| # | Source | URL |
|---|--------|-----|
| 1 | District Administration Bilaspur | https://bilaspur.gov.in/en/ |
| 2 | Nagar Nigam Bilaspur | https://nigambilaspur.com/ |
| 3 | Bilaspur Police | https://bilaspur.cgpolice.gov.in/ |
| 4 | Bilaspur Smart City | https://www.icccbilaspur.in/ |
| 5 | CMO Chhattisgarh | https://cmo.cg.gov.in/ |
| 6 | Bilaspur Railway Division | https://secr.indianrailways.gov.in/view_section.jsp?id=0,4,2212,2270&lang=0 |
| 7 | Guru Ghasidas Vishwavidyalaya | https://www.ggu.ac.in/ |
| 8 | Atal Bihari Vajpayee University | https://www.abu.ac.in/ |
| 9 | Government Engineering College Bilaspur | https://gecbsp.ac.in/ |
| 10 | OpenStreetMap (Nominatim) | https://nominatim.openstreetmap.org/search |
| 11 | Allevents.in Bilaspur | https://allevents.in/bilaspur |
| 12 | Townscript Bilaspur | https://www.townscript.com/explore/bilaspur |
| 13 | Haribhoomi | https://www.haribhoomi.com/ |
| 14 | Patrika Bilaspur | https://www.patrika.com/bilaspur-news/ |
| 15 | Dainik Bhaskar Bilaspur | https://www.bhaskar.com/chhattisgarh/bilaspur/ |
| 16 | The Hitavada | https://www.thehitavada.com/ (RSS: /rss.xml) |
| 17 | YouTube (4 channels) | Data API v3 |
| 18 | Twitter/X search | https://twitter.com/search (via Playwright) |
| 19 | Instagram (3 accounts) | https://www.instagram.com/ (via Playwright) |

---

*This document describes the complete architecture of the Bilaspur News Agent v0.1. Every file, function, configuration value, and design decision is documented above. For questions or contributions, contact the Developer Bilaspur editorial engineering team.*

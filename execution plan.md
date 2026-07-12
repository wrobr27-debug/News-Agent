# Execution Plan — AI News Monitoring Agent for Developer Bilaspur

## Overview
Build a Python-based AI news intelligence agent that monitors 11 tiers of local sources, aggregates findings, and presents a curated daily dashboard for the Developer Bilaspur editorial team.

---

## Phase 1: Foundation (Week 1)

### 1.1 Project Setup
- [ ] Initialize Python project (`uv init` or `poetry init`)
- [ ] Set up virtual environment
- [ ] Define project structure:
  ```
  news-agent/
  ├── src/
  │   ├── __init__.py
  │   ├── config.py           # All source URLs, API keys, settings
  │   ├── database.py         # SQLite/local storage for seen items
  │   ├── sources/            # One module per tier
  │   │   ├── __init__.py
  │   │   ├── government.py   # Tier 1-2
  │   │   ├── education.py    # Tier 3
  │   │   ├── business.py     # Tier 4
  │   │   ├── events.py       # Tier 5
  │   │   ├── news_publishers.py  # Tier 6
  │   │   ├── youtube.py      # Tier 7
  │   │   ├── instagram.py    # Tier 8
  │   │   ├── facebook.py     # Tier 9
  │   │   └── google_maps.py  # Tier 10
  │   ├── aggregator.py       # Merge, deduplicate, score
  │   ├── summarizer.py       # AI summarization (LLM)
  │   ├── notifier.py         # Dashboard output / email / Telegram
  │   └── main.py             # Entry point / scheduler
  ├── data/                   # SQLite DB, logs
  ├── tests/
  ├── pyproject.toml
  └── execution plan.md
  ```

### 1.2 Core Dependencies
- `httpx` + `beautifulsoup4` + `lxml` — HTML scraping
- `playwright` — Browser automation (Twitter, Instagram, Facebook)
- `google-api-python-client` — YouTube Data API v3 (free)
- `feedparser` — RSS feeds (if available)
- `sqlite3` (stdlib) — Dedup storage
- `openai` — OpenCode API (OpenAI-compatible endpoint)
- `apscheduler` — Cron-like scheduling
- `pydantic` — Data validation
- `fastapi` + `uvicorn` + `jinja2` — Dashboard web UI

---

## Phase 2: Source Implementation (Week 2-3)

### 2.1 Tier 1 — Government Sources
- [ ] District Collector press release scraper
- [ ] Municipal Corporation notice board scraper
- [ ] Bilaspur Police — browser search via Twitter (user's Twitter ID) + website
- [ ] Smart City project updates page
- [ ] PWD project page
- [ ] Chhattisgarh CM announcements (CGM Dashboard)
- [ ] Health department advisories
- [ ] Education department notices
- [ ] Railway division updates (IRCTC / Eastern Railway)

### 2.2 Tier 2 — Department Sources
- [ ] Electricity board outage notices
- [ ] Water supply schedule changes
- [ ] Forest department (eco-tourism, warnings)
- [ ] Tourism department events
- [ ] RTO / Transport department
- [ ] District court judgments / cause list
- [ ] Fire department incident reports

### 2.3 Tier 3 — Universities & Colleges
- [ ] Guru Ghasidas Vishwavidyalaya website
- [ ] Atal Bihari Vajpayee University
- [ ] Government Engineering College
- [ ] CIMS (medical college)
- [ ] Local school / coaching institute notice boards

### 2.4 Tier 4 — Business Sources
- [ ] **OpenStreetMap + Overpass API** — detect new businesses in Bilaspur
- [ ] Justdial / Sulekha — new listings
- [ ] Local business Instagram pages (browser scrape)
- [ ] Real estate portals (MagicBricks, 99acres)

### 2.5 Tier 5 — Events
- [ ] Eventbrite / Allevents.in
- [ ] Facebook Events — browser scrape using Playwright
- [ ] Instagram event posts — browser scrape
- [ ] College fest pages

### 2.6 Tier 6 — Local News Publishers
- [ ] IBC24 scraper
- [ ] Haribhoomi scraper
- [ ] Patrika (Bilaspur edition)
- [ ] Dainik Bhaskar (Bilaspur)
- [ ] The Hitavada
- [ ] Times of India (Raipur/Bilaspur)
- [ ] Navbharat Times

### 2.7 Tier 7 — YouTube
- [ ] YouTube Data API (free): channel uploads monitor
  - Bilaspur Grand News
  - IBC24
  - News18 Chhattisgarh
  - Zee MPCG
- [ ] Fallback: browser scrape YouTube channel pages if API quota exhausted

### 2.8 Tier 8 — Instagram
- [ ] Playwright browser-based login + feed scrape
- [ ] Monitor approved list of pages/journalists/influencers
- [ ] Extract new posts with text, image URLs, timestamps

### 2.9 Tier 9 — Facebook
- [ ] Playwright browser-based community group scrape
- [ ] Public page posts monitor

### 2.10 Tier 10 — OpenStreetMap (replaces Google Maps)
- [ ] **Overpass API** — query for newly added businesses, cafes, clinics, gyms in Bilaspur
- [ ] Cross-check with OSM history to detect "recently added" places
- [ ] Tag-based filtering (amenity=restaurant, shop=*, etc.)

### 2.11 Tier 11 — Public Figures
- [ ] Browser-based Twitter search using user's Twitter ID (search "from:user" queries for MPs, MLAs, Collector, SP, etc.)
- [ ] Instagram follow list — browser scrape
- [ ] Official website monitor

---

## Phase 3: Aggregation & Intelligence (Week 3-4)

### 3.1 Deduplication Engine
- [ ] Store seen URLs, titles, text hashes in SQLite
- [ ] Skip previously seen items (configurable TTL)

### 3.2 Scoring & Prioritization
- [ ] Score by: source tier, freshness, relevance keywords
- [ ] Flag "breaking" or "high importance" items

### 3.3 AI Summarization
- [ ] Use LLM to generate 2-3 sentence Hindi + English summary
- [ ] Extract key entities (people, places, dates)
- [ ] Suggest headline / category / tags

### 3.4 Daily Digest Generator
- [ ] Group items by category
- [ ] HTML email / Markdown dashboard
- [ ] Include source links
- [ ] Show only "new since last check"

---

## Phase 4: Delivery & Dashboard (Week 4)

### 4.1 Dashboard
- [ ] Simple local HTML dashboard (or Flask/FastAPI web UI)
- [ ] Shows today's items in priority order
- [ ] One-click "Draft Article" button → CMS draft
- [ ] Search / filter by category

### 4.2 Notifications
- [ ] Daily email digest
- [ ] Telegram bot (optional)
- [ ] Desktop notification

### 4.3 CMS Integration (Future)
- [ ] API endpoint → push to Developer Bilaspur Website CMS
- [ ] Pre-fill article template with summary + sources

---

## Phase 5: Schedule & Automation (Week 4+)

- [ ] Every 60 min — Tier 1-2 (government)
- [ ] Every 120 min — Tier 3-5 (education, business, events)
- [ ] Every 30 min — Tier 6 (news publishers)
- [ ] Every 240 min — Tier 7-9 (social media + Twitter browser search)
- [ ] Once daily — Tier 10 (OpenStreetMap / Overpass API)
- [ ] On-demand — manual refresh via dashboard

---

## API Key Strategy (Updated)

| Service | What We Use | Cost |
|---------|-------------|------|
| **LLM** | **OpenCode API key** (user-provided) — for all summarization, headline generation, categorization | Free (already have key) |
| **Google Maps** | **OpenStreetMap + Overpass API** — detect new businesses, recently reviewed places | Free, no key needed |
| **YouTube** | YouTube Data API v3 — free tier (10K quota/day) | Free |
| **Instagram** | Browser-based scraping (playwright) + Instagram Basic Display API | Free |
| **Facebook** | Facebook Graph API + browser scraping for community groups | Free |
| **Twitter/X** | **Browser-based search + scraping** using user's Twitter ID to find tweets from local journalists, public figures, and official handles | Free, user passes their Twitter handle/ID |

## Tech Stack Decision

| Component | Choice | Reason |
|-----------|--------|--------|
| Language | Python 3.12+ | Best ecosystem for scraping + AI |
| Scraping | httpx + BeautifulSoup | Lightweight for static pages |
| JS Rendering | Playwright | For Twitter, Instagram, Facebook, SPA sites |
| LLM | OpenCode API (OpenAI-compatible) | User's existing API key, no extra cost |
| Maps | OpenStreetMap + Overpass API | Completely free alternative to Google Maps |
| Storage | SQLite | Simple, file-based, no server |
| Scheduling | APScheduler | Fault-tolerant cron replacement |
| Dashboard | FastAPI + Jinja2 | Quick web UI with minimal deps |
| Deployment | Windows Task Scheduler | Runs on local dev machine |

---

## Status (Built So Far — July 12, 2026)

### ✅ Completed
- [x] Project structure, `pyproject.toml`, deps installed
- [x] `config.py` — loads from `.env` (OpenCode API, Twitter handle, YouTube API key)
- [x] `database.py` — SQLite dedup engine
- [x] Tier 1 — Government scraper (District Admin, Nagar Nigam, Police, Smart City, CMO, Railway)
- [x] Tier 2 — Department sources (included in government.py)
- [x] Tier 3 — Education scraper (GGV, ABU, GEC)
- [x] Tier 4 — OpenStreetMap business detector (restaurants, cafes, hotels, etc.)
- [x] Tier 5 — Events scraper (allevents.in, townscript)
- [x] Tier 6 — News publishers scraper (Haribhoomi, Patrika, Bhaskar, Hitavada) with RSS support
- [x] Tier 7 — YouTube monitor (via YouTube Data API)
- [x] Tier 8 — Instagram browser scraper
- [x] Tier 10 — OpenStreetMap/Nominatim business search
- [x] Tier 11 — Twitter browser scraper (Nitter)
- [x] `aggregator.py` — collects all sources, deduplicates, categories
- [x] `summarizer.py` — OpenCode LLM categorization + headline generation
- [x] `dashboard.py` — FastAPI web UI (port 8000)
- [x] Daily digest output (CLI)
- [x] End-to-end pipeline tested — 200+ items collected per run

### 🚧 Still To Do
- [ ] Set up `.env` with your OpenCode API key, Twitter handle, YouTube API key
- [ ] Set up YouTube API key (free, requires Google Cloud project)
- [ ] Test LLM summarization with OpenCode API
- [ ] Test Twitter scraper with your Twitter handle
- [ ] Test Instagram scraper (may require login)
- [ ] Deploy as automated Windows Task Scheduler daily task
- [ ] Add more source URLs as needed
- [ ] Add Hindi/English bilingual headline generation

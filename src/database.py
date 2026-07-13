import sqlite3
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path("data") / "news_agent.db"


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS seen_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_hash TEXT UNIQUE NOT NULL,
            source_name TEXT NOT NULL,
            title TEXT,
            url TEXT,
            published_at TEXT,
            first_seen_at TEXT DEFAULT (datetime('now')),
            category TEXT DEFAULT 'general',
            summary TEXT DEFAULT '',
            image_url TEXT DEFAULT ''
        );

        CREATE INDEX IF NOT EXISTS idx_seen_hash ON seen_items(source_hash);
    """)
    # Add columns if they do not exist in the table (migration)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(seen_items)")
    columns = [row[1] for row in cursor.fetchall()]
    if "category" not in columns:
        conn.execute("ALTER TABLE seen_items ADD COLUMN category TEXT DEFAULT 'general'")
    if "summary" not in columns:
        conn.execute("ALTER TABLE seen_items ADD COLUMN summary TEXT DEFAULT ''")
    if "image_url" not in columns:
        conn.execute("ALTER TABLE seen_items ADD COLUMN image_url TEXT DEFAULT ''")
    conn.commit()
    conn.close()


def make_hash(source: str, unique_id: str) -> str:
    raw = f"{source}:{unique_id}"
    return hashlib.sha256(raw.encode()).hexdigest()


def is_duplicate(source: str, unique_id: str, ttl_days: int = 30) -> bool:
    item_hash = make_hash(source, unique_id)
    conn = get_conn()
    cutoff = (datetime.utcnow() - timedelta(days=ttl_days)).isoformat()
    row = conn.execute(
        "SELECT 1 FROM seen_items WHERE source_hash = ? AND first_seen_at > ?",
        (item_hash, cutoff),
    ).fetchone()
    conn.close()
    return row is not None


def mark_seen(source: str, unique_id: str, title: str = "", url: str = "", published_at: str = "", image_url: str = ""):
    item_hash = make_hash(source, unique_id)
    conn = get_conn()
    conn.execute(
        """INSERT OR IGNORE INTO seen_items
           (source_hash, source_name, title, url, published_at, image_url)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (item_hash, source, title, url, published_at, image_url),
    )
    conn.commit()
    conn.close()


def update_item_details(source: str, unique_id: str, title: str, category: str, summary: str):
    item_hash = make_hash(source, unique_id)
    conn = get_conn()
    conn.execute(
        "UPDATE seen_items SET title = ?, category = ?, summary = ? WHERE source_hash = ?",
        (title, category, summary, item_hash),
    )
    conn.commit()
    conn.close()


def get_todays_items():
    conn = get_conn()
    # Fetch all items from the last 24 hours to avoid timezone/day-change blank pages
    cutoff = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    rows = conn.execute(
        "SELECT source_name, title, url, published_at, first_seen_at, category, summary, image_url "
        "FROM seen_items WHERE first_seen_at > ? ORDER BY first_seen_at DESC",
        (cutoff,),
    ).fetchall()
    conn.close()
    return rows

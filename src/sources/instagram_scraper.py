from datetime import datetime
from src.sources.government import NewsItem
from src.config import settings

INSTAGRAM_ACCOUNTS = [
    "bilaspurgrandnews",
    "bilaspurdiaries",
    "bilaspur_times",
]


def scrape_all() -> list[NewsItem]:
    """Scrape Instagram profiles for recent posts using Playwright."""
    items = []
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()

        if settings.instagram_username and settings.instagram_password:
            try:
                page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)
                page.fill('input[name="username"]', settings.instagram_username)
                page.fill('input[name="password"]', settings.instagram_password)
                page.click('button[type="submit"]')
                page.wait_for_timeout(5000)
            except Exception:
                pass

        for username in INSTAGRAM_ACCOUNTS:
            try:
                url = f"https://www.instagram.com/{username}/"
                page.goto(url, wait_until="domcontentloaded", timeout=12000)
                page.wait_for_timeout(3000)

                posts = page.evaluate("""() => {
                    const results = [];
                    const links = document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]');
                    for (const a of links) {
                        const href = a.href;
                        const img = a.querySelector('img');
                        const alt = img?.alt || '';
                        const src = img?.src || '';
                        const text = alt.slice(0, 500);
                        if (text.length > 5) {
                            results.push({ text, href, image_url: src });
                        }
                        if (results.length >= 4) break;
                    }
                    return results;
                }""")

                for post in posts:
                    text = post.get("text", "")
                    title = text[:80] if len(text) > 80 else text
                    items.append(NewsItem(
                        source=f"Instagram/@{username}",
                        title=title or "(photo)",
                        url=post.get("href", url),
                        summary=text,
                        category="social",
                        published_at=datetime.now().isoformat()[:10],
                        image_url=post.get("image_url", ""),
                    ))
            except Exception:
                continue

        browser.close()

    return items

from datetime import datetime
from src.sources.government import NewsItem

PUBLIC_FIGURES = [
    "BilaspurPolice", "CGCMOffice", "railway_bilaspur",
]


def scrape_all(twitter_handle: str) -> list[NewsItem]:
    """Search Twitter for Bilaspur-related tweets using Playwright."""
    if not twitter_handle:
        return []

    items = []
    from playwright.sync_api import sync_playwright

    queries = [
        f"Bilaspur news",
        f"Bilaspur police",
        f"Bilaspur from:{twitter_handle}",
    ]
    for username in PUBLIC_FIGURES:
        queries.append(f"from:{username}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        try:
            for query in queries:
                try:
                    url = f"https://twitter.com/search?q={query.replace(' ', '%20')}&src=typed_query&f=live"
                    page.goto(url, wait_until="domcontentloaded", timeout=12000)
                    page.wait_for_timeout(2000)

                    tweets = page.evaluate("""() => {
                        const results = [];
                        const articles = document.querySelectorAll('article[data-testid="tweet"]');
                        for (const a of articles) {
                            const textEl = a.querySelector('[data-testid="tweetText"]');
                            const text = textEl?.innerText?.trim();
                            const link = a.querySelector('a[href*="/status/"]');
                            const href = link?.href || '';
                            if (text && text.length > 10 && !results.some(r => r.text === text)) {
                                results.push({ text: text.slice(0, 200), href });
                            }
                            if (results.length >= 3) break;
                        }
                        return results;
                    }""")

                    for tw in tweets:
                        items.append(NewsItem(
                            source=f"Twitter/{query[:30]}",
                            title=tw["text"],
                            url=tw["href"] or f"https://twitter.com/search?q={query}",
                            category="social",
                            published_at=datetime.now().isoformat()[:10],
                        ))
                except Exception:
                    continue
        finally:
            browser.close()

    return items

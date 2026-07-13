from datetime import datetime
from pathlib import Path
import subprocess
import sys
import os
from src.sources.government import NewsItem
from src.config import settings

INSTAGRAM_ACCOUNTS = [
    "g_news_bilaspur",
    "decode_bilaspur",
    "bilaspurcrime",
    "bilaspur_today_news",
    "lokswar.in",
    "bilaspurdiaries",
]


def process_reel_video_and_extract_frames(reel_url: str, post_id: str) -> tuple[str, str]:
    """Download the Reel video stream and extract screenshots at 2s and 5s using ffmpeg."""
    from src.video_processor import extract_frames
    
    temp_dir = Path("data") / "temp_reels"
    temp_dir.mkdir(parents=True, exist_ok=True)
    video_path = temp_dir / f"{post_id}.mp4"
    
    try:
        # Download the worst resolution mp4 for speed and bandwidth efficiency
        cmd = [sys.executable, "-m", "yt_dlp", "-f", "worst[ext=mp4]", "-o", str(video_path), reel_url]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=40)
        
        if video_path.exists():
            img1, img2 = extract_frames(str(video_path), prefix=f"reel_{post_id}")
            return img1, img2
    except Exception as e:
        print(f"Failed to download/extract frames from Reel {reel_url}: {e}")
    finally:
        if video_path.exists():
            try:
                os.remove(video_path)
            except Exception:
                pass
    return "", ""


def scrape_via_google(page, username: str) -> list[dict]:
    results = []
    try:
        query = f'site:instagram.com/reel OR site:instagram.com/p "{username}"'
        url = f"https://www.google.com/search?q={query}&tbm=vid"
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(2000)
        
        posts = page.evaluate("""() => {
            const list = [];
            const blocks = document.querySelectorAll('div.g, div[data-hveid]');
            for (const b of blocks) {
                const a = b.querySelector('a[href*="instagram.com/p/"], a[href*="instagram.com/reel/"]');
                if (!a) continue;
                const href = a.href;
                
                const titleEl = b.querySelector('h3');
                const titleText = titleEl ? titleEl.innerText : '';
                
                const img = b.querySelector('img');
                const src = img ? img.src : '';
                
                if (href && titleText) {
                    list.push({ text: titleText, href: href, image_url: src });
                }
                if (list.length >= 4) break;
            }
            return list;
        }""")
        return posts
    except Exception as e:
        print(f"Google Search fallback failed for {username}: {e}")
        return []


def scrape_via_imginn(username: str) -> list[NewsItem]:
    import httpx
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin
    
    items = []
    url = f"https://imginn.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    try:
        resp = httpx.get(url, headers=headers, follow_redirects=True, timeout=20)
        if resp.status_code != 200:
            print(f"Imginn mirror returned status code {resp.status_code} for {username}")
            return []
            
        soup = BeautifulSoup(resp.text, "lxml")
        
        # Extract profile picture (typically the first img on the page not inside an anchor link)
        profile_pic = ""
        for img in soup.find_all("img"):
            if not img.find_parent("a"):
                profile_pic = img.get("src", "")
                if profile_pic.startswith("//"):
                    profile_pic = "https:" + profile_pic
                break
                
        # Find all post elements (div.img contains a link with a thumbnail img inside)
        post_divs = soup.find_all("div", class_="img")
        for div in post_divs:
            a = div.find("a", href=True)
            if not a:
                continue
            href = urljoin("https://instagram.com", a["href"])
            img = a.find("img")
            if not img:
                continue
                
            img_src = img.get("src", "")
            if img_src.startswith("//"):
                img_src = "https:" + img_src
                
            caption = img.get("alt", "")
            
            # Truncate title
            title = caption[:80] if len(caption) > 80 else caption
            
            # Post identifier for unique frame names
            post_id = a["href"].split("/p/")[-1].split("/reel/")[-1].replace("/", "").strip()
            
            # Attempt to download video and clip frames
            img_url = ""
            img_url_2 = ""
            if "/reel/" in a["href"] or "/p/" in a["href"]:
                img_url, img_url_2 = process_reel_video_and_extract_frames(href, post_id)
                
            # Fallback to local image hosting (download cover / avatar files) if clipping fails
            from src.video_processor import download_image
            if not img_url:
                img_url = download_image(img_src)
            if not img_url_2:
                img_url_2 = download_image(profile_pic) if profile_pic else "https://cdn-icons-png.flaticon.com/512/174/174855.png"
            
            items.append(NewsItem(
                source=f"Instagram/@{username}",
                title=title or "(photo/reel)",
                url=href,
                summary=caption,
                category="social",
                published_at=datetime.now().isoformat()[:10],
                image_url=img_url,
                image_url_2=img_url_2
            ))
        print(f"Scraped {len(items)} items from Imginn mirror for @{username}.")
        return items
    except Exception as e:
        print(f"Imginn mirror scraping failed for {username}: {e}")
        return []


def scrape_all() -> list[NewsItem]:
    """Scrape Instagram profiles using public mirrors, falling back to Playwright if needed."""
    items = []
    
    # Try public Imginn mirror first (zero login, extremely fast, works on GHA)
    remaining_accounts = []
    for username in INSTAGRAM_ACCOUNTS:
        try:
            mirror_items = scrape_via_imginn(username)
            if mirror_items:
                items.extend(mirror_items)
            else:
                remaining_accounts.append(username)
        except Exception:
            remaining_accounts.append(username)

    if not remaining_accounts:
        return items

    # Fallback to Playwright for remaining profiles if public mirror fails
    print(f"Falling back to Playwright scraper for: {remaining_accounts}")
    from playwright.sync_api import sync_playwright

    state_path = Path("data") / "instagram_state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        
        # Load saved session state if it exists
        if state_path.exists():
            context = browser.new_context(storage_state=str(state_path))
            print("Loaded Instagram login session state.")
        else:
            context = browser.new_context()
            
        page = context.new_page()

        # Perform login and save state if credentials are provided and no session exists
        if not state_path.exists() and settings.instagram_username and settings.instagram_password:
            try:
                print("Instagram session state not found. Attempting login...")
                page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)
                page.fill('input[name="username"]', settings.instagram_username)
                page.fill('input[name="password"]', settings.instagram_password)
                page.click('button[type="submit"]')
                page.wait_for_timeout(6000)
                
                # Check if login was successful
                cookies = context.cookies()
                if any(c['name'] == 'sessionid' for c in cookies):
                    # Save state for future runs
                    context.storage_state(path=str(state_path))
                    print("Instagram login successful. Saved session state.")
                else:
                    print("Login failed: sessionid cookie not found.")
            except Exception as e:
                print(f"Instagram login failed: {e}")

        for username in remaining_accounts:
            try:
                posts = []
                profile_pic = ""
                
                # Try direct profile page navigation first
                url = f"https://www.instagram.com/{username}/"
                page.goto(url, wait_until="domcontentloaded", timeout=12000)
                page.wait_for_timeout(3000)
                
                current_url = page.url
                if "accounts/login" in current_url:
                    print(f"Direct profile page blocked by login wall for {username}. Trying Google Video Search fallback...")
                else:
                    # Extract profile icon and posts from the profile page
                    profile_pic = page.evaluate("""() => {
                        const img = document.querySelector('header img[src*="cdninstagram"]');
                        return img ? img.src : '';
                    }""")
                    
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
                    
                # If direct profile scrape returned nothing, run Google Video Search fallback
                if not posts:
                    posts = scrape_via_google(page, username)
                    profile_pic = "https://cdn-icons-png.flaticon.com/512/174/174855.png"
                    
                for post in posts:
                    text = post.get("text", "")
                    title = text[:80] if len(text) > 80 else text
                    items.append(NewsItem(
                        source=f"Instagram/@{username}",
                        title=title or "(photo/reel)",
                        url=post.get("href", url),
                        summary=text,
                        category="social",
                        published_at=datetime.now().isoformat()[:10],
                        image_url=post.get("image_url", ""),
                        image_url_2=profile_pic or "https://cdn-icons-png.flaticon.com/512/174/174855.png"
                    ))
            except Exception as e:
                print(f"Failed to scrape Instagram username {username}: {e}")
                continue

        browser.close()

    return items

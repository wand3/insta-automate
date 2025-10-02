from playwright.sync_api import sync_playwright

"""
    script to run playwright in interactive mode
"""
p = sync_playwright().start()
browser = p.firefox.launch(headless=False) # Or p.firefox.launch(headless=False), etc.
page = browser.new_page()

# check if login on screen
page.fill("input[name='username']", username)
page.fill("input[name='password']", password)
login = page.query_selector("button[type='submit']:has-text('Log in')")
login.click()
posts = page.query_selector_all('article')
from bs4 import BeautifulSoup
# html_code = page.content()
html = posts[0].inner_html()
soup = BeautifulSoup(html, 'html.parser')
post_user = soup.select_one('a',{'role': 'link'})
post_user.get('href')

text_span = soup.select_one("div[style='display:inline'] span, article span")
spans = soup.find_all("span", class_="_ap3a")
print(spans[2].text)



import json
import random
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import logging

log = logging.getLogger("InstaStrategy")

# Add this method inside your existing Insta class
async def scrape_profiles(self, page, post_json_path: str = "post_details.json", out_json_path: str = "profile_scrapes.json", max_retries: int = 2):
    """
    Read post entries from post_json_path, visit each author's profile using the provided Playwright page,
    scrape structured fields, and write incremental results to out_json_path.
    Designed to be invoked from interact(page).
    """
    post_path = Path(post_json_path)
    out_path = Path(out_json_path)
    if not post_path.exists():
        log.error("post details file not found: %s", post_path)
        return

    try:
        with post_path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        log.error("Failed to load post json: %s", e)
        return

    # normalize list of posts
    if isinstance(raw, dict) and "posts" in raw:
        posts = raw["posts"]
    elif isinstance(raw, list):
        posts = raw
    else:
        log.error("Unexpected post_details.json format")
        return

    results: Dict[str, Dict] = {}
    seen = set()

async def _scrape_one(item: Dict):

    post_id = item.get("post_id") or item.get("id") or item.get("url")
    user_url = item.get("author_profile") or item.get("user_url") or item.get("profile_url")
    if not user_url:
        log.warning("No profile url for post %s", post_id)
        return

    if user_url in seen:
        log.debug("Skipping already scraped %s", user_url)
        return
    seen.add(user_url)

    attempt = 0
    while attempt <= max_retries:
        try:
            # open new tab to keep the original page state intact
            profile_page = await page.context.new_page()
            try:
                await profile_page.goto(user_url, timeout=30000)
                # wait for a stable load; adjust selector to the real target
                try:
                    await profile_page.wait_for_selector("body", timeout=5000)
                except Exception:
                    log.debug("wait_for_selector timed out for %s", user_url)
                # polite delay for dynamic content
                await asyncio.sleep(random.uniform(1.0, 2.5))
                html = await profile_page.content()
                soup = BeautifulSoup(html, "html.parser")

                # scrape fields - adjust selectors to your target
                username_tag = soup.find("h1") or soup.select_one("header h1")
                username = username_tag.get_text(strip=True) if username_tag else None

                meta_desc = soup.find("meta", {"name": "description"}) or soup.find("meta", {"property": "og:description"})
                bio = meta_desc.get("content").strip() if meta_desc and meta_desc.get("content") else None

                # simple numeric extraction for followers/following using text scanning
                text_blob = " ".join(t.get_text(separator=" ", strip=True) for t in soup.find_all(limit=200))
                def _extract_number(tokens):
                    for tok in tokens:
                        idx = text_blob.lower().find(tok)
                        if idx != -1:
                            snippet = text_blob[idx: idx + 120]
                            for part in snippet.split():
                                cleaned = part.replace(",", "").replace(".", "")
                                if cleaned.isdigit():
                                    return part
                    return None

                followers = _extract_number(["followers", "follower"])
                following = _extract_number(["following", "follows"])

                # recent media (first N images)
                imgs = []
                for img in soup.find_all("img", limit=8):
                    src = img.get("src") or img.get("data-src")
                    if src and src.startswith("http"):
                        imgs.append(src)

                results[user_url] = {
                    "_source_post": post_id,
                    "profile_url": user_url,
                    "username": username,
                    "bio": bio,
                    "followers": followers,
                    "following": following,
                    "recent_media": imgs,
                    "_attempt": attempt + 1,
                }

                # incremental write
                try:
                    tmp = out_path.with_suffix(".tmp")
                    with tmp.open("w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)
                    tmp.replace(out_path)
                except Exception as e:
                    log.warning("Failed to save partial results: %s", e)

                await profile_page.close()
                return
            finally:
                # ensure page closed
                try:
                    await profile_page.close()
                except Exception:
                    pass
        except Exception as exc:
            attempt += 1
            log.warning("Error scraping %s attempt %d: %s", user_url, attempt, exc)
            await asyncio.sleep(1 + attempt * 2)
            if attempt > max_retries:
                results[user_url] = {"error": str(exc), "_attempts": attempt}
                log.error("Failed to scrape %s after %d attempts", user_url, attempt)
                # save on permanent failure
                try:
                    tmp = out_path.with_suffix(".tmp")
                    with tmp.open("w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)
                    tmp.replace(out_path)
                except Exception as e:
                    log.warning("Failed to save final failure results: %s", e)
                return

    # sequential or limited-concurrency execution depending on desired behavior
    # for simple integration, run sequentially to avoid extra context management complexity
    for item in posts:
        await _scrape_one(item)

    # final save (redundant if already saved incrementally)
    try:
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error("Failed to write final results: %s", e)

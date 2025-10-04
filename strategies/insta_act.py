import logging
import time
import random
import re
import json
from playwright.async_api import Page, ElementHandle
from .base import InteractionStrategy
from utils.credentials import load_credentials
from utils.logger import get_logger
from utils.cookie_utils import save_cookies
from utils.fs_utils import ensure_parent_folder, save_to_json, extract_post_users_from_json, save_to_profile_json
from utils.insta_utils import check_if_click_successful, parse_count
from pathlib import Path
import asyncio
from typing import List, Any, Coroutine
from bs4 import BeautifulSoup


short_delay = random.uniform(1, 4)


class InstaStrategy(InteractionStrategy):
    """
    Perform user actions on instagram
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        creds = load_credentials("instagram")
        self.username = creds["username"]
        self.password = creds["password"]
        # self.storage_state_path = Path("state") / f"twitter.json"
        self.storage_dir = Path(".storage_state")
        self.storage_file = self.storage_dir / f"cookies.json"

        self.logger.info("InstaStrategy load success")

    async def _login(self, page: Page):
        self.logger.info("Navigating to Instagram login")        # await page.wait_for_load_state()
        await asyncio.sleep(short_delay)
        try:
            login = await page.wait_for_selector("button[type='submit']:has-text('Log in')")
            self.logger.info("Log in button spotted")
            if login:
                await page.fill("input[name='username']", self.username)
                await asyncio.sleep(short_delay)

                password_field = page.get_by_label("Password")

                passwordInputPos = await password_field.bounding_box()
                self.logger.info(f"{passwordInputPos}")

                await page.mouse.move(passwordInputPos["x"] + passwordInputPos["width"] / 2,
                                      passwordInputPos["y"] + passwordInputPos["height"] / 2)
                # await page.mouse.down()
                await page.mouse.click(passwordInputPos["x"] + passwordInputPos["width"] / 2,
                                       passwordInputPos["y"] + passwordInputPos["height"] / 2)
                # await page.mouse.up()
                await page.keyboard.type(f"{self.password}", delay=100)

                # await page.fill("input[name='password']", self.password)
                await asyncio.sleep(short_delay)
                self.logger.info("Log in button click next")

                await login.click()
                self.logger.info("Log in button click success")
                await page.wait_for_load_state()

                await asyncio.sleep(short_delay)

        except Exception as e:
            self.logger.info(f"Login page error {e}")
            raise e

    async def get_post_details(self, soup):
        post_link = ''
        post_user = None  # get_text() returns the username
        post_text = "'span', {'dir': 'auto'}"
        post_likes = 'section:nth-of-type(2)'
        post_comments = None
        post_contents = []

        # post link ------------------
        if_image = soup.find_all('img')
        links = soup.find_all('a', {'role': 'link'})
        for i in range(len(links)):
            try:
                if if_image:
                    link = links[2].get('href')
                    post_link = f'https://www.instagram.com{link}'
            except Exception as e:
                # post_object = await soup.find_all('video')
                # post_link = f'https://instagram.com/{post_object[1]}'
                link = links[2].get('href')
                post_link = f'https://www.instagram.com{link}'

        # post user ------------------
        try:
            user = soup.find_all('a', {'role': 'link'})
            post_user = user[0].get('href')
            username = str(post_user).strip('/')
            post_user = f'https://www.instagram.com/{username}'
        except Exception as e:
            self.logger.error(f"Couldn't get get username count {e}")

        # post text ------------------
        try:
            spans = soup.find_all("span", class_="_ap3a")
            if spans:
                post_text = spans[2].text
        except Exception as e:
            self.logger.error(f"Couldn't get get post text {e}")

        # post likes -----------------
        likes = soup.select_one('section:nth-of-type(2)')
        post_likes = likes.text

        # post comment count ------------------
        try:
            # 1) Find the outer anchor by href pattern (robust) and then the inner number span
            a = soup.find("a", href=re.compile(r"/comments/?"))
            num_span = a.find("span", string=re.compile(r"\d")) if a else None
            raw_text = num_span.get_text(strip=True) if num_span else None
            self.logger.info(f"Checking Comments")

            # 2) Normalize: strip non-digit characters and convert to int
            if raw_text:
                digits = re.sub(r"[^\d]", "", raw_text)  # "2,711" -> "2711"
                comments_count = int(digits) if digits else 0
            else:
                comments_count = 0
            post_comments = comments_count
        except Exception as e:
            self.logger.error(f"Couldn't get comments count {e}")

        # post content links ------------------
        post_images = soup.find_all('img')
        post_videos = soup.find_all('video')
        try:
            if post_images:
                for link in post_images:
                    url = link.get('src')
                    post_contents.append(url)
            elif post_videos:
                for link in post_videos:
                    url = link.get('src')
                    post_contents.append(url)
        except Exception as e:
            self.logger.error(f"Couldn't fetch post images/ videos {e}")

        post = {
            "post_user": post_user,
            "post_link": post_link,
            "post_text": post_text,
            "post_likes": post_likes,
            "post_comments": post_comments,
            "post_contents": post_contents,
        }
        self.logger.info(f"{post}")
        # post_exist = existing.append(post)
        try:
            self.logger.info(f"saving to json post data")
            save_to_json(self, post)

        except Exception as e:
            self.logger.error(f"Couldn't save results {e}")

    async def get_posts(self, page: Page, max_concurrent: int = 5) -> list[ElementHandle]:
        posts = await page.query_selector_all('article')

        # Limit concurrency to avoid overwhelming the browser
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_post(post: ElementHandle):
            async with semaphore:
                html_code = await post.inner_html()
                soup = BeautifulSoup(html_code, 'html.parser')
                return await self.get_post_details(soup)

        # Process all posts with controlled concurrency
        tasks = [process_post(post) for post in posts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Error handling
        successful = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Failed to process post {i}: {result}")
            else:
                successful += 1

        self.logger.info(f"Successfully processed {successful}/{len(posts)} posts")
        return posts

    async def scroll_home(self, page: Page, scrolls: int = 2, delay: float = 2.0):
        """
        Scrolls the Instagram home page downward multiple times.

        Args:
            page: Playwright Page object
            scrolls: number of scroll actions to perform
            delay: seconds to wait between scrolls
        """
        for i in range(scrolls):
            await page.evaluate("""() => {
                window.scrollBy(0, window.innerHeight);
            }""")
            await asyncio.sleep(delay)

    async def _scrape_one(self, page, profile_url, max_retries=2):
        # semaphore-controlled concurrency
        semaphore = asyncio.Semaphore(max_retries)
        seen_profiles = set()

        # dedupe
        if profile_url in seen_profiles:
            self.logger.debug("Already processed %s", profile_url)
            return
        seen_profiles.add(profile_url)

        attempt = 0
        backoff = 1
        while attempt <= max_retries:
            attempt += 1
            try:
                async with semaphore:
                    self.logger.info("Visiting profile (attempt %d) %s", attempt, profile_url)
                    # profile_page = await page.n
                    context = page.context
                    new_page = await context.new_page()
                    try:

                        # polite navigational options: timeout, wait strategy
                        await new_page.goto(profile_url)
                        await asyncio.sleep(short_delay)
                        # wait for a stable point; adjust selector to your site
                        try:
                            # await new_page.wait_for_url(profile_url)
                            verified = await check_if_click_successful(
                                new_page,
                                selector=candidate,
                                url_pattern=profile_url,
                                logger=self.logger
                            )
                            self.logger.info(f'Verified page visit status --- {verified}')
                        except Exception as e:
                            self.logger.debug(f"Failed to visit profile timed out for %s (attempt %d) {e}", profile_url, attempt)

                        # random small delay to allow dynamic content
                        delay = random.uniform(0, short_delay)
                        self.logger.debug("Sleeping %.2fs on %s to allow content load", delay, profile_url)
                        await asyncio.sleep(delay)

                        # html = await new_page.content()  # await Playwright
                        # parsed = _parse_profile_html(html, profile_url)

                        # self.logger.info("Scraped %s: username=%s images=%d", profile_url, parsed.get("username"),
                        #          len(parsed.get("recent_media", [])))

                        # save scraped profile items
                        profile = {
                            "posts": "",
                            "followers": "",
                            "following": "",
                            "website": "",
                            "about": "",
                            "user": profile_url,
                        }
                        self.logger.info(f"{profile}")
                        # post_exist = existing.append(post)
                        try:
                            header = await new_page.query_selector_all('header')
                            html_code = await header[0].inner_html()
                            soup = BeautifulSoup(html_code, 'html.parser')

                            # get all sections
                            sections = soup.find_all("section")
                            html_code = sections[2]
                            details_section = sections[3]
                            lis = html_code.find_all('li')
                            # try to map by position: 0=posts,1=followers,2=following
                            if len(lis) >= 3:
                                # posts
                                try:
                                    posts_text = lis[0].text

                                    # get first numeric token
                                    posts_num = re.search(r'[\d,.]+[kKmM]?', posts_text)
                                    profile["posts"] = posts_num.group(0) if posts_num else None
                                    self.logger.info(f"posts {profile['posts']}")

                                except Exception as e:
                                    self.logger.debug("Failed to parse posts: %s", e)

                                # followers (often inside an <a> with title or inner span)
                                try:
                                    followers_text = lis[1].text
                                    m = re.search(r'[\d,.]+[kKmM]?', followers_text)
                                    followers_val = m.group(0)
                                    profile["followers"] = parse_count(followers_val) if followers_val else None
                                except Exception as e:
                                    self.logger.debug("Failed to parse followers: %s", e)

                                # following
                                try:
                                    following_text = lis[2].text
                                    m = re.search(r'[\d,.]+[kKmM]?', following_text)
                                    profile["following"] = parse_count(m.group(0)) if m else None
                                except Exception as e:
                                    self.logger.debug("Failed to parse following: %s", e)

                            else:
                                # more defensive scanning by tokens
                                text_blob = " ".join(li.text for li in lis)
                                posts_m = re.search(r'([\d,.]+[kKmM]?)\s*posts?', text_blob, flags=re.I)
                                followers_m = re.search(r'([\d,.]+[kKmM]?)\s*followers?', text_blob, flags=re.I)
                                following_m = re.search(r'([\d,.]+[kKmM]?)\s*following', text_blob, flags=re.I)
                                if posts_m:
                                    profile["posts"] = parse_count(posts_m.group(1))
                                if followers_m:
                                    profile["followers"] = parse_count(followers_m.group(1))
                                if following_m:
                                    profile["following"] = parse_count(following_m.group(1))

                            divs = details_section.find_all('div')
                            links = details_section.find_all('a')

                            profile['about'] = divs[6].text if len(divs) <= 10 else None
                            profile['website'] = links[2].text if len(links) >= 3 else None
                            self.logger.info(f"{profile}")

                            # self.logger.info(f"saving to json post data")
                            save_to_profile_json(self, profile)
                            return profile

                        except Exception as e:
                            self.logger.error(f"Couldn't save results {e}")

                        await new_page.close()
                        # polite post-scrape delay
                        await asyncio.sleep(random.uniform(0, short_delay))
                        return
                    finally:
                        try:
                            await new_page.close()
                        except Exception:
                            pass
            except Exception as exc:
                self.logger.exception("Error scraping %s on attempt %d: %s", profile_url, attempt, exc)
                # exponential backoff but bounded
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
                if attempt > max_retries:
                    failure_record = {"_profile_url": profile_url, "error": str(exc),
                                      "_attempts": attempt}
                    self.logger.error("Failed to scrape %s after %d attempts", profile_url, attempt, failure_record)
                    return

    async def scrape_profiles(self, page: Page, profile_json_path: str = "posts_details.json",
                              ):
        users = extract_post_users_from_json(profile_json_path, 'post_user')
        # schedule tasks with bounded concurrency
        # tasks = [asyncio.create_task(self._scrape_one(page, user)) for user in users[:5]]
        # # wait for completion, propagate errors only after logging
        # await asyncio.gather(*tasks)
        for user in users[:5]:
            await self._scrape_one(page, user)

        self.logger.info("Profile scraping run complete; output appended to %s")

    async def interact(self, page: Page):
        await page.goto("https://instagram.com/")
        # 1) If no cookie file, log in fresh and save cookies
        # verify
        value = page.evaluate("() => navigator.webdriver")
        self.logger.error("navigator.webdriver =''", value)

        # login = await page.query_selector("button[type='submit']:has-text('Log in')")
        home = await page.query_selector("div[data-visualcompletion='ignore-dynamic']")

        # if not self.storage_file.exists():
        if not home:
            await self._login(page)
            await asyncio.sleep(short_delay)  # brief pause for stability
            await page.wait_for_selector("div[data-visualcompletion='ignore-dynamic']")

            try:
                # save login info
                save_info = await page.query_selector("button[type='button']:has-text('Save info')")
                if save_info:
                    self.logger.info('"Save info" button spotted')

                    await save_info.click(force=True)
                    self.logger.info('"Save info" button click success')

                    await save_cookies(page, self.storage_file)
                    self.logger.info("Save cookies success")
            except Exception as e:
                self.logger.info(f"Save cookies not successful: {e}")
                raise e
            await save_cookies(page, self.storage_file)
            self.logger.info(f"Cookies saved to {self.storage_file}")
        else:
            # 2) Already logged in via storage state
            self.logger.info("Using existing cookies")

        # 3) Any further actions here…
        try:
            await page.wait_for_selector("div[data-visualcompletion='ignore-dynamic']")
        except:
            self.logger.error("Waiting for home page selector not found")

        self.logger.info("Waiting for home page to load")

        await page.wait_for_load_state()
        await asyncio.sleep(short_delay)
        await self.scroll_home(page)
        # await self.get_posts(page)
        await self.scrape_profiles(page)

        self.logger.info("InstaStrategy finished actions")
        self.logger.info(f"la di la")
        await asyncio.sleep(short_delay)

        return


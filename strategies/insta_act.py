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
from utils.fs_utils import ensure_parent_folder, save_to_json
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

    async def scroll_home(self, page: Page, scrolls: int = 4, delay: float = 2.0):
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

    async def scrape_profiles(self, page: Page, post_json_path: str="post_details.json",
                              out_json_path: str="profile_scrapes.json", max_retries: int = 2):
        pass

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
        await self.get_posts(page)

        self.logger.info("InstaStrategy finished actions")
        self.logger.info(f"la di la")
        await asyncio.sleep(short_delay)

        return


import time
import random
from playwright.async_api import Page, ElementHandle
from .base import InteractionStrategy
from utils.credentials import load_credentials
from utils.logger import get_logger
from utils.cookie_utils import save_cookies
from utils.soup import get_posts
from pathlib import Path
import asyncio
from typing import List, Any, Coroutine

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

    async def get_post_details(self, page: Page):
        post_link = ''
        post_user = "'a',{'role': 'link'}" #get_text() returns the username
        post_text = "'span', {'dir': 'auto'}"
        post_likes = 'section:nth-of-type(2)'
        post_comments = None

        # post link ------------------
        post_object = await soup.find_all('img')
        try:
            if post_object:
                post_link = f'https://instagram.com/reels/{post_object[0]}'
        except Exception as e:
            post_object = await soup.find_all('video')
            post_link = f'https://instagram.com/reels/{post_object[1]}'


        # post comment count ------------------
        # 1) Find the outer anchor by href pattern (robust) and then the inner number span
        a = soup.find("a", href=re.compile(r"/comments/?"))
        num_span = a.find("span", string=re.compile(r"\d")) if a else None
        raw_text = num_span.get_text(strip=True) if num_span else None

        # 2) Normalize: strip non-digit characters and convert to int
        if raw_text:
            digits = re.sub(r"[^\d]", "", raw_text)  # "2,711" -> "2711"
            comments_count = int(digits) if digits else 0
        else:
            comments_count = 0
        post_comments = comments_count

    async def get_posts(self, page: Page) -> list[ElementHandle]:
        posts = await page.query_selector_all('article')
        return posts

    async def interact(self, page: Page):
        await page.goto("https://instagram.com/")
        # 1) If no cookie file, log in fresh and save cookies
        # verify
        value = page.evaluate("() => navigator.webdriver")
        print("navigator.webdriver =", value)

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
        await page.wait_for_selector("div[data-visualcompletion='ignore-dynamic']")
        self.logger.info("InstaStrategy finished actions")
        self.logger.info(f"la di la")
        return


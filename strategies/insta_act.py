import time
import random
from playwright.async_api import Page
from .base import InteractionStrategy
from utils.credentials import load_credentials
from utils.logger import get_logger
from utils.cookie_utils import save_cookies
from pathlib import Path

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
        self.logger.info("Logging in to Insta")
        # await page.wait_for_load_state()
        time.sleep(short_delay)
        try:
            login = await page.query_selector("button[type='submit']:has-text('Log in')")
            self.logger.info("Log in button spotted")
            if login:
                await page.fill("input[name='username']", self.username)
                time.sleep(short_delay)
                await page.fill("input[name='password']", self.password)
                time.sleep(short_delay)
                await login.click(force=True)
                await page.wait_for_load_state()
        except Exception as e:
            self.logger.info(f"Login page error {e}")

        # save login info
        save_info = await page.query_selector("button[type='button']:has-text('Save info')")
        if save_info:
            await save_info.click(force=True)
            save_cookies(page, self.storage_file)
            self.logger.info("Save cookies success")

        # await page.click("div[role='button']:has-text('Next')")
        # await page.click("div[role='button']:has-text('Log in')")
        # await page.wait_for_selector("nav[aria-label='Primary']")
        # self.logger.info("Login successful")

    async def interact(self, page: Page):
        await page.goto("https://instagram.com/")
        await page.wait_for_load_state()
        await self._login(page)


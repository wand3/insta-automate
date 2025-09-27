from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from utils.fs_utils import ensure_parent_folder
import os
from utils.logger import get_logger
import json

class BrowserManager:
    # def __init__(self, headless: bool = False, storage_state_path: str = None):
    def __init__(self, headless: bool = False, state_filename=None, storage_state_path=None):
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info(f"Starting BrowserManager")

        self.storage_state_path = storage_state_path
        self.headless = headless
        # Create (if needed) a hidden folder one level above project root
        storage_dir = ensure_parent_folder(".storage_state")
        # Determine path for this context’s storage state JSON
        self.state_filename = f"cookies.json"
        self.storage_state_path = (
            storage_dir / self.state_filename
        )
        # Determine path for this context’s storage state JSON
        # self.storage_state_path = storage_dir

        self.playwright = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None

    async def __aenter__(self) -> Page:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.firefox.launch(headless=self.headless,
                                                            firefox_user_prefs={
                                                                "media.peerconnection.enabled": False
                                                            }
                                                            )
        # If we have a saved state file, load it
        if self.storage_state_path and self.storage_state_path.is_file():
            self.logger.info(f"Loading storage state from {self.storage_state_path}")
            self.context = await self.browser.new_context(
                storage_state=str(self.storage_state_path),
                viewport={"width": 1440, "height": 900},  # macbook air viewport size
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0",
                locale="en-NG",  # 'en-NG' for English in Nigeria
                timezone_id="Africa/Lagos",  # Lagos is the most common timezone for Nigeria, including Abuja
                color_scheme="light",
                permissions=[],
                extra_http_headers={
                    "Accept-Language": "en-NG,en;q=0.9",  # Prioritize Nigerian English
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    # Consider adding a realistic User-Agent
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0"

                }
            )
            # with open(self.storage_state_path, "r") as f:
            #     cookies = json.load(f)
            #     await self.context.add_cookies(cookies)
            #     self.logger.info(f"Cookies loaded for successfully")
        else:
            if not storage_dir:
                ensure_parent_folder(str(self.storage_state_path))
                logger.info(f"No existing state file at {self.storage_state_path}, starting fresh")
            self.context = await self.browser.new_context(
                storage_state=None,
                viewport={"width": 1440, "height": 900},  # macbook air viewport size
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0",
                locale="en-NG",  # 'en-NG' for English in Nigeria
                timezone_id="Africa/Lagos",  # Lagos is the most common timezone for Nigeria, including Abuja
                color_scheme="light",
                permissions=[],
                extra_http_headers={
                    "Accept-Language": "en-NG,en;q=0.9",  # Prioritize Nigerian English
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    # Consider adding a realistic User-Agent
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0"

                }
            )
            # with open(self.storage_state_path, "r") as f:
            #     cookies = json.load(f)
            #     await context.add_cookies(cookies)
            #     self.logger.info(f"Cookies loaded for successfully")
        # Disable webdriver detection
        await self.context.add_init_script(
            """
                delete navigator.__proto__.webdriver;
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3]
                });
            """
        )

        page = await self.context.new_page()
        page.set_default_timeout(15000)

        return page

    async def __aexit__(self, exc_type, exc, tb) -> None:
        # Always save the updated storage state back to disk
        if self.storage_state_path:
            # This will create/overwrite the JSON with current cookies & storage
            await self.context.storage_state(path=self.storage_state_path)

        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

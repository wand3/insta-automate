from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from utils.fs_utils import ensure_parent_folder
import os
from utils.logger import get_logger


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
        self.storage_state_path = (
            storage_dir / state_filename
            if state_filename
            else None
        )
        # Determine path for this context’s storage state JSON
        # self.storage_state_path = storage_dir

        self.playwright = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None

    async def __aenter__(self) -> Page:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.firefox.launch(headless=self.headless)
        # If we have a saved state file, load it
        if self.storage_state_path and self.storage_state_path.is_file():
            logger.info(f"Loading storage state from {self.storage_state_path}")
            self.context = await self.browser.new_context(
                storage_state=str(self.storage_state_path)
            )
        else:
            if self.storage_state_path:
                logger.info(f"No existing state file at {self.storage_state_path}, starting fresh")
            self.context = await self.browser.new_context()

        page = await self.context.new_page()
        return page
        # if self.storage_state_path and os.path.exists(self.storage_state_path):
        #     self.context = await self.browser.new_context(
        #         storage_state=self.storage_state_path
        #     )
        # else:
        #     self.context = await self.browser.new_context()
        #
        # page = await self.context.new_page()
        # return page

    async def __aexit__(self, exc_type, exc, tb) -> None:
        # Always save the updated storage state back to disk
        if self.storage_state_path:
            # This will create/overwrite the JSON with current cookies & storage
            await self.context.storage_state(path=self.storage_state_path)

        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

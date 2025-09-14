from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from typing import AsyncGenerator


class BrowserManager:
    """Context manager to launch and close Playwright browser contexts."""

    def __init__(self, headless: bool = True):
        self.headless = headless

    async def __aenter__(self) -> AsyncGenerator[Page, None]:
        self._playwright = await async_playwright().start()
        self._browser: Browser = await self._playwright.chromium.launch(headless=self.headless)
        self._context: BrowserContext = await self._browser.new_context()
        page: Page = await self._context.new_page()
        yield page

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self._context.close()
        await self._browser.close()
        await self._playwright.stop()

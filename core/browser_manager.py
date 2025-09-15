from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class BrowserManager:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None

    async def __aenter__(self) -> Page:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.firefox.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        page = await self.context.new_page()
        return page

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

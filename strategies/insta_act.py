from playwright.async_api import Page
from .base import InteractionStrategy
from utils.credentials import load_credentials
from utils.logger import get_logger


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

        self.logger.info("InstaStrategy load success")


    # async def _login(self, page: Page):
    #     self.logger.info("Logging in to Twitter")
    #     await page.goto("https://twitter.com/login")
    #     await page.fill("input[name='text']", self.username)
    #     await page.click("div[role='button']:has-text('Next')")
    #     await page.fill("input[name='password']", self.password)
    #     await page.click("div[role='button']:has-text('Log in')")
    #     await page.wait_for_selector("nav[aria-label='Primary']")
    #     self.logger.info("Login successful")

    async def interact(self, page: Page):
        pass


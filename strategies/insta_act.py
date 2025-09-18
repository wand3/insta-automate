from playwright.async_api import Page
from .base import InteractionStrategy
from utils.credentials import load_credentials


class InstaStrategy(InteractionStrategy):
    """
    Perform user actions on instagram
    """

    async def interact(self, page: Page):
        pass


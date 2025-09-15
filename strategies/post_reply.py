from playwright.async_api import Page
from .base import InteractionStrategy


class ReplyStrategy(InteractionStrategy):
    """
    comments on posts or reels
    """

    async def interact(self, page: Page):
        pass

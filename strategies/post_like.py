from playwright.async_api import Page
from .base import InteractionStrategy


class LikeStrategy(InteractionStrategy):
    """
    likes posts or reels
    """

    async def interact(self, page: Page):
        pass

from typing import Any
from strategies.base import InteractionStrategy
from core.browser_manager import BrowserManager


class Actor:
    """
    Wraps a strategy and executes it inside its own browser session.
    """

    def __init__(self, strategy: InteractionStrategy, headless: bool = True):
        self.strategy = strategy
        self.browser_manager = BrowserManager(headless=headless)

    def set_strategy(self, strategy: InteractionStrategy) -> None:
        """
        Swap in a new InteractionStrategy on the fly.
        """
        self.strategy = strategy

    async def run(self) -> Any:
        """
        Launch Playwright, execute the strategy,
        then clean up the browser context.
        """
        async with self.browser_manager as page:
            return await self.strategy.interact(page)

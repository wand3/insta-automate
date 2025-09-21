from typing import Any
from strategies.base import InteractionStrategy
from core.browser_manager import BrowserManager
from utils.logger import get_logger
from utils.fs_utils import ensure_parent_folder


class Actor:
    """
    Wraps a strategy and executes it inside its own browser session.
    """

    def __init__(self,
                 strategy: InteractionStrategy,
                 storage_state_path: str = None,
                 headless: bool = True):
        storage_dir = ensure_parent_folder(".storage_state")
        storage_path = storage_dir / f"{strategy.__class__.__name__}.json"
        self.storage_state_path = str(storage_path)
        self.strategy = strategy
        self.browser_manager = BrowserManager(
            headless=headless,
            storage_state_path=storage_state_path
        )
        self.logger = get_logger(self.__class__.__name__)

    def set_strategy(self, strategy: InteractionStrategy) -> None:
        """
        Swap in a new InteractionStrategy on the fly.
        """
        self.strategy = strategy

    async def run(self):
        """
        Executes the strategy inside a browser context,
        logging successes or exceptions.
        """
        self.logger.info(f"Starting strategy: {self.strategy.__class__.__name__}")
        try:
            async with self.browser_manager as page:
                result = await self.strategy.interact(page)
            self.logger.info(f"Completed strategy: {self.strategy.__class__.__name__}")
            return result
        except Exception as e:
            self.logger.exception(f"Error in strategy {self.strategy.__class__.__name__}: {e}")
            raise

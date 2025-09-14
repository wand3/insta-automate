from abc import ABC, abstractmethod
from playwright.async_api import Page


class InteractionStrategy(ABC):
    """Defines the interface for all interaction strategies."""
    @abstractmethod
    async def interact(self, page: Page) -> None:
        """
        Execute platform-specific automation steps
        on the given Playwright Page object.
        """
        pass

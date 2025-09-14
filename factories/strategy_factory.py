from strategies.base import InteractionStrategy
from strategies.profile_scrape import ScrapeStrategy
from strategies.post_reply import ReplyStrategy
from strategies.post_like import LikeStrategy


def get_strategy(name: str) -> InteractionStrategy:
    """
    Return the appropriate strategy instance by name.
    """
    mapping = {
        "profile_scrape": ScrapeStrategy,
        "post_reply": ReplyStrategy,
        "post_like": LikeStrategy,
    }
    StrategyClass = mapping.get(name)
    if not StrategyClass:
        raise ValueError(f"No strategy found for '{name}'")
    return StrategyClass()

import asyncio
from core.actor import Actor
from factories.strategy_factory import get_strategy


async def schedule_task(platform: str):
    """
    Single-task scheduler: builds an actor for the chosen platform
    and runs it.
    """
    strategy = get_strategy(platform)
    actor = Actor(strategy, headless=False)
    result = await actor.run()
    return result


async def main():
    """
    Example: run tasks for multiple platforms concurrently.
    """
    platforms = ["twitter_scrape", "twitter_reply"]
    tasks = [schedule_task(p) for p in platforms]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    print(results)

if __name__ == "__main__":
    asyncio.run(main())

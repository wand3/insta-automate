import asyncio
from core.actor import Actor
from factories.strategy_factory import get_strategy


async def main():
    # 1. Create an actor using the scrape strategy
    scrape_strategy = get_strategy("profile_scrape")
    actor = Actor(scrape_strategy, headless=False)

    # 2. Run the scrape and capture results
    scraped_tweets = await actor.run()

    # 3. Dynamically switch to the reply strategy
    reply_strategy = get_strategy("post_reply")
    actor.set_strategy(reply_strategy)

    # 4. Run the reply strategy (e.g., reply to the same hashtag feed)
    await actor.run()

    # 5. Optionally, switch again to any other strategy at any time
    actor.set_strategy(get_strategy("post_like"))
    await actor.run()

if __name__ == "__main__":
    asyncio.run(main())

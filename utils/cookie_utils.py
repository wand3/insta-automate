# utils/cookie_utils.py

import json
from pathlib import Path
from playwright.async_api import Page


async def save_cookies(page: Page, file_path) -> None:
    """
    Extracts all cookies from the given Playwright Page's context
    and writes them to `file_path` in JSON format.

    Args:
        page: the Playwright Page after a successful login
        file_path: path to the JSON file where cookies will be saved
    """
    # Ensure we have a Path object
    file_path = Path(file_path)

    # Make sure parent folder exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Grab cookies from the browser context
    cookies = await page.context.cookies()

    # Write cookies to disk
    file_path.write_text(
        json.dumps(cookies, indent=2),
        encoding="utf-8"
    )

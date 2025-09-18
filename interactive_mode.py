from playwright.sync_api import sync_playwright

"""
    script to run playwright in interactive mode
"""
p = sync_playwright().start()
browser = p.firefox.launch(headless=False) # Or p.firefox.launch(headless=False), etc.
page = browser.new_page()

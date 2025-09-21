from playwright.sync_api import sync_playwright

"""
    script to run playwright in interactive mode
"""
p = sync_playwright().start()
browser = p.firefox.launch(headless=False) # Or p.firefox.launch(headless=False), etc.
page = browser.new_page()

# check if login on screen
login = page.wait_for_selector("button[type='submit']:has-text('Log in')")
login = page.query_selector("button[type='submit']:has-text('Log in')")
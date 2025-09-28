from playwright.sync_api import sync_playwright

"""
    script to run playwright in interactive mode
"""
p = sync_playwright().start()
browser = p.firefox.launch(headless=False) # Or p.firefox.launch(headless=False), etc.
page = browser.new_page()

# check if login on screen
page.fill("input[name='username']", username)
page.fill("input[name='password']", password)
login = page.query_selector("button[type='submit']:has-text('Log in')")
login.click()
posts = page.query_selector_all('article')
from bs4 import BeautifulSoup
# html_code = page.content()
html = posts[0].inner_html()
soup = BeautifulSoup(html, 'html.parser')
post_user = soup.select_one('a',{'role': 'link'})
post_user.get('href')

text_span = soup.select_one("div[style='display:inline'] span, article span")

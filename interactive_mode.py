from playwright.sync_api import sync_playwright

"""
    script to run playwright in interactive mode
"""
p = sync_playwright().start()
browser = p.firefox.launch(headless=False) # Or p.firefox.launch(headless=False), etc.
page = browser.new_page()
page.goto('https://www.instagram.com')
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
spans = soup.find_all("span", class_="_ap3a")
print(spans[2].text)
header = page.query_selector_all('header')

query_selector('svg[aria-label="Like"]')
likePos = i.bounding_box()
page.mouse.move(likePos["x"] + likePos["width"] / 2, likePos["y"] + likePos["height"] / 2)
page.mouse.dblclick(likePos["x"] + likePos["width"] / 2, likePos["y"] + likePos["height"] / 2)
# comment

c = query_selector('textarea[aria-label="Add a comment…"]')
commentPos = c.bounding_box()
page.mouse.move(commentPos["x"] + commentPos["width"] / 2, commentPos["y"] + commentPos["height"] / 2)
page.mouse.click(commentPos["x"] + commentPos["width"] / 2, commentPos["y"] + commentPos["height"] / 2)
page.keyboard.type("kkkkkk", delay=200)
page.keyboard.press('Enter')
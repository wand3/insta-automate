from bs4 import BeautifulSoup


async def get_posts(page, element):
    html_code = page.content()
    soup = BeautifulSoup(html_code, 'html.parser')

    all_posts = soup.find_all(element)
    return all_posts

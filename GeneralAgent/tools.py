import os
import json

class Tools():
    def __init__(self, funs=[]):
        self.funs = funs

    def add_funs(self, funs):
        self.funs += funs

    def get_funs_description(self):
        return '\n\n'.join([get_function_signature(fun) for fun in self.funs])


def google_search(query: str) -> dict:
    """
    google search with query, return a result in list like [{"title": "xx", "link": "xx", "snippet": "xx"}]
    """
    import requests
    SERPER_API_KEY = os.environ.get('SERPER_API_KEY', None)
    if SERPER_API_KEY is None:
        print('Please set SERPER_API_KEY in environment variable first.')
        return None
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    result = json.loads(response.text)
    # 提取organic的title、link、snippet
    organic = [{'title': item['title'], 'link': item['link'], 'snippet': item['snippet']} for item in result['organic']]
    return organic


def wikipedia_search(query: str) -> str:
    """
    wikipedia search with query, return a result in string
    """
    import requests
    from bs4 import BeautifulSoup

    def get_page_obs(page):
        # find all paragraphs
        paragraphs = page.split("\n")
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # find all sentence
        sentences = []
        for p in paragraphs:
            sentences += p.split('. ')
        sentences = [s.strip() + '.' for s in sentences if s.strip()]
        return ' '.join(sentences[:5])

    def clean_str(s):
        return s.replace("\xa0", " ").replace("\n", " ")

    entity = query.replace(" ", "+")
    search_url = f"https://en.wikipedia.org/w/index.php?search={entity}"
    response_text = requests.get(search_url).text
    soup = BeautifulSoup(response_text, features="html.parser")
    result_divs = soup.find_all("div", {"class": "mw-search-result-heading"})
    if result_divs:
        result_titles = [clean_str(div.get_text().strip()) for div in result_divs]
        obs = f"Could not find {query}. Similar: {result_titles[:5]}."
    else:
        page = [p.get_text().strip() for p in soup.find_all("p") + soup.find_all("ul")]
        if any("may refer to:" in p for p in page):
            obs = wikipedia_search("[" + query + "]")
        else:
            page_content = ""
            for p in page:
                if len(p.split(" ")) > 2:
                    page_content += ' ' + clean_str(p)
                    if not p.endswith("\n"):
                        page_content += "\n"
            obs = get_page_obs(page_content)
            if not obs:
                obs = None
    return obs


def scrape_web(url: str) -> (str, str, [str], [str]):
    """
    Scrape web page, return (title: str, text: str, image_urls: [str], hyperlinks: [str]) when success, otherwise return None.
    """
    """
    Scrape web page, return BeautifulSoup object soup when success, otherwise return None.
    page title: soup.title.string
    page text content: re.sub(r'<style.*?</style>', '', soup.get_text(), flags=re.DOTALL) (you should import re first)
    image urls: [image['src'] for image in soup.find_all('img')]
    hyperlinks: [(link.text, urljoin(url, link["href"])) for link in soup.find_all("a", href=True) if urljoin(url, link["href"].startswith('http'))] (from requests.compat import urljoin first)
    """
    import re
    from playwright.sync_api import sync_playwright
    from requests.compat import urljoin
    from bs4 import BeautifulSoup
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(url)
            page.wait_for_load_state()
            html_content = page.content()
            soup = BeautifulSoup(html_content, "html.parser")
            title = str(soup.title.string)
            text = str(re.sub(r'<style.*?</style>', '', soup.get_text(), flags=re.DOTALL))
            image_urls = [str(image['src']) for image in soup.find_all('img')]
            hyperlinks = [(str(link.text), str(urljoin(url, link["href"]))) for link in soup.find_all("a", href=True) if urljoin(url, link["href"]).startswith('http')]
            return (title, text, image_urls, hyperlinks)
        except Exception as e:
            import logging
            logging.exception(e)
        finally:
            browser.close()
    return None


def get_function_signature(func):
    """Returns a description string of function"""
    import inspect
    sig = inspect.signature(func)
    sig_str = str(sig)
    desc = f"{func.__name__}{sig_str}"
    if func.__doc__:
        desc += func.__doc__
    return desc


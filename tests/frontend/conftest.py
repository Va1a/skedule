from bs4 import BeautifulSoup


def parse_html(response):
    return BeautifulSoup(response.data, "html.parser")

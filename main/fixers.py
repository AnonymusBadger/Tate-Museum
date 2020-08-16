import re


def set_first_page(url):
    if "page=" in url:
        url = re.sub(r"page=([\d]*)&", "", url)
        return url
    return url

import requests
from bs4 import BeautifulSoup
import re
import os


class Page:
    url = None
    title = None
    keywords = []
    description = None
    authority = 1
    hub = 1

    def __init__(self, url, title: str):
        self.url = url
        self.title = title.replace('\n', ' ')

    def __str__(self) -> str:
        return "[url: " + self.url + ", title: " + self.title + "]"


# 伪造请求头，伪装成浏览器
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
    "Connection": "keep-alive",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8"
}

page_map = {}

link_queue = []


def get_charset(res):
    if res.encoding == 'ISO-8859-1':
        encodings = requests.utils.get_encodings_from_content(res.text)
        if encodings:
            encoding = encodings[0]
        else:
            encoding = res.apparent_encoding
    else:
        encoding = res.encoding
    return encoding


def search_page_hits(url):
    link_queue.append(url)
    stop_flag = False
    search_lim = 100

    while len(link_queue) != 0:
        try:
            url = link_queue.pop(0)
            res = requests.get(url, headers=headers, timeout=2)
            res.encoding = get_charset(res)
            html = res.text
            soup = BeautifulSoup(html, 'lxml')

            page = Page(url, soup.title.string)

            keywords = soup.find(attrs={'name': 'keywords'}).get('content').replace('\n', ' ').strip()
            description = soup.find(attrs={'name': 'description'}).get('content').replace('\n', ' ').strip()
            page.keywords = keywords.split(',')
            page.description = description

            print(len(link_queue), page)
            page_map[url] = page

            hub_tmp = page.hub
            for link in soup.find_all(name='a', attrs={'href': re.compile(r'^http:')}):
                link_url = link.get('href')
                if link_url in page_map:
                    page.hub += page_map[link_url].authority
                    page_map[link_url].authority += hub_tmp
                else:
                    children_page = Page(link_url, link.text)
                    print(len(link_queue), children_page)
                    page_map[link_url] = children_page
                if not stop_flag:
                    link_queue.append(link_url)
                    if len(link_queue) >= search_lim:
                        stop_flag = True
        except Exception as e:
            print(e.args)


def write_file(path):
    count = 0
    with open(path, 'w', encoding='utf8') as file:
        for val in page_map.values():
            count += 1
            file.write(val.url + '||||' + val.title + '||||' + str(val.authority) + '||||' + str(val.hub) + '||||' + str(val.keywords) + '||||' + str(val.description) + '\n')
    print(str(count) + '条记录已写入')


if __name__ == '__main__':
    rounds = 5
    out_path = "./pages_data/"
    seed_url = "https://www.hao123.com/"

    for i in range(rounds):
        search_page_hits(seed_url)
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    write_file(out_path + "pages.txt")

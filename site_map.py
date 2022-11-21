import requests as req
from bs4 import BeautifulSoup as bs
from urllib.parse import parse_qsl, urlunparse, urlparse, urljoin

def joinurl(root:str, url:str, page:str):
    url = url.strip()
    page = page.strip()

    if url.startswith("http://") or url.startswith("https://"):
        return url

    if not len(page):
        page = root

    url = urlparse(url)
    url = url._replace(scheme="")
    url = url._replace(netloc="")
    url = url._replace(fragment="")

    filtered_params = []
    for query_pair in parse_qsl(url.query):
        name, val = query_pair

        val_url = urlparse(val)

        same = list(filter(lambda pair: pair[0] == name, parse_qsl(val_url.query)))

        if len(same) == 0:
            filtered_params.append("{}={}".format(name, val))

    url = url._replace(query="&".join(filtered_params))

    return urljoin(page, urlunparse(url))

class URL_Entry:
    def __init__(self, url, page = "", label=""):
        self.url = url
        self.history = []
        self.endpoint_url = ""
        self.pages = [page]
        self.status_code = ""
        self.label = label

site_root = "cr-obr.ru"

known_urls = set("http://"+site_root)
processed_urls = dict()
tasks = [URL_Entry("http://"+site_root)]

counter = 0

exlude_dirs = ["/auth", "/ajax", "/dev", "/bitrix/admin", "/thanks", "/tests"]

while len(tasks):
    ar_url = tasks.pop()

    exclude = False
    for dir in exlude_dirs:
        if (site_root + dir) in ar_url.url:
            exclude = True

    if exclude:
        continue

    if not (ar_url.url.startswith("https://" + site_root) or ar_url.url.startswith("http://" + site_root)):
        continue

    try:
        print("try {} [{}] tasks ({})".format(ar_url.url, counter, len(tasks)))

        response = req.get(ar_url.url)

        ar_url.history = response.history
        ar_url.endpoint_url = response.url
        ar_url.status_code = response.status_code

        processed_urls[ar_url.url] = ar_url
    except:
        ar_url.status_code = "connection error"

        processed_urls[ar_url.url] = ar_url
        continue

    page_url = response.url

    counter += 1

    if response.status_code == 200 and "text/html" in response.headers['Content-type']:
        html_bs = bs(response.text, "html.parser")

        links = html_bs.findAll("a")
        imgs = html_bs.findAll("img")

        for link in links:
            link_url : str = link.get('href')
            
            if link_url is None:
                continue

            link_url = link_url.strip()

            if len(link_url) == 0 or link_url.startswith("#") or link_url.startswith("mailto:") or link_url.startswith("tel:"):
                continue

            target_url = joinurl(site_root, link_url, page_url)

            if target_url in processed_urls:
                processed_urls[target_url].pages.append(page_url)
            elif target_url not in known_urls:
                tasks.append(URL_Entry(target_url, page_url, link.text.strip().replace("\n", "")))
                known_urls.add(target_url)
        continue
        for img in imgs:
            img_url : str = img.get('src')
            
            if img_url is None:
                continue

            img_url = img_url.strip()

            if len(img_url) == 0 or img_url == "#" or img_url.startswith("mailto:") or link_url.startswith("tel:"):
                continue

            target_url = joinurl(site_root, img_url, page_url)

            if target_url in processed_urls:
                processed_urls[target_url].pages.append(page_url)
            elif target_url not in known_urls:
                tasks.append(URL_Entry(target_url, page_url))
                known_urls.add(target_url)
            # else:
            #     tasks.append(URL_Entry(target_url, page_url))

print("tasks counter ", len(tasks))

for url in processed_urls:
    with open("C:\\Users\\alkir\\OneDrive\\Рабочий стол\\pages_result.csv", "w+", encoding="utf-8") as f:
        f.write("Целевой адрес;Список редиректов;Конечная страница;Код статуса конечной страницы;Список страниц;Есть редиректы;Текст ссылки\n")

        for url in processed_urls.values():
            redirects_formatted = ",".join(map(lambda redir: redir.url + "({})".format(redir.status_code), url.history))

            f.write("{};{};{};{};{};{};{}\n".format(url.url, redirects_formatted, url.endpoint_url, url.status_code, ",".join(url.pages), "Да" if len(url.history) else "Нет", url.label if url.label is not None else ""))
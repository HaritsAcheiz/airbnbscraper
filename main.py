import csv
import os
import random

import requests
from bs4 import BeautifulSoup
from requests import ConnectTimeout
from requests.exceptions import ProxyError


def get_proxy():
    print("Collecting proxies...")
    with requests.Session() as s:
        response = s.get('https://free-proxy-list.net/')
    s.close()
    soup = BeautifulSoup(response.text, 'html.parser')
    list_data = soup.select('table.table.table-striped.table-bordered>tbody>tr')
    proxies = []
    blocked_cc = ['IR','RU']
    for i in list_data:
        ip = i.select_one('tr > td:nth-child(1)').text
        port = i.select_one('tr > td:nth-child(2)').text
        cc = i.select_one('tr > td:nth-child(3)').text
        if cc in blocked_cc:
            continue
        else:
            proxies.append(f'{ip}:{port}')
    print(f"{len(proxies)} proxies collected")
    return proxies

def choose_proxy(proxies):
    selected_proxies=[]
    for i, item in enumerate(proxies):
        if i < len(proxies) and len(selected_proxies) < 8:
            formated_proxy = {
                "http": f"http://{item}",
                "https": f"http://{item}"
            }
            print(f'checking {formated_proxy}')
            try:
                with requests.Session() as session:
                    session.get(url='https://www.airbnb.com', proxies=formated_proxy, timeout=3)
                session.close()
                selected_proxies.append(item)
                print(f'{item} selected')
            except Exception as e:
                print(f"not working with {e}")
                pass
        else:
            break
    return selected_proxies

def get_detail_url(url, selected_proxies):
    print('Collecting url...')
    parsed_url = url.split('/')
    url_schema = f"{parsed_url[0]}/{parsed_url[1]}/{parsed_url[2]}"
    detail_url_locators = "div.gh7uyir.giajdwt.g14v8520.dir.dir-ltr > div"
    next_page_locator = "a._1bfat5l"
    selected_proxy = random.choice(selected_proxies)
    end = False
    page = 1
    next_page_url = url
    detail_urls = list()
    while not end:
        if page % 10 == 0:
            selected_proxy = random.choice(selected_proxies)
        trial = 0
        while (trial < 8):
            try:
                session = requests.Session()
                formated_proxy = {
                    "http": f"http://{selected_proxy}",
                    "https": f"http://{selected_proxy}"
                }
                headers = {
                    'referer': next_page_url,
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0',
                    }
                response = session.get(next_page_url, proxies=formated_proxy, headers=headers, timeout=(3,27))
                session.close()
                break
            except (ProxyError, ConnectTimeout) as e:
                print(e)
                selected_proxy = random.choice(selected_proxies)
                print(f"Change proxy to {selected_proxy}")
                trial += 1

        if trial < 8:
            soup = BeautifulSoup(response.text, 'html.parser')
            try:
                next_page_url = f"{url_schema}{soup.select_one(next_page_locator)['href']}"
            except TypeError:
                end = True
            html_detail_urls = soup.select(detail_url_locators)
            url_locator = "div.cy5jw6o.dir.dir-ltr > a"
            for i in html_detail_urls:
                detail_urls.append(f"{url_schema}/{i.select_one(url_locator)['href']}")
            print(f"{len(detail_urls)} url collected from {str(page)} page")
            page += 1

        else:
            print("Proxy Error")
            detail_urls = None
            break

    return detail_urls

def get_datas(urls, selected_proxies):
    print('Collecting datas...')
    datas = list()
    name_locator = 'h1._fecoyn4'
    instagram_locator = 'div.d1isfkwk.dir.dir-ltr>span.ll4r2nl.dir.dir-ltr'
    website_locator = 'div.d1isfkwk.dir.dir-ltr>span.ll4r2nl.dir.dir-ltr'

    for counter, url in enumerate(urls):
        if counter % 10:
            selected_proxy = random.choice(selected_proxies)
        data = {
            'link': [],
            'name': [],
            'instagram': [],
            'website': []
        }
        trial = 0
        while (trial < 3):
            try:
                session = requests.Session()
                formated_proxy = {
                    "http": f"http://{selected_proxy}",
                    "https": f"http://{selected_proxy}"
                }
                headers = {
                    'referer': url,
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0'
                    }
                response = session.get(url, proxies=formated_proxy, headers=headers, timeout=(3,27))
                session.close()
                break
            except (ProxyError, ConnectTimeout) as e:
                print(e)
                selected_proxy = random.choice(selected_proxies)
                print(f"Change proxy to {selected_proxy}")
                trial += 1

        if trial < 3:
            soup = BeautifulSoup(response.text, 'html.parser')
            try:
                data['link'] = response.url()
                data['name'] = soup.select_one(name_locator)
                data['instagram'] = soup.select_one(instagram_locator)
                data['website'] = soup.select_one(website_locator)
            except TypeError:
                break
            datas.append(data.copy())

        else:
            continue

    return datas

def to_csv(datas=None, filepath=None):
    print('Creating file...')
    folder = filepath.rsplit("/", 1)[0]
    try:
        os.mkdir(folder)
    except FileExistsError:
        pass
    with open(filepath, 'w+', encoding="utf-8", newline='') as f:
        headers = ['link', 'name', 'instagram', 'website']
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for i in datas:
            writer.writerow(i)
        f.close()
    print(f'{filepath} created')

if __name__ == '__main__':
    url = "https://www.airbnb.com/s/Belgium/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&price_filter_input_type=0&price_filter_num_nights=5&query=Belgium&place_id=ChIJl5fz7WR9wUcR8g_mObTy60c&date_picker_type=calendar&flexible_trip_lengths%5B%5D=weekend_trip&checkin=2023-01-29&checkout=2023-01-30&adults=1&source=structured_search_input_header&search_type=autocomplete_click"
    save_path = r"C:\project\airbnbscraper\result.csv"
    proxies = get_proxy()
    selected_proxies = choose_proxy(proxies)
    detail_urls = get_detail_url(url, selected_proxies=selected_proxies)
    datas = get_datas(detail_urls, selected_proxies=selected_proxies)

    to_csv(datas, save_path)
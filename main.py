import csv
import os
import random

import requests
from bs4 import BeautifulSoup
from requests import ConnectTimeout, ReadTimeout, ConnectionError
from requests.exceptions import ProxyError
from urllib3.exceptions import ReadTimeoutError


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
        else:
            pass
        trial = 0
        success = False
        while (trial < 8 and success is False):
            try:
                session = requests.Session()
                formated_proxy = {
                    "http": f"http://{selected_proxy}",
                    "https": f"http://{selected_proxy}"
                }
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0'
                    }
                response = session.get(next_page_url, proxies=formated_proxy, headers=headers, timeout=(3,27))
                session.close()
                success = True
            except (ProxyError, ConnectTimeout, ReadTimeoutError, ReadTimeout, ConnectionError, ConnectionError) as e:
                print(e)
                selected_proxy = random.choice(selected_proxies)
                print(f"Change proxy to {selected_proxy}")
                trial += 1

        if trial < 8:
            soup = BeautifulSoup(response.text, 'html.parser')
            try:
                next_page_url = f"{url_schema}{soup.select_one(next_page_locator)['href']}"
                print(next_page_url)
            except TypeError as e:
                print(e)
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
            page += 1

    return detail_urls

def get_datas(urls, selected_proxies):
    print('Collecting datas...')
    datas = list()
    name_locator = 'h1._fecoyn4'
    profile_locator = 'div.h1144bf3.dir.dir-ltr>div.a'
    # website_locator = 'div.d1isfkwk.dir.dir-ltr>span.ll4r2nl.dir.dir-ltr'
    selected_proxy = random.choice(selected_proxies)
    for counter, url in enumerate(urls):
        parsed_url = url.split('/')
        url_schema = f"{parsed_url[0]}/{parsed_url[1]}/{parsed_url[2]}"
        if counter % 10:
            selected_proxy = random.choice(selected_proxies)
            print(f"Change proxy to {selected_proxy}")
        else:
            pass
        print(counter)
        print(url)
        data = {
            'link': [],
            'name': [],
            'instagram': []
            # 'website': []
        }
        status_code = 0
        trial = 0
        while (trial < 5 and status_code != 200):
            try:
                if (status_code != 0 or status_code != 200):
                    selected_proxy = random.choice(selected_proxies)
                    print(f"Change proxy to {selected_proxy}")
                else:
                    pass
                session = requests.Session()
                formated_proxy = {
                    "http": f"http://{selected_proxy}",
                    "https": f"http://{selected_proxy}"
                }
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0'
                }
                response = session.get(url, proxies=formated_proxy, headers=headers, timeout=(3,27))
                session.close()
                status_code = response.status_code

            except (ProxyError, ConnectTimeout, ReadTimeoutError, ReadTimeout, ConnectionError, ConnectionError) as e:
                print(e)
                selected_proxy = random.choice(selected_proxies)
                print(f"Change proxy to {selected_proxy}")
                trial += 1

        print(f'got response {status_code}')

        if trial < 5:
            soup = BeautifulSoup(response.text, 'html.parser')
            data['link'] = response.url
            data['name'] = soup.select_one(name_locator)

            try:
                profile_url = f"{url_schema}{soup.select_one(profile_locator)['href']}"
                data['instagram'] = get_instagram(url=profile_url, selected_proxy=selected_proxy)
            except Exception:
                data['instagram'] = None

            # data['website'] = soup.select_one(website_locator)

            datas.append(data.copy())

        else:
            print('proxy error')
            continue

    return datas


def get_instagram(url,selected_proxy):
    session = requests.Session()
    formated_proxy = {
        "http": f"http://{selected_proxy}",
        "https": f"http://{selected_proxy}"
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0'
    }
    response = session.get(url, proxies=formated_proxy, headers=headers, timeout=(3, 27))
    session.close()
    soup = BeautifulSoup(response.text, 'html.parser')
    job_locator = 'div._o7dyhr>section>div:nth-child(4)>section>div:nth-child(2)>div:nth-child(3)>span._1ax9t0a'
    job = soup.select_one(job_locator).text
    instagram = job.split('@')[-1].split()[0]
    return instagram

def to_csv(datas=None, filepath=None):
    print('Creating file...')
    folder = filepath.rsplit("/", 1)[0]
    try:
        os.mkdir(folder)
    except FileExistsError:
        pass
    with open(filepath, 'w+', encoding="utf-8", newline='') as f:
        headers = ['link', 'name', 'instagram']
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for i in datas:
            writer.writerow(i)
        f.close()
    print(f'{filepath} created')

if __name__ == '__main__':
    url = "https://www.airbnb.com/s/Belgium/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&price_filter_input_type=0&price_filter_num_nights=5&query=Belgium&place_id=ChIJl5fz7WR9wUcR8g_mObTy60c&date_picker_type=calendar&flexible_trip_lengths%5B%5D=weekend_trip&checkin=2023-01-29&checkout=2023-01-30&adults=1&source=structured_search_input_header&search_type=autocomplete_click"
    save_path = "C:/project/airbnbscraper/result.csv"
    proxies = get_proxy()
    selected_proxies = choose_proxy(proxies)
    # selected_proxies = ['158.69.52.218:9300','178.33.198.181:3128','201.229.250.19:8080', '115.68.221.147:80', '112.217.162.5:3128', '179.96.28.58:80', '147.139.193.92:3128']
    # detail_urls = get_detail_url(url, selected_proxies=selected_proxies)
    # print(detail_urls)
    detail_urls = ['https://www.airbnb.com//rooms/45249678?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/670806019201784094?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/556403144075739762?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/640957686671430797?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43537696?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/19157408?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/663178942796891124?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52332812?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/23837349?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52580537?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/4985457?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/556320999594495655?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000']
    datas = get_datas(detail_urls, selected_proxies=selected_proxies)
    to_csv(datas, save_path)
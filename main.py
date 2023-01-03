import csv
import os
import random

import requests
from bs4 import BeautifulSoup
from requests import ConnectTimeout, ReadTimeout, ConnectionError
from requests.exceptions import ProxyError
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from urllib3.exceptions import ReadTimeoutError
from selenium.webdriver.support import expected_conditions as ec


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
        print(url)
        data = {
            'link': [],
            'name': [],
            'instagram': []
            # 'website': []
        }
        status_code = None
        trial = 0
        while (trial < 5 and status_code == None):
            try:
                driver = webdriver_setup(proxies=selected_proxy)
                driver.delete_all_cookies()
                driver.fullscreen_window()
                driver.get(url)
                WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.CSS_SELECTOR,name_locator)))
                status_code = ec.presence_of_element_located((By.CSS_SELECTOR,name_locator))
                print(status_code)
            except Exception as e:
                print(e)
                selected_proxy = random.choice(selected_proxies)
                print(f"Change proxy to {selected_proxy}")
                trial += 1

        print(f'got response {status_code}')

        if trial < 5:
            data['link'] = driver.current_url
            data['name'] = driver.find_element(By.CSS_SELECTOR, name_locator).text
            try:
                profile_url = f"{url_schema}{driver.find_element(profile_locator).get_attribute('href')}"
                print(profile_url)
                data['instagram'] = get_instagram(url=profile_url, selected_proxy=selected_proxy)
            except Exception as e:
                print(e)
                data['instagram'] = None

            # data['website'] = soup.select_one(website_locator)

            datas.append(data.copy())

        else:
            print('proxy error')
            continue

    return datas

def webdriver_setup(proxies = None):
    ip, port = proxies.split(sep=':')
    useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0'
    firefox_options = Options()

    firefox_options.headless = True
    firefox_options.add_argument('--no-sandbox')

    firefox_options.set_preference("general.useragent.override", useragent)
    firefox_options.set_preference('network.proxy.type', 1)
    firefox_options.set_preference('network.proxy.socks', ip)
    firefox_options.set_preference('network.proxy.socks_port', int(port))
    firefox_options.set_preference('network.proxy.socks_version', 4)
    firefox_options.set_preference('network.proxy.socks_remote_dns', True)
    firefox_options.set_preference('network.proxy.http', ip)
    firefox_options.set_preference('network.proxy.http_port', int(port))
    firefox_options.set_preference('network.proxy.ssl', ip)
    firefox_options.set_preference('network.proxy.ssl_port', int(port))

    firefox_options.set_capability("acceptSslCerts", True)
    firefox_options.set_capability("acceptInsecureCerts", True)
    firefox_options.set_capability("ignore-certificate-errors", False)

    driver = webdriver.Firefox(options=firefox_options)
    return driver

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
    # proxies = get_proxy()
    # selected_proxies = choose_proxy(proxies)
    selected_proxies = ['8.219.97.248:80','20.210.26.214:3128','168.138.33.70:8080', '203.154.91.28:8080','45.91.133.137:8080', '109.207.76.37:8080', '66.42.53.233:8000', '178.33.198.181:3128']
    # detail_urls = get_detail_url(url, selected_proxies=selected_proxies)
    # print(detail_urls)
    detail_urls = ['https://www.airbnb.com//rooms/45249678?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000']
    datas = get_datas(detail_urls, selected_proxies=selected_proxies)
    to_csv(datas, save_path)
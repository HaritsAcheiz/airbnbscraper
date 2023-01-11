# Import required package
import csv
import os
import random
import time

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


# Scrape free proxy from free proxy list dot net
def get_proxy():
    print("Collecting proxies...")
    with requests.Session() as s:
        response = s.get('https://free-proxy-list.net/')
    s.close()
    soup = BeautifulSoup(response.text, 'html.parser')
    list_data = soup.select('table.table.table-striped.table-bordered>tbody>tr')
    scraped_proxies = []
    blocked_cc = ['IR', 'RU']
    for i in list_data:
        ip = i.select_one('tr > td:nth-child(1)').text
        port = i.select_one('tr > td:nth-child(2)').text
        cc = i.select_one('tr > td:nth-child(3)').text
        if cc in blocked_cc:
            continue
        else:
            scraped_proxies.append(f'{ip}:{port}')
    print(f"{len(scraped_proxies)} proxies collected")
    return scraped_proxies


# Choose working proxy from scraped proxy
def choose_proxy(scraped_proxies):
    working_proxies = []
    for i, item in enumerate(scraped_proxies):
        if i < len(scraped_proxies) and len(working_proxies) < 3:
            formated_proxy = {
                "http": f"http://{item}",
                "https": f"http://{item}"
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
            }
            print(f'checking {formated_proxy}')
            try:
                with requests.Session() as session:
                    response = session.get(url='https://www.airbnb.com', proxies=formated_proxy, headers=headers,
                                           timeout=(15,27))
                if response.status_code == 200:
                    working_proxies.append(item)
                    print(f'{item} selected')
                else:
                    print(f"not working with status code: {response.status_code}")
                response.close()
            except Exception as e:
                print(f"not working with {e}")
                pass
        else:
            break
    return working_proxies


def get_detail_url(url, working_proxies):
    print('Collecting url...')
    parsed_url = url.split('/')
    url_schema = f"{parsed_url[0]}/{parsed_url[1]}/{parsed_url[2]}"
    detail_url_locators = "div.gh7uyir.giajdwt.g14v8520.dir.dir-ltr > div"
    next_page_locator = "a._1bfat5l"
    selected_proxy = random.choice(working_proxies)
    page = 1
    next_page_url = url
    detail_urls = list()
    end = False
    while end == False:
        if page % 10 == 0:
            selected_proxy = random.choice(working_proxies)
        else:
            pass
        trial = 0
        while trial < 8:
            try:
                session = requests.Session()
                formated_proxy = {
                    "http": f"http://{selected_proxy}",
                    "https": f"http://{selected_proxy}"
                }
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
                    }
                response = session.get(next_page_url, proxies=formated_proxy, headers=headers, timeout=(15, 27))
                break
            except (ProxyError, ConnectTimeout, ReadTimeoutError, ReadTimeout, ConnectionError, ConnectionError) as e:
                print(e)
                selected_proxy = random.choice(working_proxies)
                print(f"Change proxy to {selected_proxy}")
                trial += 1

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            response.close()
            next_page_url_href = soup.select_one(next_page_locator)['href']
            next_page_url = f"{url_schema}{next_page_url_href}"
            print(next_page_url)
            html_detail_urls = soup.select(detail_url_locators)
            url_locator = "a.bn2bl2p.dir.dir-ltr"
            for i in html_detail_urls:
                try:
                    detail_urls.append(f"{url_schema}/{i.select_one(url_locator)['href']}")
                except TypeError as e:
                    print(f'url locator get {e}')
                    break
            print(f"{len(detail_urls)} url collected from {str(page)} page")
            page += 1
        except TypeError as e:
            print(e)
            print('reach end of page')
            end = True
            break

    return detail_urls

def get_datas(urls, selected_proxies):
    print('Collecting datas...')
    datas = list()
    name_locator = 'h1._fecoyn4'
    # profile_locator = 'div.h1144bf3.dir.dir-ltr > div > a'
    profile_locator = '/html/body/div[5]/div/div/div[1]/div/div[1]/div/div/div/div[1]/main/div/div[1]/div[6]/div/div/div/div[2]/div/section/div[1]/div[1]/div/a'
    ## job_locator = 'div._o7dyhr>section>div:nth-child(4)>section>div:nth-child(2)>div:nth-child(1)>span._1ax9t0a'
    job_locator = '/html/body/div[5]/div/div/div[1]/div/div[1]/div[1]/main/div/div/div/div[2]/div/section/div[4]/section/div[2]/div[3]/span[2]'
    close_modal_locator = 'div._1piuevz > button.czcfm7x.dir.dir-ltr'
    selected_proxy = random.choice(selected_proxies)
    for counter, url in enumerate(urls):
        if counter % 10 == 0:
            selected_proxy = random.choice(selected_proxies)
            print(f"Change proxy to {selected_proxy}")
        else:
            pass
        print(url)
        data = {
            'link': [],
            'name': [],
            'instagram': []
        }
        status_code = None
        trial = 0
        while (trial < 5 and status_code == None):
            try:
                driver = webdriver_setup(proxies=selected_proxy)
                driver.delete_all_cookies()
                driver.fullscreen_window()
                driver.set_page_load_timeout(30)
                driver.get(url)
                status_code = ec.presence_of_element_located((By.CSS_SELECTOR, close_modal_locator))
            except Exception as e:
                driver.quit()
                selected_proxy = random.choice(selected_proxies)
                print(f"Change proxy to {selected_proxy}")
                trial += 1

        if trial < 5:
            try:
                WebDriverWait(driver,20).until(ec.presence_of_element_located((By.CSS_SELECTOR, close_modal_locator)))
                driver.find_element(By.CSS_SELECTOR, close_modal_locator).click()
            except Exception as e:
                print(f"modal translation is not visible")
                pass

            try:
                data['link'] = driver.current_url
                data['name'] = driver.find_element(By.CSS_SELECTOR, name_locator).text
                WebDriverWait(driver, 20).until(ec.element_to_be_clickable((By.XPATH, profile_locator)))
                driver.find_element(By.XPATH, profile_locator).click()
                time.sleep(20)
                tab1 = driver.window_handles[0]
                tab2 = driver.window_handles[1]
                driver.switch_to.window(tab2)
                print(driver.current_url)
                WebDriverWait(driver, 20).until(ec.presence_of_element_located((By.XPATH, job_locator)))
                data['instagram'] = f"https://www.instagram.com/{driver.find_element(By.XPATH, job_locator).text.split('@')[-1].split()[0]}/"
                print(data['instagram'])
            except Exception as e:
                print(f'cannot find instagram link')
                print(e)
                data['instagram'] = None
            driver.quit()
            datas.append(data.copy())

        else:
            print('proxy error')
            continue
        print(f'{len(datas)} datas are collected')

    return datas

def webdriver_setup(proxies = None):
    ip, port = proxies.split(sep=':')
    useragent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0'
    firefox_options = Options()

    firefox_options.headless = True
    firefox_options.add_argument('--no-sandbox')

    firefox_options.set_preference("intl.accept_languages", "en-GB")
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
    url = "https://www.airbnb.com/s/Belgium/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&flexible_trip_lengths%5B%5D=one_week&price_filter_input_type=0&price_filter_num_nights=1&query=Belgium&place_id=ChIJl5fz7WR9wUcR8g_mObTy60c&date_picker_type=calendar&checkin=2023-01-07&checkout=2023-01-08&adults=1&source=structured_search_input_header&search_type=autocomplete_click&federated_search_session_id=dc608cc7-e1d4-4363-9d73-4b7da1ff6d05&pagination_search=true&cursor=eyJzZWN0aW9uX29mZnNldCI6MiwiaXRlbXNfb2Zmc2V0IjoyODgsInZlcnNpb24iOjF9"
    save_path = "C:/NaruProject/airbnbscraper/result.csv"
    # scraped_proxies = get_proxy()
    # working_proxies = choose_proxy(scraped_proxies)
    # print(working_proxies)
    working_proxies = ['154.236.179.226:1981', '103.156.15.18:8080', '182.253.183.67:80']
    detail_urls = get_detail_url(url, working_proxies=working_proxies)
    # print(detail_urls)
    # detail_urls = [
        # 'https://www.airbnb.com//rooms/41953733?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000',
        # 'https://www.airbnb.com//rooms/19157408?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000',
        # 'https://www.airbnb.com//rooms/45249678?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000',
        # 'https://www.airbnb.com//rooms/670806019201784094?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000',
        # 'https://www.airbnb.com//rooms/648208678396952595?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000',
        # 'https://www.airbnb.com//rooms/50257276?adults=1&check_in=2023-01-29&check_out=2023-01-30&previous_page_section_name=1000']
    datas = get_datas(detail_urls, selected_proxies=working_proxies)
    to_csv(datas, save_path)
# Import required package
import concurrent.futures.thread
import csv
import os
import random
import time
import re
from itertools import repeat

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
        if i < len(scraped_proxies) and len(working_proxies) < 5:
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
                                           timeout=(7,10), allow_redirects=False)
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

def cek_proxy(scraped_proxy):
    print(f'checking {scraped_proxy}...')
    formated_proxy = {
        "http": f"http://{scraped_proxy}",
        "https": f"http://{scraped_proxy}"
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
    }
    try:
        with requests.Session() as session:
            response = session.get(url='https://www.airbnb.com', proxies=formated_proxy, headers=headers,
                                   timeout=(7, 10), allow_redirects=False)
        if response.status_code == 200:
            print(f'{scraped_proxy} selected')
            result = scraped_proxy
        else:
            print(f"not working with status code: {response.status_code}")
            result =  'Not Working'
        response.close()
    except Exception as e:
        print(f"not working with {e}")
        result = 'Not Working'
    return result

def get_detail_urls(url, working_proxies):
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
                response = session.get(next_page_url, proxies=formated_proxy, headers=headers, timeout=(7, 27), allow_redirects=False)
                break
            except (ProxyError, ConnectTimeout, ReadTimeoutError, ReadTimeout, ConnectionError, ConnectionError) as e:
                print(e)
                selected_proxy = random.choice(working_proxies)
                print(f"Change proxy to {selected_proxy}")
                trial += 1

        if trial < 8:
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
                print('reach end of page')
                end = True
                break
        else:
            print('Proxy Connection Error')
            page += 1
            continue

    return detail_urls

def get_datas(urls, selected_proxies):
    print('Collecting datas...')
    datas = list()

    name_locator = 'h1._fecoyn4'
    price_locator = '/html/body/div[5]/div/div/div[1]/div/div[1]/div/div/div/div[1]/main/div/div[1]/div[3]/div/div[2]/div/div/div[1]/div/div/div/div/div/div/div[1]/div[1]/div[1]/div/span/div/span[1]'
    disc_price_locator = '/html/body/div[5]/div/div/div[1]/div/div[1]/div/div/div/div[1]/main/div/div[1]/div[3]/div/div[2]/div/div/div[1]/div/div/div/div/div/div/div[1]/div[1]/div[1]/div/span/div/span[2]'
    profile_locator = '/html/body/div[5]/div/div/div[1]/div/div[1]/div/div/div/div[1]/main/div/div[1]/div[6]/div/div/div/div[2]/div/section/div[1]/div[1]/div/a'
    job_locator = '/html/body/div[5]/div/div/div[1]/div/div[1]/div[1]/main/div/div/div/div[2]/div/section/div[4]/section/div[2]/div[3]/span[2]'
    close_modal_locator = 'div._1piuevz>button.czcfm7x.dir.dir-ltr'
    review_locator = '//div[@id="review-section-title"]'

    selected_proxy = random.choice(selected_proxies)
    for counter, url in enumerate(urls[0:10]):
        if counter % 10 == 0:
            selected_proxy = random.choice(selected_proxies)
            print(f"Change proxy to {selected_proxy}")
        else:
            pass
        print(url)
        data = {
            'link': None,
            'name': None,
            'instagram': None,
            'price': None,
            'review': None
        }
        trial = 0
        while trial < 5:
            try:
                driver = webdriver_setup(proxies=selected_proxy)
                driver.delete_all_cookies()
                driver.fullscreen_window()
                wait = WebDriverWait(driver, 15)
                driver.set_page_load_timeout(20)
                driver.get(url)
                try:
                    wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, close_modal_locator)))
                    driver.find_element(By.CSS_SELECTOR, close_modal_locator).click()
                except Exception as e:
                    print(f"modal translation is not visible {e}")

                wait.until(ec.element_to_be_clickable((By.XPATH, profile_locator)))
                data['link'] = driver.current_url
                data['name'] = driver.find_element(By.CSS_SELECTOR, name_locator).text
                price = re.findall(r'\b\d+\b', driver.find_element(By.XPATH, disc_price_locator).text)

                if len(price) > 0:
                    data['price'] = int(price[0])
                else:
                    print('no discount')
                    price = re.findall(r'\b\d+\b', driver.find_element(By.XPATH, price_locator).text)
                    data['price'] = int(price[0])

                driver.find_element(By.XPATH, profile_locator).click()
                tab1 = driver.window_handles[0]
                tab2 = driver.window_handles[1]
                driver.switch_to.window(tab2)
                wait.until(ec.presence_of_element_located((By.XPATH, review_locator)))
                print(driver.current_url)
                try:
                    data['instagram'] = f"https://www.instagram.com/{driver.find_element(By.XPATH, job_locator).text.split('@')[-1].split()[0]}/"
                    print(data['instagram'])
                except Exception as e:
                    print(f'instagram not found {e}')
                    data['instagram'] = None
                try:
                    review = re.findall(r'\b\d+\b', driver.find_element(By.XPATH, review_locator).text)
                    print(len(review))
                    if len(review) > 0:
                        data['review'] = int(review[0])
                    else:
                        print('no review')
                        data['review'] = 0
                except Exception as e:
                    print(f'no review {e}')
                    data['review'] = 0

                driver.quit()
                datas.append(data.copy())
                break

            except Exception as e:
                print(e)
                driver.quit()
                selected_proxy = random.choice(selected_proxies)
                print(f"Change proxy to {selected_proxy}")
                trial += 1

        if trial < 5:
            print(f'{len(datas)} datas are collected')
        else:
            print('Connection Error')

    return datas

def get_datas_2(url, selected_proxies):
    print('Collecting datas...')

    name_locator = 'h1._fecoyn4'
    price_locator = '/html/body/div[5]/div/div/div[1]/div/div[1]/div/div/div/div[1]/main/div/div[1]/div[3]/div/div[2]/div/div/div[1]/div/div/div/div/div/div/div[1]/div[1]/div[1]/div/span/div/span[1]'
    disc_price_locator = '/html/body/div[5]/div/div/div[1]/div/div[1]/div/div/div/div[1]/main/div/div[1]/div[3]/div/div[2]/div/div/div[1]/div/div/div/div/div/div/div[1]/div[1]/div[1]/div/span/div/span[2]'
    profile_locator = '/html/body/div[5]/div/div/div[1]/div/div[1]/div/div/div/div[1]/main/div/div[1]/div[6]/div/div/div/div[2]/div/section/div[1]/div[1]/div/a'
    job_locator = '/html/body/div[5]/div/div/div[1]/div/div[1]/div[1]/main/div/div/div/div[2]/div/section/div[4]/section/div[2]/div[3]/span[2]'
    close_modal_locator = 'div._1piuevz>button.czcfm7x.dir.dir-ltr'
    review_locator = '//div[@id="review-section-title"]'

    selected_proxy = random.choice(selected_proxies)

    data = {
        'link': None,
        'name': None,
        'instagram': None,
        'price': None,
        'review': None
    }
    trial = 0
    while trial < 5:
        try:
            driver = webdriver_setup(proxies=selected_proxy)
            driver.delete_all_cookies()
            driver.fullscreen_window()
            wait = WebDriverWait(driver, 180)
            driver.set_page_load_timeout(250)
            driver.get(url)
            try:
                wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, close_modal_locator)))
                driver.find_element(By.CSS_SELECTOR, close_modal_locator).click()
            except Exception as e:
                print(f"modal translation is not visible {e}")

            wait.until(ec.element_to_be_clickable((By.XPATH, profile_locator)))
            data['link'] = driver.current_url
            data['name'] = driver.find_element(By.CSS_SELECTOR, name_locator).text
            price = re.findall(r'\b\d+\b', driver.find_element(By.XPATH, disc_price_locator).text)

            if len(price) > 0:
                data['price'] = int(price[0])
            else:
                print('no discount')
                price = re.findall(r'\b\d+\b', driver.find_element(By.XPATH, price_locator).text)
                data['price'] = int(price[0])

            driver.find_element(By.XPATH, profile_locator).click()
            tab1 = driver.window_handles[0]
            tab2 = driver.window_handles[1]
            driver.switch_to.window(tab2)
            wait.until(ec.presence_of_element_located((By.XPATH, review_locator)))
            print(driver.current_url)
            try:
                data['instagram'] = f"https://www.instagram.com/{driver.find_element(By.XPATH, job_locator).text.split('@')[-1].split()[0]}/"
                print(data['instagram'])
            except Exception as e:
                print(f'instagram not found {e}')
                data['instagram'] = None
            try:
                review = re.findall(r'\b\d+\b', driver.find_element(By.XPATH, review_locator).text)
                if len(review) > 0:
                    data['review'] = int(review[0])
                else:
                    print('no review')
                    data['review'] = 0
            except Exception as e:
                print(f'no review {e}')
                data['review'] = 0

            driver.quit()
            break

        except Exception as e:
            print(e)
            driver.quit()
            selected_proxy = random.choice(selected_proxies)
            print(f"Change proxy to {selected_proxy}")
            trial += 1

    if trial < 5:
        print(f'Data collected')
    else:
        print('Connection error')

    return data

def webdriver_setup(proxies = None):
    ip, port = proxies.split(sep=':')
    useragent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0'
    firefox_options = Options()

    # setup browser mode
    firefox_options.headless = True
    firefox_options.add_argument('--no-sandbox')

    # setup language and user-agent
    firefox_options.set_preference("intl.accept_languages", "en-GB")
    firefox_options.set_preference("general.useragent.override", useragent)

    # setup proxy
    firefox_options.set_preference('network.proxy.type', 1)
    firefox_options.set_preference('network.proxy.socks', ip)
    firefox_options.set_preference('network.proxy.socks_port', int(port))
    firefox_options.set_preference('network.proxy.socks_version', 4)
    firefox_options.set_preference('network.proxy.socks_remote_dns', True)
    firefox_options.set_preference('network.proxy.http', ip)
    firefox_options.set_preference('network.proxy.http_port', int(port))
    firefox_options.set_preference('network.proxy.ssl', ip)
    firefox_options.set_preference('network.proxy.ssl_port', int(port))

    # setup geo location
    # firefox_options.set_preference('geo.prompt.testing', True)
    # firefox_options.set_preference('geo.prompt.testing.allow', True)
    # firefox_options.set_preference('geo.provider.network.url',
    #                          'data:application/json,{"location": {"lat": 51.47, "lng": 0.0}, "accuracy": 100.0}')

    # setup ssl certificate
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
        headers = ['link', 'name', 'instagram', 'price', 'review']
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for i in datas:
            writer.writerow(i)
        f.close()
    print(f'{filepath} created')

if __name__ == '__main__':
    url = "https://www.airbnb.com/s/Belgium/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&flexible_trip_lengths%5B%5D=one_week&price_filter_input_type=0&price_filter_num_nights=1&query=Belgium&place_id=ChIJl5fz7WR9wUcR8g_mObTy60c&date_picker_type=calendar&checkin=2023-01-07&checkout=2023-01-08&adults=1&source=structured_search_input_header&search_type=autocomplete_click&federated_search_session_id=dc608cc7-e1d4-4363-9d73-4b7da1ff6d05&pagination_search=true&cursor=eyJzZWN0aW9uX29mZnNldCI6MiwiaXRlbXNfb2Zmc2V0IjoyODgsInZlcnNpb24iOjF9"
    save_path = "C:/NaruProject/airbnbscraper/result.csv"

    # without multithreading
    # scraped_proxies = get_proxy()
    # working_proxies = choose_proxy(scraped_proxies)
    # print(working_proxies)
    # # working_proxies = ['35.184.247.96:80', '14.177.234.252:8080', '115.144.109.179:10000', '193.123.98.126:8080', '138.117.229.208:999']
    # detail_urls = get_detail_urls(url, working_proxies=working_proxies)
    # # print(detail_urls)
    # # detail_urls = ['https://www.airbnb.com//rooms/36473296?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/53641703?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43264089?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/53617070?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/29619942?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/34683708?adults=1&children=0&infants=0&pets=0&check_in=2023-02-03&check_out=2023-02-08&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/686012375955193499?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43574791?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/722540128797545418?adults=1&children=0&infants=0&pets=0&check_in=2023-11-01&check_out=2023-11-08&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/16839818?adults=1&children=0&infants=0&pets=0&check_in=2023-02-24&check_out=2023-03-01&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/600352600119488042?adults=1&children=0&infants=0&pets=0&check_in=2023-02-15&check_out=2023-02-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/694200148486705447?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-23&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/38649945?adults=1&children=0&infants=0&pets=0&check_in=2023-02-04&check_out=2023-02-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/561350603097409643?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52727569?adults=1&children=0&infants=0&pets=0&check_in=2023-02-02&check_out=2023-02-09&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/561620272984687183?adults=1&children=0&infants=0&pets=0&check_in=2023-01-19&check_out=2023-01-24&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/589074445257405853?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/45213074?adults=1&children=0&infants=0&pets=0&check_in=2023-01-20&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/786960216859874837?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/51496210?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/666363082285199382?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/612196126355080278?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/773118921716241392?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/47248319?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/33907970?adults=1&children=0&infants=0&pets=0&check_in=2023-01-20&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/802637407968593416?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/48657959?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/31976913?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/20856073?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-04&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43672798?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/12349210?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/791744313492866759?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52670098?adults=1&children=0&infants=0&pets=0&check_in=2023-02-07&check_out=2023-02-13&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/564424064722836839?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/37584149?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/555632483431529555?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/555632483431529555?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43814920?adults=1&children=0&infants=0&pets=0&check_in=2023-02-13&check_out=2023-02-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52342377?adults=1&children=0&infants=0&pets=0&check_in=2023-01-28&check_out=2023-02-03&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52363949?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/37584149?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/678937378254782795?adults=1&children=0&infants=0&pets=0&check_in=2023-09-01&check_out=2023-09-07&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/28374792?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/741703139638818460?adults=1&children=0&infants=0&pets=0&check_in=2023-01-26&check_out=2023-02-02&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/53888064?adults=1&children=0&infants=0&pets=0&check_in=2023-09-18&check_out=2023-09-25&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/786970231534031985?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/48686587?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/21853899?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/24112105?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/39812999?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/737374858667519765?adults=1&children=0&infants=0&pets=0&check_in=2023-02-06&check_out=2023-02-11&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/651434509480567820?adults=1&children=0&infants=0&pets=0&check_in=2023-02-04&check_out=2023-02-09&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/49604139?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/49133684?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/37027776?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52973208?adults=1&children=0&infants=0&pets=0&check_in=2023-01-21&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/51774073?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/555700153795504858?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/50937848?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/37768869?adults=1&children=0&infants=0&pets=0&check_in=2023-12-01&check_out=2023-12-06&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/46048765?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-28&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/32509871?adults=1&children=0&infants=0&pets=0&check_in=2023-03-02&check_out=2023-03-08&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/802810302858425251?adults=1&children=0&infants=0&pets=0&check_in=2023-01-31&check_out=2023-02-06&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/30700216?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/37237249?adults=1&children=0&infants=0&pets=0&check_in=2023-01-20&check_out=2023-01-25&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/669560724544886830?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/36908027?adults=1&children=0&infants=0&pets=0&check_in=2023-03-20&check_out=2023-03-25&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/37701024?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/45130857?adults=1&children=0&infants=0&pets=0&check_in=2023-01-25&check_out=2023-02-01&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/556370619614335737?adults=1&children=0&infants=0&pets=0&check_in=2023-06-26&check_out=2023-07-01&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/612880742297500158?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43795657?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/19404147?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/643917634539054270?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/622883760429512991?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/46784342?adults=1&children=0&infants=0&pets=0&check_in=2023-01-17&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/45636126?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/30152054?adults=1&children=0&infants=0&pets=0&check_in=2023-02-07&check_out=2023-02-12&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/14371260?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/53109666?adults=1&children=0&infants=0&pets=0&check_in=2023-03-12&check_out=2023-03-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/29005858?adults=1&children=0&infants=0&pets=0&check_in=2023-06-22&check_out=2023-06-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/49335769?adults=1&children=0&infants=0&pets=0&check_in=2023-03-05&check_out=2023-03-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/49627651?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52512859?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/731499385976629530?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/47868254?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43994436?adults=1&children=0&infants=0&pets=0&check_in=2023-12-25&check_out=2023-12-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/40520223?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/50757650?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/670980771120687394?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-23&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/50757650?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/670980771120687394?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-23&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/625775081594425165?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/51134026?adults=1&children=0&infants=0&pets=0&check_in=2023-03-02&check_out=2023-03-07&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/718744717609522584?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/48137229?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/10845191?adults=1&children=0&infants=0&pets=0&check_in=2023-03-02&check_out=2023-03-07&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/555584093029808791?adults=1&children=0&infants=0&pets=0&check_in=2023-01-17&check_out=2023-01-24&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/556403144075739762?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/44469927?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/53628179?adults=1&children=0&infants=0&pets=0&check_in=2023-02-28&check_out=2023-03-05&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/46549617?adults=1&children=0&infants=0&pets=0&check_in=2023-01-25&check_out=2023-01-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/45754546?adults=1&children=0&infants=0&pets=0&check_in=2023-02-06&check_out=2023-02-13&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/733987897564897984?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/39556662?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/599697415260342058?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/799985627649322165?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-28&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/41953733?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/30080363?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/37773248?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/667089215393425719?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/36437683?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/734667707057877756?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/44486051?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/675372115266201939?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/48669044?adults=1&children=0&infants=0&pets=0&check_in=2023-02-22&check_out=2023-02-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/723271304055081071?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/51116786?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52233878?adults=1&children=0&infants=0&pets=0&check_in=2023-03-12&check_out=2023-03-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/45056309?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-23&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/21571129?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/6788954?adults=1&children=0&infants=0&pets=0&check_in=2023-05-16&check_out=2023-05-23&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/42735877?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/654524439731515169?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/50952403?adults=1&children=0&infants=0&pets=0&check_in=2023-01-25&check_out=2023-01-31&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/42321414?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/42321414?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/48806789?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/53002967?adults=1&children=0&infants=0&pets=0&check_in=2023-03-05&check_out=2023-03-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52922148?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/783166408670360526?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/620217090290949354?adults=1&children=0&infants=0&pets=0&check_in=2023-01-21&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/544146284105911280?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/48157379?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/51545932?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/19320012?adults=1&children=0&infants=0&pets=0&check_in=2023-03-31&check_out=2023-04-05&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/619245723820096877?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/762953820839187460?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/790684385153906110?adults=1&children=0&infants=0&pets=0&check_in=2023-02-01&check_out=2023-02-06&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/12820524?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/44622699?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/24958521?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52645856?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/702723013903191015?adults=1&children=0&infants=0&pets=0&check_in=2023-01-24&check_out=2023-01-29&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/755475912277584573?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/44165333?adults=1&children=0&infants=0&pets=0&check_in=2023-02-08&check_out=2023-02-14&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/749648911863699961?adults=1&children=0&infants=0&pets=0&check_in=2023-07-01&check_out=2023-07-07&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/40652747?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/54206350?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-28&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/10563051?adults=1&children=0&infants=0&pets=0&check_in=2023-04-16&check_out=2023-04-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/51596918?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/670806019201784094?adults=1&children=0&infants=0&pets=0&check_in=2023-02-26&check_out=2023-03-03&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/6545997?adults=1&children=0&infants=0&pets=0&check_in=2023-02-02&check_out=2023-02-08&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/28041044?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/742629153217315853?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/614982397366037662?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/42320793?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/44400305?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-29&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/36623791?adults=1&children=0&infants=0&pets=0&check_in=2023-02-14&check_out=2023-02-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/50762484?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/50664912?adults=1&children=0&infants=0&pets=0&check_in=2023-02-20&check_out=2023-02-25&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/599699502795231227?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/54224122?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/36437683?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43889305?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-28&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/53641703?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/28277705?adults=1&children=0&infants=0&pets=0&check_in=2023-03-05&check_out=2023-03-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/22364339?adults=1&children=0&infants=0&pets=0&check_in=2023-01-17&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/53617070?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/44622699?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/623632030831415322?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/37584149?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/12820524?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/42828138?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-23&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/44486051?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/780184322390694928?adults=1&children=0&infants=0&pets=0&check_in=2023-01-21&check_out=2023-01-26&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/561350603097409643?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43574791?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/16132937?adults=1&children=0&infants=0&pets=0&check_in=2023-11-16&check_out=2023-11-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/13729878?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-28&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/16132937?adults=1&children=0&infants=0&pets=0&check_in=2023-11-16&check_out=2023-11-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/13729878?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-28&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/19781331?adults=1&children=0&infants=0&pets=0&check_in=2023-06-19&check_out=2023-06-24&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/45682824?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/30080363?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43264089?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/555632483431529555?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43994436?adults=1&children=0&infants=0&pets=0&check_in=2023-12-25&check_out=2023-12-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/802021977482508406?adults=1&children=0&infants=0&pets=0&check_in=2023-01-21&check_out=2023-01-28&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/46087502?adults=1&children=0&infants=0&pets=0&check_in=2023-06-08&check_out=2023-06-13&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/50276168?adults=1&children=0&infants=0&pets=0&check_in=2023-01-24&check_out=2023-01-29&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/1018048?adults=1&children=0&infants=0&pets=0&check_in=2023-06-27&check_out=2023-07-02&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/794623796837107792?adults=1&children=0&infants=0&pets=0&check_in=2023-01-20&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/22399853?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/44035109?adults=1&children=0&infants=0&pets=0&check_in=2023-03-05&check_out=2023-03-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/686012375955193499?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/21497507?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/46188316?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/19277929?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-28&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/51530480?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/16967210?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-11&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/566696907908086879?adults=1&children=0&infants=0&pets=0&check_in=2023-01-30&check_out=2023-02-04&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/622964892110901459?adults=1&children=0&infants=0&pets=0&check_in=2023-02-22&check_out=2023-02-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/629676088297344470?adults=1&children=0&infants=0&pets=0&check_in=2023-05-02&check_out=2023-05-07&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/8384927?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/37104895?adults=1&children=0&infants=0&pets=0&check_in=2023-03-26&check_out=2023-03-31&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/54252755?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/28779013?adults=1&children=0&infants=0&pets=0&check_in=2023-01-31&check_out=2023-02-07&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52272212?adults=1&children=0&infants=0&pets=0&check_in=2023-01-31&check_out=2023-02-05&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/798457669497623793?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/45401481?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/553594269017890273?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/616457445053759701?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/44400305?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-29&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/38530?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/722540128797545418?adults=1&children=0&infants=0&pets=0&check_in=2023-11-01&check_out=2023-11-08&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/45693176?adults=1&children=0&infants=0&pets=0&check_in=2023-01-31&check_out=2023-02-07&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/50768533?adults=1&children=0&infants=0&pets=0&check_in=2023-02-13&check_out=2023-02-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/49271757?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/27720151?adults=1&children=0&infants=0&pets=0&check_in=2023-01-30&check_out=2023-02-04&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/29138832?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43795657?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/53180182?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-12&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/51686892?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/561620272984687183?adults=1&children=0&infants=0&pets=0&check_in=2023-01-19&check_out=2023-01-24&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/510929?adults=1&children=0&infants=0&pets=0&check_in=2023-02-20&check_out=2023-02-25&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52772752?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52440497?adults=1&children=0&infants=0&pets=0&check_in=2023-01-25&check_out=2023-02-01&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/28277491?adults=1&children=0&infants=0&pets=0&check_in=2023-01-20&check_out=2023-01-25&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/16566743?adults=1&children=0&infants=0&pets=0&check_in=2023-01-30&check_out=2023-02-04&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/37933276?adults=1&children=0&infants=0&pets=0&check_in=2023-09-01&check_out=2023-09-06&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/48330899?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/37027776?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/36826834?adults=1&children=0&infants=0&pets=0&check_in=2023-06-23&check_out=2023-06-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/11160077?adults=1&children=0&infants=0&pets=0&check_in=2023-01-19&check_out=2023-01-24&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/704966189619395427?adults=1&children=0&infants=0&pets=0&check_in=2023-03-11&check_out=2023-03-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/48416471?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/34039735?adults=1&children=0&infants=0&pets=0&check_in=2023-02-10&check_out=2023-02-15&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/733987897564897984?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/600352600119488042?adults=1&children=0&infants=0&pets=0&check_in=2023-02-15&check_out=2023-02-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/754989397377031581?adults=1&children=0&infants=0&pets=0&check_in=2023-01-17&check_out=2023-01-24&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/645302417646443822?adults=1&children=0&infants=0&pets=0&check_in=2023-02-10&check_out=2023-02-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/21131832?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/46869040?adults=1&children=0&infants=0&pets=0&check_in=2023-02-04&check_out=2023-02-09&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/26442003?adults=1&children=0&infants=0&pets=0&check_in=2023-03-16&check_out=2023-03-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/749648911863699961?adults=1&children=0&infants=0&pets=0&check_in=2023-07-01&check_out=2023-07-07&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/23665678?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-12&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/34683708?adults=1&children=0&infants=0&pets=0&check_in=2023-02-03&check_out=2023-02-08&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/18428858?adults=1&children=0&infants=0&pets=0&check_in=2023-02-01&check_out=2023-02-08&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/18750916?adults=1&children=0&infants=0&pets=0&check_in=2023-02-13&check_out=2023-02-19&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/645459718750771967?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/784539966739738163?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000']
    # start_time = time.time()
    # datas = get_datas(detail_urls, selected_proxies=working_proxies)
    # print('processing time: %.2f seconds' % (time.time() - start_time))
    # to_csv(datas, save_path)

    # with multithreading

    # cek proxy
    start_time = time.time()
    scraped_proxies = get_proxy()
    # working_proxies = list()
    # with concurrent.futures.thread.ThreadPoolExecutor() as executor:
    #     working_proxies = list(filter(lambda x: x != 'Not Working', executor.map(cek_proxy, scraped_proxies)))
    #
    # print(working_proxies)
    working_proxies = ['185.217.137.241:1337', '213.230.107.235:8080', '51.154.79.204:80', '129.213.115.0:8088', '45.8.179.241:1337', '82.66.18.27:8080', '178.248.60.103:80', '158.101.197.81:3128']
    # print(f'got {len(working_proxies)} working proxy(s)')
    print('check proxy processing time: %.2f second(s)' % (time.time() - start_time))

    # get detail urls
    start_time = time.time()

    # detail_urls = get_detail_urls(url, working_proxies)
    # print(detail_urls)

    detail_urls = [
        'https://www.airbnb.com//rooms/45085010?adults=1&children=0&infants=0&pets=0&check_in=2023-02-26&check_out=2023-03-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/41187001?adults=1&children=0&infants=0&pets=0&check_in=2023-03-12&check_out=2023-03-17&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/42303113?adults=1&children=0&infants=0&pets=0&check_in=2023-01-19&check_out=2023-01-26&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/558544417835722215?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/42986806?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/691904944587171135?adults=1&children=0&infants=0&pets=0&check_in=2023-03-05&check_out=2023-03-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/731499385976629530?adults=1&children=0&infants=0&pets=0&check_in=2023-01-26&check_out=2023-02-02&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/580185003907474705?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-28&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/11939475?adults=1&children=0&infants=0&pets=0&check_in=2023-01-19&check_out=2023-01-26&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/713641514702154143?adults=1&children=0&infants=0&pets=0&check_in=2023-01-21&check_out=2023-01-26&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/633972514136474985?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/25160240?adults=1&children=0&infants=0&pets=0&check_in=2023-02-26&check_out=2023-03-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/572103741139745432?adults=1&children=0&infants=0&pets=0&check_in=2023-01-24&check_out=2023-01-29&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/51596918?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-11&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/673637864074774522?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/611402294237214523?adults=1&children=0&infants=0&pets=0&check_in=2023-03-20&check_out=2023-03-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/42641765?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/28277705?adults=1&children=0&infants=0&pets=0&check_in=2023-03-05&check_out=2023-03-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/52899791?adults=1&children=0&infants=0&pets=0&check_in=2023-03-18&check_out=2023-03-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/791744313492866759?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/46048765?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/773118921716241392?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/36063690?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/32509871?adults=1&children=0&infants=0&pets=0&check_in=2023-03-02&check_out=2023-03-09&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/26442003?adults=1&children=0&infants=0&pets=0&check_in=2023-05-29&check_out=2023-06-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/619245723820096877?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/571668401920099499?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/620217090290949354?adults=1&children=0&infants=0&pets=0&check_in=2023-01-21&check_out=2023-01-28&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/46784342?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-24&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/44827813?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/50757650?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/22364339?adults=1&children=0&infants=0&pets=0&check_in=2023-01-28&check_out=2023-02-04&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/759302343704247881?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/51530480?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/620218739043546518?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/51134026?adults=1&children=0&infants=0&pets=0&check_in=2023-03-02&check_out=2023-03-07&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/48657959?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/22364339?adults=1&children=0&infants=0&pets=0&check_in=2023-01-28&check_out=2023-02-04&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/51530480?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/759302343704247881?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/45692697?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-12&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/42828138?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/43807794?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/51596918?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-11&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/571668401920099499?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/805796839887683673?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-24&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/10733576?adults=1&children=0&infants=0&pets=0&check_in=2023-03-12&check_out=2023-03-17&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/10845191?adults=1&children=0&infants=0&pets=0&check_in=2023-04-20&check_out=2023-04-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/47571956?adults=1&children=0&infants=0&pets=0&check_in=2023-06-30&check_out=2023-07-07&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/750740708278296296?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/45546939?adults=1&children=0&infants=0&pets=0&check_in=2023-03-01&check_out=2023-03-06&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/45747962?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-05&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/44469927?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/566428431722674289?adults=1&children=0&infants=0&pets=0&check_in=2023-05-02&check_out=2023-05-07&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/53473869?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/662149370590077192?adults=1&children=0&infants=0&pets=0&check_in=2023-02-20&check_out=2023-02-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/43243215?adults=1&children=0&infants=0&pets=0&check_in=2023-01-25&check_out=2023-01-30&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/44274690?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-28&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/52899791?adults=1&children=0&infants=0&pets=0&check_in=2023-03-18&check_out=2023-03-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/44031038?adults=1&children=0&infants=0&pets=0&check_in=2023-06-12&check_out=2023-06-19&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/42320793?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/36063690?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/556403144075739762?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/651298281979473745?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/44827813?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/49920591?adults=1&children=0&infants=0&pets=0&check_in=2023-03-05&check_out=2023-03-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/16967210?adults=1&children=0&infants=0&pets=0&check_in=2023-04-14&check_out=2023-04-20&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/790293061826668019?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/43476654?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/45488966?adults=1&children=0&infants=0&pets=0&check_in=2023-01-19&check_out=2023-01-24&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/802021977482508406?adults=1&children=0&infants=0&pets=0&check_in=2023-01-21&check_out=2023-01-28&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/49271757?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/52512859?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/42191068?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/556403144075739762?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/51686892?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-24&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/48669044?adults=1&children=0&infants=0&pets=0&check_in=2023-02-22&check_out=2023-02-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/28144301?adults=1&children=0&infants=0&pets=0&check_in=2023-01-25&check_out=2023-01-30&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/53109666?adults=1&children=0&infants=0&pets=0&check_in=2023-03-12&check_out=2023-03-17&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/738847781625605690?adults=1&children=0&infants=0&pets=0&check_in=2023-04-24&check_out=2023-04-29&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/794623796837107792?adults=1&children=0&infants=0&pets=0&check_in=2023-01-20&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/614982397366037662?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/48806789?adults=1&children=0&infants=0&pets=0&check_in=2023-02-06&check_out=2023-02-11&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/43523807?adults=1&children=0&infants=0&pets=0&check_in=2023-03-19&check_out=2023-03-24&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/36908027?adults=1&children=0&infants=0&pets=0&check_in=2023-03-20&check_out=2023-03-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/28554132?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/788736158654496985?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/48686587?adults=1&children=0&infants=0&pets=0&check_in=2023-02-16&check_out=2023-02-21&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/48137229?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/6585827?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/42863657?adults=1&children=0&infants=0&pets=0&check_in=2023-02-06&check_out=2023-02-13&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/731499385976629530?adults=1&children=0&infants=0&pets=0&check_in=2023-01-26&check_out=2023-02-02&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/36063690?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/39246575?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/14890511?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/670870724333913352?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/683089375448589008?adults=1&children=0&infants=0&pets=0&check_in=2023-08-01&check_out=2023-08-06&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/25911812?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-24&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/52922148?adults=1&children=0&infants=0&pets=0&check_in=2023-01-19&check_out=2023-01-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/685498433816815291?adults=1&children=0&infants=0&pets=0&check_in=2023-03-05&check_out=2023-03-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/17253081?adults=1&children=0&infants=0&pets=0&check_in=2023-02-02&check_out=2023-02-07&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/54090003?adults=1&children=0&infants=0&pets=0&check_in=2023-01-19&check_out=2023-01-24&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/38470295?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/49665188?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/25410569?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-24&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/47306107?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/44454697?adults=1&children=0&infants=0&pets=0&check_in=2023-02-10&check_out=2023-02-16&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/586141223158601994?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/663558036986447712?adults=1&children=0&infants=0&pets=0&check_in=2023-01-21&check_out=2023-01-26&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/802021977482508406?adults=1&children=0&infants=0&pets=0&check_in=2023-01-21&check_out=2023-01-28&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/555584093029808791?adults=1&children=0&infants=0&pets=0&check_in=2023-01-21&check_out=2023-01-26&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/43516799?adults=1&children=0&infants=0&pets=0&check_in=2023-09-17&check_out=2023-09-22&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/52082928?adults=1&children=0&infants=0&pets=0&check_in=2023-05-25&check_out=2023-06-01&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/53515409?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/53180182?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/50276168?adults=1&children=0&infants=0&pets=0&check_in=2023-01-24&check_out=2023-01-29&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/572103741139745432?adults=1&children=0&infants=0&pets=0&check_in=2023-01-24&check_out=2023-01-29&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/607061907166941199?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/52272212?adults=1&children=0&infants=0&pets=0&check_in=2023-01-31&check_out=2023-02-06&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/643917634539054270?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-24&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/20856073?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/47853849?adults=1&children=0&infants=0&pets=0&check_in=2023-03-13&check_out=2023-03-18&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/547187488400579776?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/3932670?adults=1&children=0&infants=0&pets=0&check_in=2023-04-17&check_out=2023-04-22&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/803338335713548033?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-24&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/734667707057877756?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/734667707057877756?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/52363949?adults=1&children=0&infants=0&pets=0&check_in=2023-02-06&check_out=2023-02-11&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/41364971?adults=1&children=0&infants=0&pets=0&check_in=2023-03-05&check_out=2023-03-11&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/44086554?adults=1&children=0&infants=0&pets=0&check_in=2023-03-01&check_out=2023-03-07&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/45488966?adults=1&children=0&infants=0&pets=0&check_in=2023-01-19&check_out=2023-01-24&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/42828138?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/26704399?adults=1&children=0&infants=0&pets=0&check_in=2023-04-08&check_out=2023-04-13&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/40135137?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/567788414508459631?adults=1&children=0&infants=0&pets=0&check_in=2023-01-20&check_out=2023-01-26&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/671898836909946262?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-29&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/44031038?adults=1&children=0&infants=0&pets=0&check_in=2023-06-12&check_out=2023-06-19&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/32806956?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/11258864?adults=1&children=0&infants=0&pets=0&check_in=2023-01-21&check_out=2023-01-26&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/51956443?adults=1&children=0&infants=0&pets=0&check_in=2023-01-26&check_out=2023-02-01&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/38131435?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/12349210?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/50768533?adults=1&children=0&infants=0&pets=0&check_in=2023-02-13&check_out=2023-02-18&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/45588312?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/13289354?adults=1&children=0&infants=0&pets=0&check_in=2023-01-19&check_out=2023-01-24&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/26704399?adults=1&children=0&infants=0&pets=0&check_in=2023-04-08&check_out=2023-04-14&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/670870724333913352?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/50455820?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/44469927?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/556370619614335737?adults=1&children=0&infants=0&pets=0&check_in=2023-08-10&check_out=2023-08-15&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/38719338?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/33907970?adults=1&children=0&infants=0&pets=0&check_in=2023-01-27&check_out=2023-02-01&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/44165333?adults=1&children=0&infants=0&pets=0&check_in=2023-02-08&check_out=2023-02-13&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/716388304158934417?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/721944402264095896?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/10563051?adults=1&children=0&infants=0&pets=0&check_in=2023-05-01&check_out=2023-05-06&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/47015377?adults=1&children=0&infants=0&pets=0&check_in=2023-01-27&check_out=2023-02-01&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/53460122?adults=1&children=0&infants=0&pets=0&check_in=2023-02-25&check_out=2023-03-04&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/51861612?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/670980771120687394?adults=1&children=0&infants=0&pets=0&check_in=2023-01-31&check_out=2023-02-07&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/47791290?adults=1&children=0&infants=0&pets=0&check_in=2023-10-20&check_out=2023-10-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/52900340?adults=1&children=0&infants=0&pets=0&check_in=2023-02-25&check_out=2023-03-02&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/43476654?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/46784342?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-24&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/698975263275419971?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-28&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/33907970?adults=1&children=0&infants=0&pets=0&check_in=2023-01-27&check_out=2023-02-01&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/671016116684973586?adults=1&children=0&infants=0&pets=0&check_in=2023-02-21&check_out=2023-02-26&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/42191068?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/599699502795231227?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/798457669497623793?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/737552837590909483?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/50206309?adults=1&children=0&infants=0&pets=0&check_in=2023-02-20&check_out=2023-02-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/38080630?adults=1&children=0&infants=0&pets=0&check_in=2023-03-19&check_out=2023-03-24&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/733987897564897984?adults=1&children=0&infants=0&pets=0&check_in=2023-01-21&check_out=2023-01-26&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/716434153847043906?adults=1&children=0&infants=0&pets=0&check_in=2023-01-30&check_out=2023-02-04&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/677432783387536095?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/678937378254782795?adults=1&children=0&infants=0&pets=0&check_in=2023-09-01&check_out=2023-09-08&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/53888064?adults=1&children=0&infants=0&pets=0&check_in=2023-09-18&check_out=2023-09-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/35473872?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/48686587?adults=1&children=0&infants=0&pets=0&check_in=2023-02-16&check_out=2023-02-21&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/49665188?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/45213074?adults=1&children=0&infants=0&pets=0&check_in=2023-03-03&check_out=2023-03-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/17152504?adults=1&children=0&infants=0&pets=0&check_in=2023-02-03&check_out=2023-02-09&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/17253081?adults=1&children=0&infants=0&pets=0&check_in=2023-02-02&check_out=2023-02-07&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/585311363438797308?adults=1&children=0&infants=0&pets=0&check_in=2023-02-14&check_out=2023-02-19&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/672148377508806019?adults=1&children=0&infants=0&pets=0&check_in=2023-11-28&check_out=2023-12-04&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/12414785?adults=1&children=0&infants=0&pets=0&check_in=2023-04-22&check_out=2023-04-28&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/35980940?adults=1&children=0&infants=0&pets=0&check_in=2023-02-26&check_out=2023-03-04&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/17227417?adults=1&children=0&infants=0&pets=0&check_in=2023-03-31&check_out=2023-04-07&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/806249318335956109?adults=1&children=0&infants=0&pets=0&check_in=2023-02-03&check_out=2023-02-08&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/722540128797545418?adults=1&children=0&infants=0&pets=0&check_in=2023-11-01&check_out=2023-11-08&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/640957686671430797?adults=1&children=0&infants=0&pets=0&check_in=2023-03-26&check_out=2023-03-31&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/37773248?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/551864311114545925?adults=1&children=0&infants=0&pets=0&check_in=2023-06-05&check_out=2023-06-11&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/32705597?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/19277929?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-29&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/26766044?adults=1&children=0&infants=0&pets=0&check_in=2023-01-21&check_out=2023-01-26&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/9768173?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/32705597?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/19277929?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-29&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/26766044?adults=1&children=0&infants=0&pets=0&check_in=2023-01-21&check_out=2023-01-26&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/9768173?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/47754370?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/803478424422983777?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-24&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/46043645?adults=1&children=0&infants=0&pets=0&check_in=2023-01-30&check_out=2023-02-04&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/28277705?adults=1&children=0&infants=0&pets=0&check_in=2023-03-05&check_out=2023-03-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/725905771760277558?adults=1&children=0&infants=0&pets=0&check_in=2023-06-26&check_out=2023-07-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/6545997?adults=1&children=0&infants=0&pets=0&check_in=2023-02-02&check_out=2023-02-07&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/787436640855953369?adults=1&children=0&infants=0&pets=0&check_in=2023-01-19&check_out=2023-01-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/638305428398330977?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/34683708?adults=1&children=0&infants=0&pets=0&check_in=2023-03-26&check_out=2023-03-31&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/18239784?adults=1&children=0&infants=0&pets=0&check_in=2023-02-04&check_out=2023-02-09&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/45692697?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-12&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/44370005?adults=1&children=0&infants=0&pets=0&check_in=2023-03-06&check_out=2023-03-12&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/25880432?adults=1&children=0&infants=0&pets=0&check_in=2023-03-27&check_out=2023-04-02&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/50417240?adults=1&children=0&infants=0&pets=0&check_in=2023-02-27&check_out=2023-03-04&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/53641703?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/44035109?adults=1&children=0&infants=0&pets=0&check_in=2023-03-05&check_out=2023-03-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/41645642?adults=1&children=0&infants=0&pets=0&check_in=2023-02-27&check_out=2023-03-04&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/802836588573681984?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/10733576?adults=1&children=0&infants=0&pets=0&check_in=2023-03-12&check_out=2023-03-17&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/651298281979473745?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/702136058838170491?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/780393189043316201?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/29138832?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/18750916?adults=1&children=0&infants=0&pets=0&check_in=2023-02-13&check_out=2023-02-19&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/16132937?adults=1&children=0&infants=0&pets=0&check_in=2023-11-16&check_out=2023-11-21&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/673637864074774522?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/4500694?adults=1&children=0&infants=0&pets=0&check_in=2023-02-27&check_out=2023-03-04&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/26991935?adults=1&children=0&infants=0&pets=0&check_in=2023-02-25&check_out=2023-03-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/16213810?adults=1&children=0&infants=0&pets=0&check_in=2023-03-13&check_out=2023-03-18&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/41762147?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/5520273?adults=1&children=0&infants=0&pets=0&check_in=2023-02-10&check_out=2023-02-15&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/36473296?adults=1&children=0&infants=0&pets=0&check_in=2023-01-19&check_out=2023-01-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/638305428398330977?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/724505227705541419?adults=1&children=0&infants=0&pets=0&check_in=2023-02-20&check_out=2023-02-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/27720151?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/39242461?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/45754546?adults=1&children=0&infants=0&pets=0&check_in=2023-02-06&check_out=2023-02-13&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/711323457881778389?adults=1&children=0&infants=0&pets=0&check_in=2023-01-20&check_out=2023-01-27&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/27871508?adults=1&children=0&infants=0&pets=0&check_in=2023-02-27&check_out=2023-03-04&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/5937726?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/35967247?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/623632030831415322?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/18251917?adults=1&children=0&infants=0&pets=0&check_in=2023-06-21&check_out=2023-06-26&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/44401285?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-28&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/53638118?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/47791290?adults=1&children=0&infants=0&pets=0&check_in=2023-10-20&check_out=2023-10-25&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/31358573?adults=1&children=0&infants=0&pets=0&check_in=2023-03-09&check_out=2023-03-14&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/51421663?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-30&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/686012375955193499?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-28&previous_page_section_name=1000',
        'https://www.airbnb.com//rooms/738847781625605690?adults=1&children=0&infants=0&pets=0&check_in=2023-04-24&check_out=2023-04-29&previous_page_section_name=1000']

    print('get detail url processing time: %.2f second(s)' % (time.time() - start_time))

    # get datas
    start_time = time.time()
    with concurrent.futures.thread.ThreadPoolExecutor() as executor:
        datas = list(executor.map(get_datas_2, detail_urls, repeat(working_proxies, len(detail_urls))))

    print(datas)
    print('get datas processing time: %.2f second(s)' % (time.time() - start_time))

    # save to csv
    start_time = time.time()
    to_csv(datas, save_path)
    print('to_csv processing time: %.2f second(s)' % (time.time() - start_time))
# Import required package
import csv
import os
import random
import time
import re
from http.client import EXPECTATION_FAILED

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
                                           timeout=(5,27))
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
                response = session.get(next_page_url, proxies=formated_proxy, headers=headers, timeout=(5, 27))
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
                print(e)
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
    review_locator = '//*[@id="tab--user-profile-review-tabs--0"]'

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
                driver.set_page_load_timeout(15)
                driver.get(url)
                # WebDriverWait(driver, 10).until(ec.element_to_be_clickable((By.XPATH, profile_locator)))
                try:
                    WebDriverWait(driver,10).until(ec.presence_of_element_located((By.CSS_SELECTOR, close_modal_locator)))
                    driver.find_element(By.CSS_SELECTOR, close_modal_locator).click()
                except Exception as e:
                    print(e)
                    WebDriverWait(driver, 10).until(ec.element_to_be_clickable((By.XPATH, profile_locator)))
                    print(f"modal translation is not visible")

                data['link'] = driver.current_url
                data['name'] = driver.find_element(By.CSS_SELECTOR, name_locator).text
                driver.find_element(By.XPATH, profile_locator).click()
                try:
                    data['price'] = int(re.findall(r'\b\d+\b', driver.find_element(By.XPATH, disc_price_locator).text))
                except Exception as e:
                    data['price'] = int(re.findall(r'\b\d+\b', driver.find_element(By.XPATH, price_locator).text))
                driver.find_element(By.XPATH, profile_locator).click()
                time.sleep(20)
                tab1 = driver.window_handles[0]
                tab2 = driver.window_handles[1]
                driver.switch_to.window(tab2)
                print(driver.current_url)
                WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.XPATH, job_locator)))
                try:
                    data[
                        'instagram'] = f"https://www.instagram.com/{driver.find_element(By.XPATH, job_locator).text.split('@')[-1].split()[0]}/"
                except Exception as e:
                    data['instagram'] = None
                try:
                    data['review'] = int(re.findall(r'\b\d+\b', driver.find_element(By.XPATH, review_locator).text))
                except:
                    data['review'] = 0

                driver.quit()
                datas.append(data.copy())

                break

                # status_code = ec.presence_of_element_located((By.CSS_SELECTOR, close_modal_locator))
                # status_code = ec.presence_of_element_located((By.CSS_SELECTOR, profile_locator))

            except Exception as e:
                driver.quit()
                selected_proxy = random.choice(selected_proxies)
                print(f"Change proxy to {selected_proxy}")
                trial += 1

        if trial < 5:
            print(f'{len(datas)} datas are collected')
        else:
            print('Connenction Error')

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
    start_time = time.time()
    scraped_proxies = get_proxy()
    working_proxies = choose_proxy(scraped_proxies)
    print(working_proxies)
    # working_proxies = ['47.243.105.131:4780', '103.92.26.190:4002', '171.101.74.119:8080']
    detail_urls = get_detail_url(url, working_proxies=working_proxies)
    # print(detail_urls)
    detail_urls = ['https://www.airbnb.com//rooms/18521687?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/663484635456479209?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/13122058?adults=1&children=0&infants=0&pets=0&check_in=2023-03-17&check_out=2023-03-24&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/13162145?adults=1&children=0&infants=0&pets=0&check_in=2023-03-06&check_out=2023-03-12&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/645459718750771967?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/26766044?adults=1&children=0&infants=0&pets=0&check_in=2023-01-14&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/632481632827632494?adults=1&children=0&infants=0&pets=0&check_in=2023-01-13&check_out=2023-01-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/655511314824007229?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/784539966739738163?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/547825121142703401?adults=1&children=0&infants=0&pets=0&check_in=2023-02-20&check_out=2023-02-25&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/46043645?adults=1&children=0&infants=0&pets=0&check_in=2023-01-30&check_out=2023-02-05&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/666363082285199382?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/749648911863699961?adults=1&children=0&infants=0&pets=0&check_in=2023-01-13&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/551864311114545925?adults=1&children=0&infants=0&pets=0&check_in=2023-01-30&check_out=2023-02-05&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/1015379?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/12349210?adults=1&children=0&infants=0&pets=0&check_in=2023-01-14&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/738847781625605690?adults=1&children=0&infants=0&pets=0&check_in=2023-04-24&check_out=2023-04-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/44353407?adults=1&children=0&infants=0&pets=0&check_in=2023-04-10&check_out=2023-04-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/29473779?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/54347284?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/16967210?adults=1&children=0&infants=0&pets=0&check_in=2023-03-03&check_out=2023-03-08&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/612196126355080278?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-19&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/773118921716241392?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/669560724544886830?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/547187488400579776?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/44469927?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/14696900?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52342377?adults=1&children=0&infants=0&pets=0&check_in=2023-01-28&check_out=2023-02-02&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/12238423?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/31976913?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43814920?adults=1&children=0&infants=0&pets=0&check_in=2023-02-13&check_out=2023-02-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/718744717609522584?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/47185340?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/49604139?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-19&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/27844982?adults=1&children=0&infants=0&pets=0&check_in=2023-01-26&check_out=2023-01-31&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/797142955726999557?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-28&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/797142955726999557?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-28&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/794753839515960689?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/675372115266201939?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/720181915255082313?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/29005858?adults=1&children=0&infants=0&pets=0&check_in=2023-06-22&check_out=2023-06-28&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/38131435?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/44469927?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/28379011?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-28&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/48669044?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/41953733?adults=1&children=0&infants=0&pets=0&check_in=2023-01-14&check_out=2023-01-19&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43817372?adults=1&children=0&infants=0&pets=0&check_in=2023-03-12&check_out=2023-03-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/49200820?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/799919363322598230?adults=1&children=0&infants=0&pets=0&check_in=2023-01-13&check_out=2023-01-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/678937378254782795?adults=1&children=0&infants=0&pets=0&check_in=2023-07-17&check_out=2023-07-23&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/733987897564897984?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-19&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52512859?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/32509871?adults=1&children=0&infants=0&pets=0&check_in=2023-03-02&check_out=2023-03-09&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/737374858667519765?adults=1&children=0&infants=0&pets=0&check_in=2023-02-06&check_out=2023-02-11&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/555700153795504858?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/53002967?adults=1&children=0&infants=0&pets=0&check_in=2023-03-05&check_out=2023-03-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/45546939?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/23163699?adults=1&children=0&infants=0&pets=0&check_in=2023-02-03&check_out=2023-02-08&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/39445904?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/796163715363467041?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/54373395?adults=1&children=0&infants=0&pets=0&check_in=2023-02-27&check_out=2023-03-04&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/754989397377031581?adults=1&children=0&infants=0&pets=0&check_in=2023-01-13&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/622883760429512991?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/50937848?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/38033633?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43994436?adults=1&children=0&infants=0&pets=0&check_in=2023-12-25&check_out=2023-12-31&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/670806019201784094?adults=1&children=0&infants=0&pets=0&check_in=2023-02-26&check_out=2023-03-03&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/46048765?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43795657?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52670098?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/49920591?adults=1&children=0&infants=0&pets=0&check_in=2023-03-05&check_out=2023-03-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52233878?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52233878?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/36931678?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/46549617?adults=1&children=0&infants=0&pets=0&check_in=2023-01-13&check_out=2023-01-19&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52922148?adults=1&children=0&infants=0&pets=0&check_in=2023-01-14&check_out=2023-01-19&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/5706158?adults=1&children=0&infants=0&pets=0&check_in=2023-02-02&check_out=2023-02-07&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/28779013?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-19&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/51596918?adults=1&children=0&infants=0&pets=0&check_in=2023-01-20&check_out=2023-01-25&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/42320793?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/796849904073175148?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/556403144075739762?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/670980771120687394?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-19&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/49765152?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/44401285?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43672798?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/798369315670847191?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/33907970?adults=1&children=0&infants=0&pets=0&check_in=2023-01-20&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/36437683?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/11258864?adults=1&children=0&infants=0&pets=0&check_in=2023-01-21&check_out=2023-01-26&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/33907970?adults=1&children=0&infants=0&pets=0&check_in=2023-01-20&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/36437683?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/11258864?adults=1&children=0&infants=0&pets=0&check_in=2023-01-21&check_out=2023-01-26&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/50276168?adults=1&children=0&infants=0&pets=0&check_in=2023-01-24&check_out=2023-01-29&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/10693530?adults=1&children=0&infants=0&pets=0&check_in=2023-02-26&check_out=2023-03-03&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/34683708?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/4502646?adults=1&children=0&infants=0&pets=0&check_in=2023-03-19&check_out=2023-03-24&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/720073411182460108?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/42828138?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-19&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/28554132?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-28&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/26965977?adults=1&children=0&infants=0&pets=0&check_in=2023-02-06&check_out=2023-02-11&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/10563051?adults=1&children=0&infants=0&pets=0&check_in=2023-04-16&check_out=2023-04-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/797233703345709375?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/790684385153906110?adults=1&children=0&infants=0&pets=0&check_in=2023-02-01&check_out=2023-02-06&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/45056309?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/53109666?adults=1&children=0&infants=0&pets=0&check_in=2023-02-13&check_out=2023-02-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/40135137?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/24958521?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/679442277136508138?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/30700216?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/775830976934967420?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/24486842?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/794113017337550996?adults=1&children=0&infants=0&pets=0&check_in=2023-01-21&check_out=2023-01-26&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/50455820?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-05&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/51134026?adults=1&children=0&infants=0&pets=0&check_in=2023-03-02&check_out=2023-03-07&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/15534294?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/53617070?adults=1&children=0&infants=0&pets=0&check_in=2023-01-13&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/42735877?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/48686587?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/45130857?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/45754542?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/553594269017890273?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/48330899?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/34693798?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/49133684?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/614982397366037662?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/10845191?adults=1&children=0&infants=0&pets=0&check_in=2023-03-02&check_out=2023-03-07&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/6788954?adults=1&children=0&infants=0&pets=0&check_in=2023-05-16&check_out=2023-05-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/24958521?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/2916945?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/18750916?adults=1&children=0&infants=0&pets=0&check_in=2023-02-13&check_out=2023-02-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/53617070?adults=1&children=0&infants=0&pets=0&check_in=2023-01-13&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/6475127?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/640957686671430797?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43537696?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/45754542?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/720037607904813446?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/46447673?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/599676224294414374?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/45745772?adults=1&children=0&infants=0&pets=0&check_in=2023-01-31&check_out=2023-02-07&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/49557545?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/18090396?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43523807?adults=1&children=0&infants=0&pets=0&check_in=2023-04-02&check_out=2023-04-08&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/663438201930206614?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/2475235?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/675149558308921583?adults=1&children=0&infants=0&pets=0&check_in=2023-02-26&check_out=2023-03-03&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/762953820839187460?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/54206350?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/36908027?adults=1&children=0&infants=0&pets=0&check_in=2023-03-20&check_out=2023-03-25&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/45682824?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-30&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/620217090290949354?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/552915837374149723?adults=1&children=0&infants=0&pets=0&check_in=2023-01-19&check_out=2023-01-24&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/51530480?adults=1&children=0&infants=0&pets=0&check_in=2023-01-14&check_out=2023-01-19&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/765769311273817975?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/716388304158934417?adults=1&children=0&infants=0&pets=0&check_in=2023-01-30&check_out=2023-02-04&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/21467207?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/34693798?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/47868254?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/35088650?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52766039?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/51861612?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/37768869?adults=1&children=0&infants=0&pets=0&check_in=2023-12-01&check_out=2023-12-06&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/42986806?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/765769311273817975?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/18750916?adults=1&children=0&infants=0&pets=0&check_in=2023-02-13&check_out=2023-02-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/18090396?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/765970235104357418?adults=1&children=0&infants=0&pets=0&check_in=2023-01-14&check_out=2023-01-19&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/29619942?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/563625832767687902?adults=1&children=0&infants=0&pets=0&check_in=2023-02-15&check_out=2023-02-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43807794?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/42173305?adults=1&children=0&infants=0&pets=0&check_in=2023-02-11&check_out=2023-02-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/37768869?adults=1&children=0&infants=0&pets=0&check_in=2023-12-01&check_out=2023-12-06&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/50762484?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/791327047769421357?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/50952403?adults=1&children=0&infants=0&pets=0&check_in=2023-02-02&check_out=2023-02-08&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/625683137433149381?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/42483895?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/600352600119488042?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/50768533?adults=1&children=0&infants=0&pets=0&check_in=2023-02-13&check_out=2023-02-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/41094334?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/635938751706586026?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/678139?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/48806789?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-19&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43677822?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/13729878?adults=1&children=0&infants=0&pets=0&check_in=2023-01-23&check_out=2023-01-28&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/791744313492866759?adults=1&children=0&infants=0&pets=0&check_in=2023-01-29&check_out=2023-02-03&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/710527100095989248?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/35088650?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/586141223158601994?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/797850751736579200?adults=1&children=0&infants=0&pets=0&check_in=2023-01-17&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/2916945?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/25822252?adults=1&children=0&infants=0&pets=0&check_in=2023-02-02&check_out=2023-02-07&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/587652946112393877?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-24&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/42321414?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/51861612?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/784494773853228607?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/48563759?adults=1&children=0&infants=0&pets=0&check_in=2023-01-13&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/5554483?adults=1&children=0&infants=0&pets=0&check_in=2023-01-24&check_out=2023-01-31&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/48563759?adults=1&children=0&infants=0&pets=0&check_in=2023-01-13&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/734615819034123022?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/5554483?adults=1&children=0&infants=0&pets=0&check_in=2023-01-24&check_out=2023-01-31&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/48137229?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/18840169?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/50757650?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-23&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/29605455?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/599867120056612766?adults=1&children=0&infants=0&pets=0&check_in=2023-03-27&check_out=2023-04-02&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/800121620489755461?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/555584093029808791?adults=1&children=0&infants=0&pets=0&check_in=2023-01-17&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/25410569?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/6620672?adults=1&children=0&infants=0&pets=0&check_in=2023-07-03&check_out=2023-07-08&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/53177716?adults=1&children=0&infants=0&pets=0&check_in=2023-05-12&check_out=2023-05-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/51774073?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/26442003?adults=1&children=0&infants=0&pets=0&check_in=2023-03-16&check_out=2023-03-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/47868254?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/52645856?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-19&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/791721390440699151?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/51545932?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-19&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/54353205?adults=1&children=0&infants=0&pets=0&check_in=2023-04-23&check_out=2023-04-28&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/29138832?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/671898836909946262?adults=1&children=0&infants=0&pets=0&check_in=2023-01-13&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/47791290?adults=1&children=0&infants=0&pets=0&check_in=2023-02-27&check_out=2023-03-04&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/46468536?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/47248319?adults=1&children=0&infants=0&pets=0&check_in=2023-01-14&check_out=2023-01-19&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/44165333?adults=1&children=0&infants=0&pets=0&check_in=2023-02-08&check_out=2023-02-13&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/799958311129483638?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/21467207?adults=1&children=0&infants=0&pets=0&check_in=2023-02-05&check_out=2023-02-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/799894449030239086?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-22&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/44400305?adults=1&children=0&infants=0&pets=0&check_in=2023-01-18&check_out=2023-01-23&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/42661008?adults=1&children=0&infants=0&pets=0&check_in=2023-05-08&check_out=2023-05-13&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/572103741139745432?adults=1&children=0&infants=0&pets=0&check_in=2023-01-24&check_out=2023-01-29&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/plus/1039139?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/47593160?adults=1&children=0&infants=0&pets=0&check_in=2023-01-15&check_out=2023-01-20&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/38613860?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/43051416?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/45682913?adults=1&children=0&infants=0&pets=0&check_in=2023-02-11&check_out=2023-02-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/54090003?adults=1&children=0&infants=0&pets=0&check_in=2023-01-19&check_out=2023-01-24&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/792641880181537093?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/625775081594425165?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/638419808293798296?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/53944435?adults=1&children=0&infants=0&pets=0&check_in=2023-01-31&check_out=2023-02-05&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/46443974?adults=1&children=0&infants=0&pets=0&check_in=2023-05-07&check_out=2023-05-12&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/674476703999629765?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/47015377?adults=1&children=0&infants=0&pets=0&check_in=2023-01-16&check_out=2023-01-21&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/42381112?adults=1&children=0&infants=0&pets=0&check_in=2023-01-22&check_out=2023-01-27&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/40410476?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/44035109?adults=1&children=0&infants=0&pets=0&check_in=2023-03-05&check_out=2023-03-10&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/47825352?adults=1&children=0&infants=0&pets=0&check_in=2023-01-13&check_out=2023-01-18&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/40652747?adults=1&children=0&infants=0&pets=0&check_in=2023-01-12&check_out=2023-01-19&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/49960259?adults=1&children=0&infants=0&pets=0&check_in=2023-07-01&check_out=2023-07-07&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/569261689912817039?adults=1&children=0&infants=0&pets=0&check_in=2023-02-06&check_out=2023-02-11&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/32705597?adults=1&children=0&infants=0&pets=0&check_in=2023-02-12&check_out=2023-02-17&previous_page_section_name=1000', 'https://www.airbnb.com//rooms/50182907?adults=1&children=0&infants=0&pets=0&check_in=2023-01-11&check_out=2023-01-16&previous_page_section_name=1000']
    datas = get_datas(detail_urls, selected_proxies=working_proxies)
    to_csv(datas, save_path)
    print('processing time: %.2f seconds' % (time.time() - start_time))
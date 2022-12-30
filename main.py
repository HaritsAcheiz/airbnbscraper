import requests
from bs4 import BeautifulSoup

def get_detail_url(url):
    print('Collecting url...')
    page = 1
    url_schema = url.split('/')[2]
    detail_url_locators = "div.gh7uyir.giajdwt.g14v8520.dir.dir-ltr > div"
    next_page_locator = "a._1bfat5l"
    session = requests.Session()
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    next_page_url = soup.select_one(next_page_locator)
    html_detail_urls = soup.select(detail_url_locators)
    detail_urls = list()
    url_locator = "div.cy5jw6o.dir.dir-ltr > a"
    for i in html_detail_urls:
        detail_urls.append(f"{url_schema}/{i.select_one(url_locator)['href']}")
    print(f"{len(detail_urls)} url collected from page {page}")
    return detail_urls

def to_file(data, save_path):
    pass

if __name__ == '__main__':
    url = "https://www.airbnb.co.id/s/Belgium/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&price_filter_input_type=0&price_filter_num_nights=5&query=Belgium&place_id=ChIJl5fz7WR9wUcR8g_mObTy60c&date_picker_type=calendar&flexible_trip_lengths%5B%5D=weekend_trip&checkin=2023-01-29&checkout=2023-01-30&adults=1&source=structured_search_input_header&search_type=autocomplete_click"
    save_path = "C:\project\airbnbscraper\result.csv"
    detail_urls = get_detail_url(url)

    # to_file(data, save_path)
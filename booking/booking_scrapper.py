from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup, SoupStrainer
from .constants import DATA_TO_BE_SCRAPPED
import threading
import multiprocessing
import time, re

def scrape_chunk_of_data(html_content, parent_attr, items_attr, tag_attr, data_name):
    data = []
    strainer = SoupStrainer('div', attrs=parent_attr)
    soup = BeautifulSoup(html_content, 'lxml', parse_only=strainer)
    parent_box = soup.find('div', attrs=parent_attr)
    parent_items = parent_box.find_all('div', attrs=items_attr)
    if data_name == "property_stars":
        stars_values = []
        for item in parent_items:
            star_value = re.sub(r'[^\d]', '', item.get('data-filters-item'))
            stars_values.append(star_value)
        return stars_values
    for item in parent_items:
        tag = item.find('div', attrs=tag_attr)
        if tag and tag.string:
            # with lock:
            data.append(tag.string)
            # parsed_data[data_name].append(tag.string)
    return data

class BookingScrapper:

    def __init__(self, selenium_web_driver:WebDriver):
        self.selenium_web_driver = selenium_web_driver

    def pull_data(self):
        return self.parse_data()
    
    def get_specific_data(self, el_locator):
        if el_locator['btn_locator'] is not None:
            self.try_expanding_list(locator=el_locator['btn_locator'])
        html_content = self.selenium_web_driver.page_source  
        return scrape_chunk_of_data(html_content, el_locator['parent_attr'], el_locator['items_attr'], el_locator['tag_attr'], el_locator['data_name'])
    
    def get_property_price_range(self):
        budget_per_night_range_locator = (By.CSS_SELECTOR, 'div[data-filters-group="price"] > div[data-testid="filters-group-slider"] > span > div')
        budget_per_night_range_txt = self.selenium_web_driver.find_element(*budget_per_night_range_locator).text.strip()
        bounds = budget_per_night_range_txt.replace(' ', '').replace("\u2013", "-").split("-")
        lower_bound = int(re.sub(r'[^\d,]', '', bounds[0]).replace(',', ''))
        upper_bound = int(re.sub(r'[^\d,]', '', bounds[1]).replace(',', ''))
        return {
            'lower_range': lower_bound,
            'upper_range': upper_bound
        }

    def scrape_all_data(self):
        # Try to expand every box that is possible to have all the data to scrape
        neighborhood_btn_locator = (By.CSS_SELECTOR, 'div[data-filters-group="di"] > button')
        hotel_facility_btn_locator = (By.CSS_SELECTOR, 'div[data-filters-group="hotelfacility"] > button')
        room_facility_btn_locator = (By.CSS_SELECTOR, 'div[data-filters-group="roomfacility"] > button')
        property_btn_locator = (By.CSS_SELECTOR, 'div[data-filters-group="ht_id"] > button')
        budget_per_night_range_locator = (By.CSS_SELECTOR, 'div[data-filters-group="price"] > div[data-testid="filters-group-slider"] > span > div')
        budget_per_night_range_txt = self.selenium_web_driver.find_element(*budget_per_night_range_locator).text.strip()
        bounds = budget_per_night_range_txt.replace(' ', '').replace("\u2013", "-").split("-")
        lower_bound = re.sub(r'[^\d,]', '', bounds[0])
        upper_bound = re.sub(r'[^\d,+]', '', bounds[1])
        locators = [neighborhood_btn_locator, hotel_facility_btn_locator, room_facility_btn_locator, property_btn_locator]
        locator_threads = []

        for locator in locators:
            t = threading.Thread(
                target=self.try_expanding_list,
                args=(locator,)
            )
            locator_threads.append(t)
            t.start()
        for thread in locator_threads:
            thread.join()
        print(f'Scraping started...')
        start_time = time.time()
        html_content = self.selenium_web_driver.page_source
        
        with multiprocessing.Manager() as manager:
            scrapped_data = manager.dict() # Common dictionary for processes
            lock = manager.Lock() # Common lock for processes
            processes = []
            for data_obj in DATA_TO_BE_SCRAPPED:
                scrapped_data[data_obj['data_name']] = manager.list()
                p = multiprocessing.Process(
                    target=scrape_chunk_of_data,
                    args=(html_content, data_obj['parent_attr'], data_obj['items_attr'], data_obj['tag_attr'], scrapped_data, lock, data_obj['data_name'])
                )
                processes.append(p)
                p.start()
            for p in processes:
                p.join()
            scrapped_data = {key: list(value) for key, value in scrapped_data.items()}
        scrapped_data['budget_range'] = (lower_bound, upper_bound)
        print(f'Time elapsed in seconds: {(time.time() - start_time)}')
        return scrapped_data

    def try_expanding_list(self, locator):
        try:
            element = WebDriverWait(self.selenium_web_driver, timeout=1.5, poll_frequency=0.3).until(
                EC.presence_of_element_located(locator)
            )
            ActionChains(self.selenium_web_driver).move_to_element(element).click().pause(0.4).perform()
            WebDriverWait(self.selenium_web_driver, 1.5).until(
                EC.text_to_be_present_in_element_attribute(locator, "aria-expanded", "true")
            )
        except StaleElementReferenceException:
            element = WebDriverWait(self.selenium_web_driver, timeout=1.5, poll_frequency=0.3).until(
                EC.presence_of_element_located(locator)
            )
            ActionChains(self.selenium_web_driver).move_to_element(element).click().pause(0.4).perform()
            WebDriverWait(self.selenium_web_driver, 1.5).until(
                EC.text_to_be_present_in_element_attribute(locator, "aria-expanded", "true")
            )
        except TimeoutException as e:
            print(f"Element of locator: {locator} was not found on the site.")

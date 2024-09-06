# File includes a class with instance methods
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

class BookingFiltration:

    def __init__(self, web_driver:WebDriver):
        self.web_driver = web_driver

    def apply_star_rating(self, *star_values):
        actions = ActionChains(self.web_driver)
        star_box = WebDriverWait(self.web_driver, 10).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'div[data-filters-group="class"]')
            )            
        )
        actions.move_to_element(star_box).pause(0.5).perform()
        for star_val in star_values:
            WebDriverWait(self.web_driver, 10).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, 'div[data-filters-group="class"]')
                )            
            )
            filter_el = WebDriverWait(self.web_driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, f'div[data-filters-item="class:class={str(star_val)}"]'))
            )
            if not filter_el.is_selected():
                filter_el.click()
                self.await_results()

    # 1 sort type available at a time
    def apply_sorting(self, sort_type):
        sort_box_btn = self.web_driver.find_element(By.CSS_SELECTOR, 'button[data-testid="sorters-dropdown-trigger"]')
        sort_box_btn.click()
        WebDriverWait(self.web_driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-testid="sorters-dropdown"]'))
        )
        sorting_options_box = self.web_driver.find_element(By.CSS_SELECTOR, 'div[data-testid="sorters-dropdown"] > ul')
        sort_option_el = sorting_options_box.find_element(By.XPATH, f'.//li//span[text()="{sort_type}"]')
        sort_option_el.click()

    def apply_bedrooms_and_bathrooms_count(self, **kwargs):
        if kwargs['bedrooms'] is not None:
            box_element = self.web_driver.find_element(By.CSS_SELECTOR, 'div[data-filters-group="unit_config_grouped"]')
            bedrooms_btn_element = box_element.find_element(By.CSS_SELECTOR, 'div[data-filters-item="unit_config_grouped:entire_place_bedroom_count"] > div.f71ad9bb14 > button.dba1b3bddf.e99c25fd33.aabf155f9a.f42ee7b31a.a86bcdb87f.e137a4dfeb.d1821e6945')
            for _ in range(kwargs['bedrooms']):
                bedrooms_btn_element.click()
        if kwargs['bathrooms'] is not None:
            bathrooms_btn_element = box_element.find_element(By.CSS_SELECTOR, 'div[data-filters-item="unit_config_grouped:min_bathrooms"] > div.f71ad9bb14 > button.dba1b3bddf.e99c25fd33.aabf155f9a.f42ee7b31a.a86bcdb87f.e137a4dfeb.d1821e6945')
            for _ in range(kwargs['bathrooms']):
                bathrooms_btn_element.click()
    
    def apply_neighborhood(self, places):
        for place in places:
            try:
                element = self.web_driver.find_element(By.CSS_SELECTOR, 'div[data-filters-group="di"]').find_element(By.XPATH, f'.//div[text()="{place}"]')
                element.click()
                self.await_results()
            except Exception as e:
                print(e.__str__)

    def apply_hotel_facilities(self, facilities):
        for facility in facilities:
            try:
                element = self.web_driver.find_element(By.CSS_SELECTOR, 'div[data-filters-group="hotelfacility"]').find_element(By.XPATH, f'.//div[text()="{facility}"]')
                element.click()
                self.await_results()
            except Exception as e: 
                print(e.__str__)

    def apply_room_facilities(self, facilities):
        for room_facility in facilities:
            try:
                element = self.web_driver.find_element(By.CSS_SELECTOR, 'div[data-filters-group="roomfacility"]').find_element(By.XPATH, f'.//div[text()="{room_facility}"]')
                element.click()
                self.await_results()
            except Exception as e:
                print(e.__str__)

    def apply_properties(self, properties):
        for property in properties:
            try:
                element = self.web_driver.find_element(By.CSS_SELECTOR, 'div[data-filters-group="ht_id"]').find_element(By.XPATH, f'.//div[text()="{property}"]')
                element.click()
                self.await_results()
            except Exception as e:
                print(e.__str__)

    def adjust_budget(self, range):
        pass

    def await_results(self):
        try:
            skeleton_loader_locator = (By.CSS_SELECTOR, 'div[data-testid="skeleton-loader"]')
            WebDriverWait(self.web_driver, 10).until(
                EC.presence_of_element_located(skeleton_loader_locator)
            )
        except TimeoutException: 
            print('Unable to wait for all the results')
        except Exception as e:
            print(f'Error occurred: {str(e)}')
    
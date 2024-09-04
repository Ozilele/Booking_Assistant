from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from .constants import RESULTS_PER_CALL
import re

class BookingReport:

    def __init__(self, web_driver:WebDriver, box_section_element:WebElement, wait_for_results):
        self.web_driver = web_driver
        self.box_section_element = box_section_element
        self.deals = self.pull_deal_boxes(wait_for_results)

    def pull_deal_boxes(self, wait_for_new_results): # method used in __init__
        cards = self.box_section_element.find_elements(By.CSS_SELECTOR, 'div[data-testid="property-card"]')
        properties_count_txt = self.web_driver.find_element(By.CSS_SELECTOR, "div.eda0d449dc.a45957e294 > h1").get_attribute('innerHTML').strip()
        properties_count = int(re.sub(r'[^\d]', '', properties_count_txt))
        print(f"Properties count: {properties_count}")
        curr_count = 0
        deal_boxes = []
        isStopped = False

        for i in range(properties_count):
            if isStopped is True:
                break
            elif i % RESULTS_PER_CALL == 0:
                if curr_count < 75:
                    # Move to the last element to load new results and wait for new results
                    ActionChains(self.web_driver).move_to_element(cards[i-1]).pause(1).perform()
                    wait_for_new_results()
                else:
                    load_new_results_btn = self.box_section_element.find_element(By.CSS_SELECTOR, 'div.e01df12ddf.d399a62c2a > button')
                    load_new_results_btn.click()
                    wait_for_new_results()
                cards = self.box_section_element.find_elements(By.CSS_SELECTOR, 'div[data-testid="property-card"]')
            attempts = 0
            max_attempts = 5
            while attempts < max_attempts:
                try:
                    child = cards[i]
                    data_testid = child.get_attribute("data-testid")
                    if data_testid == "sticky-container": # stop condition
                        isStopped = True
                    elif data_testid == "property-card":
                        curr_count += 1
                        deal_boxes.append(child)
                    break
                except StaleElementReferenceException:
                    attempts += 1
                    if attempts >= max_attempts:
                        print("Maximum attempts reached...")
                        break  
        return deal_boxes
    
    def pull_deal_box_attributes(self, data, deals, lock):
        for deal_box in deals:
            attempts = 0
            max_attempts = 5
            hotel_name = ""
            hotel_price = ""
            hotel_score = ""
            while attempts < max_attempts:
                try:
                    hotel_name_locator = (By.CSS_SELECTOR, 'div[data-testid="title"]')
                    self.wait_for_element_presence(deal_box, hotel_name_locator, 2)
                    hotel_name = deal_box.find_element(*hotel_name_locator).get_attribute('innerHTML').strip()

                    price_locator = (By.CSS_SELECTOR, 'span[data-testid="price-and-discounted-price"]')
                    self.wait_for_element_presence(deal_box, price_locator, 2)
                    hotel_price = deal_box.find_element(*price_locator).get_attribute('innerHTML').strip()
                    # hotel_price = re.sub(r'[^\d]', '', hotel_price_txt) -> match for any character except digit
                    hotel_score_locator = (By.CSS_SELECTOR, "div.d0522b0cca.fd44f541d8 > div") 
                    self.wait_for_element_presence(deal_box, hotel_score_locator, 2)
                    hotel_score = float(deal_box.find_element(*hotel_score_locator).get_attribute('innerHTML').strip().split(" ")[1])
                    with lock:
                        data.append([hotel_name, hotel_price, hotel_score])
                    break
                except StaleElementReferenceException:
                    attempts += 1
                    if attempts >= max_attempts:
                        print(f'Stale Element error exception')
                        with lock:
                            data.append([hotel_name, hotel_price, "unknown"])
                        break
                except NoSuchElementException as e:
                    if hotel_score == "":
                        with lock:
                            data.append([hotel_name, hotel_price, "unknown"])
                    break
    
    def get_deals_discounts(self, discounts, deals, discount_lock, max=None):
        for deal in deals:
            try:
                hotel_name_locator = (By.CSS_SELECTOR, 'div[data-testid="title"]')
                self.wait_for_element_presence(deal, hotel_name_locator, 0.8)
                hotel_name = deal.find_element(*hotel_name_locator).get_attribute('innerHTML').strip()

                old_price_locator = (By.CSS_SELECTOR, "span.f018fa3636.d9315e4fb0")
                self.wait_for_element_presence(deal, old_price_locator, 0.8)
                old_price_txt = deal.find_element(*old_price_locator).get_attribute('innerHTML').strip()
                old_price = int(re.sub(r'[^\d]', '', old_price_txt))

                new_price_locator = (By.CSS_SELECTOR, 'span[data-testid="price-and-discounted-price"]')
                self.wait_for_element_presence(deal, new_price_locator, 0.8)
                new_price_txt = deal.find_element(*new_price_locator).get_attribute('innerHTML').strip()
                new_price = int(re.sub(r'[^\d]', '', new_price_txt))
                discount = str(round((((old_price - new_price) / old_price) * 100), 2)) + "%"
                with discount_lock:
                    discounts.append([
                        hotel_name, new_price_txt, discount
                    ])
            except NoSuchElementException as e:
                continue
            
    def wait_for_element_presence(self, deal_box:WebElement, locator:tuple, time):
        ignored_exceptions = (StaleElementReferenceException, NoSuchElementException)
        try:
            WebDriverWait(self.web_driver, timeout=time, ignored_exceptions=ignored_exceptions).until(
                lambda driver: deal_box.find_element(*locator).is_displayed()
            )
        except (NoSuchElementException, TimeoutException) as e:
            print(f"Element with locator: {locator} not found in deal_box")
            raise NoSuchElementException(f"Element with locator {locator} was not found on DOM")
    

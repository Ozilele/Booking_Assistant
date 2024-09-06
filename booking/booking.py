from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
from prettytable import PrettyTable
from selenium.common.exceptions import StaleElementReferenceException
from .booking_filtration import BookingFiltration
from .booking_report import BookingReport
from .booking_scrapper import BookingScrapper
import booking.constants as const
import time
import threading

class Booking(webdriver.Chrome):

    def __init__(self, chrome_options, teardown=True):
        self.teardown = teardown
        self.advertise_closed = False
        super(Booking, self).__init__(options=chrome_options)
        self.delete_all_cookies()
        self.implicitly_wait(15)
        self.maximize_window()
        self.scrapper = BookingScrapper(self)
        self.filtration_obj = BookingFiltration(self)

    def __exit__(self, exc_type, exc, traceback):
        if self.teardown:
            time.sleep(90)
            self.quit()

    def land_first_page(self):
        self.get(const.BASE_URL)
        reject_cookie_btn = self.find_element(By.ID, "onetrust-reject-all-handler")
        reject_cookie_btn.click()
        self.try_close_advertise()

    def try_close_advertise(self):
        self.implicitly_wait(0)
        try:
            login_screen_close_btn = WebDriverWait(self, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Zamknij okno logowania."]')))
            login_screen_close_btn.click()
            self.advertise_closed = True
        except Exception as e:
            print("Error getting the advertise")
        finally:
            self.implicitly_wait(const.IMPLICIT_TIME)
        
    def change_language(self, language=None):
        curr_url = self.current_url
        language_btn = WebDriverWait(self, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'button[data-testid="header-language-picker-trigger"]'))
        )
        language_btn.click()
        specific_language_btn = self.find_element(By.XPATH, f'//button[@data-testid="selection-item" and .//span[contains(text(), "{language}")]]')
        specific_language_btn.click()
        if self.advertise_closed is False:
            self.try_close_advertise()
        self.wait_till_url_change(curr_url)

    def change_currency(self, currency=None):
        curr_url = self.current_url
        currency_btn = WebDriverWait(self, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'button[data-testid="header-currency-picker-trigger"]'))
        )
        currency_btn.click()
        specific_curr_btn = self.find_element(By.XPATH, f'//button[@data-testid="selection-item" and .//span[contains(text(), "{currency}")]]')
        specific_curr_btn.click()
        if self.advertise_closed is False:
            self.try_close_advertise()
        self.wait_till_url_change(curr_url)

    def wait_till_url_change(self, url):
        try:
            WebDriverWait(self, 15).until(
                EC.url_changes(url)
            )
        except TimeoutException:
            print("Url did not change - apply more timeout when you have slow internet connection")

    def select_place_to_go(self, place_to_go:str):
        actions = ActionChains(self)
        input_locator = (By.CSS_SELECTOR, 'input[name="ss"]')
        search_field_element = WebDriverWait(self, 8).until(
            EC.presence_of_element_located(input_locator)
        )
        search_field_element.clear()
        time.sleep(0.5)
        for char in place_to_go:
            try:
                search_field_element.send_keys(char)
                time.sleep(0.2)  # Krótkie opóźnienie po każdym znaku
            except StaleElementReferenceException:
                search_field_element = WebDriverWait(self, 8).until(
                    EC.presence_of_element_located(input_locator)
                )
                search_field_element.send_keys(char)
        WebDriverWait(self, 8).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'li[id="autocomplete-result-0"]'))
        )
        locator = (By.XPATH, f'//li[@id="autocomplete-result-0"]//div[contains(text(), "{place_to_go}")]')
        element = WebDriverWait(self, 8, poll_frequency=0.25).until(
            EC.presence_of_element_located(locator)
        )
        if element:
            actions.move_to_element(element).click().perform()

    def select_dates(self, check_in_date, check_out_date):
        span_check_in = self.find_element(By.CSS_SELECTOR, f'span[data-date="{check_in_date}"]')
        check_in_el = span_check_in.find_element(By.XPATH, "./parent::td")
        check_in_el.click()
        span_check_out = self.find_element(By.CSS_SELECTOR, f'span[data-date="{check_out_date}"]')
        check_out_el = span_check_out.find_element(By.XPATH, "./parent::td")
        check_out_el.click()

    def select_adults(self, adults=1, children=0, children_ages=(), rooms=1, withPets=False):
        # Default 1 adult, 0 children, 1 room - boundaries in booking.com
        select_btn = self.find_element(By.CSS_SELECTOR, 'button[data-testid="occupancy-config"]')
        select_btn.click()
        decrease_adults_btn = self.find_element(By.XPATH, '//*[@id=":ri:"]/div/div[1]/div[2]/button[1]')
        decrease_adults_btn.click()
        increase_adults_el = self.find_element(By.XPATH, '//*[@id=":ri:"]/div/div[1]/div[2]/button[2]')
        if adults > 1:
            for _ in range(1, adults):
                increase_adults_el.click()
        if children > 0:
            increase_children_el = self.find_element(By.XPATH, '//*[@id=":ri:"]/div/div[2]/div[2]/button[2]')
            for _ in range(children):
                increase_children_el.click()
            for i in range(1, children+1):
                select_element = self.find_element(By.CSS_SELECTOR, f'div[data-testid="kids-ages"] > div:nth-child({i}) > div > select')
                select = Select(select_element)
                select.select_by_value(str(children_ages[i-1]))
        if rooms > 1:
            if children > 0:    
                increase_rooms_el = self.find_element(By.XPATH, '//*[@id=":ri:"]/div/div[5]/div[2]/button[2]')
            else:
                increase_rooms_el = self.find_element(By.XPATH, '//*[@id=":ri:"]/div/div[3]/div[2]/button[2]')
            for _ in range(1, rooms):
                increase_rooms_el.click()
        if withPets: # if we travel with pets
            label_pets_el = self.find_element(By.CSS_SELECTOR, 'label[for="pets"]')
            label_pets_el.click()
        search_btn_element = self.find_element(By.XPATH, '//*[@id="indexsearch"]/div[2]/div/form/div[1]/div[4]/button')
        search_btn_element.click() # click search btn
        self.wait_for_results()
    
    def apply_filtration(self, **kwargs):
        filtration_methods = {
            'sort_by': lambda value: self.filtration_obj.apply_sorting(value),
            'bedrooms': lambda value: self.filtration_obj.apply_bedrooms_and_bathrooms_count(
                bedrooms=value, 
                bathrooms=kwargs.get('bathrooms') 
            ),
            'property_stars': lambda values: self.filtration_obj.apply_star_rating(*values),
            'neighborhood': lambda value: self.filtration_obj.apply_neighborhood(value),
            'hotel_facilities': lambda value: self.filtration_obj.apply_hotel_facilities(value),
            'room_facilities': lambda value: self.filtration_obj.apply_room_facilities(value),
            'properties': lambda value: self.filtration_obj.apply_properties(value),
            'budget_range': lambda value: self.filtration_obj.adjust_budget(value)
        }
        for key, values in kwargs.items():
            if key in filtration_methods:
                filtration_methods[key](values)
            elif key == 'bathrooms':
                self.filtration_obj.apply_bedrooms_and_bathrooms_count(bedrooms=kwargs.get('bedrooms'), bathrooms=values)
            self.wait_for_results()

    def apply_filtrations(self, *stars, **kwargs):
        filtration = BookingFiltration(web_driver=self)
        filtration.apply_star_rating(*stars)
        self.wait_for_results()
        filtration_methods = {
            'sort_by': lambda value: filtration.apply_sorting(value),
            'bedrooms': lambda value: filtration.apply_bedrooms_and_bathrooms_count(
                bedrooms=value, 
                bathrooms=kwargs.get('bathrooms') 
            ),
            'neighborhood': lambda value: filtration.apply_neighborhood(value),
            'hotel_facilities': lambda value: filtration.apply_hotel_facilities(value),
            'room_facilities': lambda value: filtration.apply_room_facilities(value),
            'properties': lambda value: filtration.apply_properties(value),
            'budget_range': lambda value: filtration.adjust_budget(value)
        }
        for key, value in kwargs.items():
            if key in filtration_methods:
                filtration_methods[key](value) # calling specific function from BookingFiltration class
                self.wait_for_results()
            elif key == 'bathrooms':
                filtration.apply_bedrooms_and_bathrooms_count(bedrooms=kwargs.get('bedrooms'), bathrooms=value)

    def report_data(self):
        hotels_box = WebDriverWait(self, 3).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.f9958fb57b"))
        )
        report = BookingReport(self, hotels_box, self.wait_for_results)
        # Create report with all the data
        report_data = []
        report_discounts = []
        data_lock = threading.Lock()
        report_data_threads = []
        deals_per_thread = 12
        for i in range(0, len(report.deals), deals_per_thread):
            t = threading.Thread(target=report.pull_deal_box_attributes, args=(report_data, report.deals[i:min(len(report.deals), i+deals_per_thread)], data_lock))
            report_data_threads.append(t)
            t.start()
        
        discount_lock = threading.Lock()
        report_discounts_threads = []
        discounts_per_thread = 8
        for i in range(0, len(report.deals), discounts_per_thread):
            t = threading.Thread(target=report.get_deals_discounts, args=(report_discounts, report.deals[i:min(len(report.deals), i+discounts_per_thread)], discount_lock))
            report_discounts_threads.append(t)
            t.start()
        for t in report_data_threads:
            t.join()
        for t in report_discounts_threads:
            t.join()
        print(f"Length of results: {len(report_data)}")
        report_data_table = PrettyTable(
            field_names=["Hotel Name", "Hotel Price", "Hotel Score"]
        )
        report_data_table.add_rows(report_data)
        report_data_table.align["Hotel Name"] = "l"
        print(report_data_table)
        print("Discounts on the searched hotels:")
        report_discounts_table = PrettyTable(
            field_names=["Hotel Name", "Current Price", "Discount"]
        )
        report_discounts_table.add_rows(report_discounts)
        report_discounts_table.align["Hotel Name"] = "l"
        print(report_discounts_table)

    def scrape_data(self, obj):
        if obj['data_name'] == "budget_range":
            return self.scrapper.get_property_price_range()
        scrapped_data = self.scrapper.get_specific_data(obj)
        return scrapped_data
    
    def wait_for_results(self):
        try:
            self.implicitly_wait(0)
            WebDriverWait(self, 10).until(
                EC.invisibility_of_element(
                    (By.CSS_SELECTOR, 'div[data-testid="skeleton-loader"]')
                )
            )
            self.implicitly_wait(const.IMPLICIT_TIME)
        except TimeoutException: 
            print('Unable to wait for all the results')
        except Exception as e:
            print(f'Error occurred: {str(e)}')
        
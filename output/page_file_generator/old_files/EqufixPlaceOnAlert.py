import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

class Equfix_Place_On_Alert:
    LOCATORS = {
        "continue_button": (By.XPATH, "//button[@id='continue-button']"),
        "zip": (By.XPATH, "//input[@id='zip']"),
        "state_dropdown": (By.XPATH, "//button[contains(@id,'efx-dropdown')]"),
        "city": (By.XPATH, "//input[@id='city']"),
        "address_line_2": (By.XPATH, "//input[@id='addressLine2Id']"),
        "address": (By.XPATH, "//input[@id='address']"),
        "phone_number": (By.XPATH, "//input[@id='phoneNumber']"),
        "ssn": (By.XPATH, "//input[@id='ssn']"),
        "dob": (By.XPATH, "//input[@id='dob']"),
        "last_name": (By.XPATH, "//input[@id='lastName']"),
        "first_name": (By.XPATH, "//input[@id='firstNameId']"),
        "state_option": (By.XPATH, "//a[contains(@id,'AK')]")
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)
        self.actions = ActionChains(self.driver)

    def wait_for_element(self, locator):
        return self.wait.until(EC.presence_of_element_located(locator))

    def click(self, locator):
        element = self.wait_for_element(locator)
        element.click()

    def enter_text(self, locator, text):
        element = self.wait_for_element(locator)
        element.clear()
        element.send_keys(text)

    def switch_to_window_by_index(self, index):
        windows = self.driver.window_handles
        if 0 <= index < len(windows):
            self.driver.switch_to.window(windows[index])
        else:
            raise RuntimeError(f"Window with index {index} does not exist.")

    def switch_to_window_by_handle(self, handle):
        if handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
        else:
            raise RuntimeError(f"Window handle {handle} not found.")

    def switch_to_window_matching_url(self, url):
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if self.driver.current_url == url:
                return
        raise RuntimeError(f"No window with URL {url} found.")

    def switch_to_new_window(self, url):
        current_handles = set(self.driver.window_handles)
        self.driver.switch_to.new_window('window')
        new_handle = list(set(self.driver.window_handles) - current_handles)
        if new_handle:
            self.driver.switch_to.window(new_handle[0])
            if self.driver.current_url != url:
                raise RuntimeError(f"Switched to a new window, but URL does not match expected {url}.")

    def click_continue_button(self):
        time.sleep(10)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        scrollable_elements = self.driver.find_elements("xpath",
                                                        "//*[contains(@style,'overflow') or contains(@class,'scroll')]")
        for el in scrollable_elements:
            try:
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", el)
                time.sleep(1)
            except Exception:
                continue
        self.driver.find_element(*self.LOCATORS["continue_button"]).click()

    def enter_zip_code(self, zip_code):
        self.enter_text(self.LOCATORS["zip"], zip_code)

    def select_state_alaska(self):
        self.click(self.LOCATORS["state_dropdown"])
        self.click(self.LOCATORS["state_option"])

    def enter_city(self, city):
        self.enter_text(self.LOCATORS["city"], city)

    def enter_address_line_2(self, address_line_2):
        self.enter_text(self.LOCATORS["address_line_2"], address_line_2)

    def enter_address(self, address):
        self.enter_text(self.LOCATORS["address"], address)

    def enter_phone_number(self, phone_number):
        self.enter_text(self.LOCATORS["phone_number"], phone_number)

    def enter_ssn(self, ssn):
        self.enter_text(self.LOCATORS["ssn"], ssn)

    def enter_dob(self, dob):
        self.enter_text(self.LOCATORS["dob"], dob)

    def enter_last_name(self, last_name):
        self.enter_text(self.LOCATORS["last_name"], last_name)

    def enter_first_name(self, first_name):
        self.enter_text(self.LOCATORS["first_name"], first_name)

    def perform_alert_placement_flow(self, ssn, last_name, phone_number, dob, address, city, address_line_2, zip_code):
        self.switch_to_window_matching_url("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/")
        self.click_continue_button()
        self.switch_to_window_matching_url("https://my.equifax.com/consumer-registration/UCSC/#/personal-info")
        self.enter_ssn(ssn)
        self.enter_last_name(last_name)
        self.enter_phone_number(phone_number)
        self.enter_dob(dob)
        self.enter_address(address)
        self.enter_city(city)
        self.enter_address_line_2(address_line_2)
        self.select_state_alaska()
        self.enter_zip_code(zip_code)
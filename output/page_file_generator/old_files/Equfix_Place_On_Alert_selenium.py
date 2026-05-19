from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class PageObjectModel:

    LOCATORS = {
        "continue_button": (By.XPATH, "//button[@id='continue-button']"),
        "zip": (By.XPATH, "//input[@id='zip']"),
        "efx_dropdown_label": (By.XPATH, "//button[@id='efx-dropdown-label-753393']"),
        "city": (By.XPATH, "//input[@id='city']"),
        "address_line2": (By.XPATH, "//input[@id='addressLine2Id']"),
        "address": (By.XPATH, "//input[@id='address']"),
        "phone_number": (By.XPATH, "//input[@id='phoneNumber']"),
        "ssn": (By.XPATH, "//input[@id='ssn']"),
        "dob": (By.XPATH, "//input[@id='dob']"),
        "last_name": (By.XPATH, "//input[@id='lastName']"),
        "first_name_id": (By.XPATH, "//input[@id='firstNameId']")
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)
        
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
        handles = self.driver.window_handles
        self.driver.switch_to.window(handles[index])

    def switch_to_window_by_handle(self, handle):
        self.driver.switch_to.window(handle)

    def switch_to_window_matching_url(self, url):
        handles = self.driver.window_handles
        for handle in handles:
            self.driver.switch_to.window(handle)
            if self.driver.current_url == url:
                return
        raise RuntimeError(f"No window found with URL: {url}")

    def switch_to_new_window(self, url=None):
        handles = self.driver.window_handles
        self.driver.switch_to.window(handles[-1])
        if url and self.driver.current_url != url:
            raise RuntimeError(f"Switched to new window, but URL is not as expected. Expected: {url}, but found: {self.driver.current_url}")

    def click_continue_button(self):
        self.click(self.LOCATORS["continue_button"])

    def enter_zip(self, text):
        self.enter_text(self.LOCATORS["zip"], text)

    def click_efx_dropdown(self):
        self.click(self.LOCATORS["efx_dropdown_label"])

    def enter_city(self, text):
        self.enter_text(self.LOCATORS["city"], text)

    def enter_address_line2(self, text):
        self.enter_text(self.LOCATORS["address_line2"], text)

    def enter_address(self, text):
        self.enter_text(self.LOCATORS["address"], text)

    def enter_phone_number(self, text):
        self.enter_text(self.LOCATORS["phone_number"], text)

    def click_ssn(self):
        self.click(self.LOCATORS["ssn"])

    def enter_ssn(self, text):
        self.enter_text(self.LOCATORS["ssn"], text)

    def click_last_name(self):
        self.click(self.LOCATORS["last_name"])

    def enter_last_name(self, text):
        self.enter_text(self.LOCATORS["last_name"], text)

    def click_phone_number(self):
        self.click(self.LOCATORS["phone_number"])

    def enter_dob(self, text):
        self.enter_text(self.LOCATORS["dob"], text)

    def click_address_line1(self):
        self.click(self.LOCATORS["address"])

    def enter_address_line1(self, text):
        self.enter_text(self.LOCATORS["address"], text)

    def click_city_name(self):
        self.click(self.LOCATORS["city"])

    def enter_city_name(self, text):
        self.enter_text(self.LOCATORS["city"], text)

    def click_address_line2(self):
        self.click(self.LOCATORS["address_line2"])

    def enter_address_line2(self, text):
        self.enter_text(self.LOCATORS["address_line2"], text)

    def click_zip_code(self):
        self.click(self.LOCATORS["zip"])

    def enter_zip_code(self, text):
        self.enter_text(self.LOCATORS["zip"], text)
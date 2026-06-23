from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Equfix_Place_On_Alert_selenium:
    LOCATORS = {
        "continue_button": (By.XPATH, "//button[@id='continue-button']"),
        "zip": (By.XPATH, "//input[@id='zip']"),
        "state_dropdown": (By.XPATH, "//button[@id='efx-dropdown-label-753393']"),
        "city": (By.XPATH, "//input[@id='city']"),
        "address_line_2": (By.XPATH, "//input[@id='addressLine2Id']"),
        "address": (By.XPATH, "//input[@id='address']"),
        "phone_number": (By.XPATH, "//input[@id='phoneNumber']"),
        "ssn": (By.XPATH, "//input[@id='ssn']"),
        "dob": (By.XPATH, "//input[@id='dob']"),
        "last_name": (By.XPATH, "//input[@id='lastName']"),
        "first_name": (By.XPATH, "//input[@id='firstNameId']")
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def wait_for_element(self, key):
        if key in self.LOCATORS:
            return self.wait.until(EC.presence_of_element_located(self.LOCATORS[key]))
        else:
            raise RuntimeError(f"Locator '{key}' not found in LOCATORS.")

    def click_element(self, key):
        element = self.wait_for_element(key)
        element.click()

    def enter_text(self, key, text):
        element = self.wait_for_element(key)
        element.clear()
        element.send_keys(text)

    def switch_to_new_window(self):
        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[-1])

    def perform_actions(self):
        self.switch_to_new_window()
        self.click_element("continue_button")
        self.enter_text("ssn", "***-**-7575")
        self.click_element("last_name")
        self.enter_text("last_name", "test")
        self.click_element("phone_number")
        self.enter_text("phone_number", "768-676-****")
        self.click_element("dob")
        self.enter_text("dob", "04/22/1990")
        self.click_element("address")
        self.enter_text("address", "test")
        self.click_element("city")
        self.enter_text("city", "test")
        self.click_element("address_line_2")
        self.enter_text("address_line_2", "test")
        self.click_element("state_dropdown")
        self.enter_text("zip", "67567")
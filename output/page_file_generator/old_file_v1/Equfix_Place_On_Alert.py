from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Equfix_Place_On_Alert:
    LOCATORS = {
        "continue_button": (By.XPATH, "//button[@id='continue-button']"),
        "zip": (By.XPATH, "//input[@id='zip']"),
        "state_dropdown": (By.XPATH, "//button[@id='efx-dropdown-label-753393']"),
        "city": (By.XPATH, "//input[@id='city']"),
        "address_line2": (By.XPATH, "//input[@id='addressLine2Id']"),
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

    def wait_for_element(self, locator_key):
        locator = self.LOCATORS.get(locator_key)
        if locator is None:
            raise RuntimeError(f"Locator '{locator_key}' not found.")
        return self.wait.until(EC.presence_of_element_located(locator))

    def click(self, locator_key):
        element = self.wait_for_element(locator_key)
        element.click()

    def enter_text(self, locator_key, text):
        element = self.wait_for_element(locator_key)
        element.clear()
        element.send_keys(text)

    def switch_to_window_by_index(self, index):
        all_windows = self.driver.window_handles
        if index >= len(all_windows):
            raise RuntimeError(f"Invalid index: {index}. Total open windows: {len(all_windows)}.")
        self.driver.switch_to.window(all_windows[index])

    def switch_to_window_by_handle(self, handle):
        all_windows = self.driver.window_handles
        if handle not in all_windows:
            raise RuntimeError(f"Window handle '{handle}' not found.")
        self.driver.switch_to.window(handle)

    def switch_to_window_matching_url(self, url):
        all_windows = self.driver.window_handles
        for handle in all_windows:
            self.driver.switch_to.window(handle)
            if self.driver.current_url == url:
                return
        raise RuntimeError(f"No window found with URL '{url}'.")

    def switch_to_new_window(self, url):
        current_windows = set(self.driver.window_handles)
        self.wait.until(lambda driver: len(set(driver.window_handles) - current_windows) > 0)
        new_windows = set(self.driver.window_handles) - current_windows
        if not new_windows:
            raise RuntimeError("No new window appeared.")
        new_window_handle = new_windows.pop()
        self.driver.switch_to.window(new_window_handle)
        if self.driver.current_url != url:
            raise RuntimeError(f"Expected URL '{url}', but found '{self.driver.current_url}'.")

    def switch_to_personal_credit_fraud_page(self):
        self.switch_to_new_window("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/")

    def fill_first_name(self, first_name):
        self.wait_for_element("first_name")
        self.enter_text("first_name", first_name)

    def fill_last_name(self, last_name):
        self.wait_for_element("last_name")
        self.click("last_name")
        self.enter_text("last_name", last_name)

    def fill_ssn(self, ssn_text):
        self.wait_for_element("ssn")

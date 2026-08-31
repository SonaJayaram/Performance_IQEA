from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class CheckoutStepOne:
    LOCATORS = {
        "first_name_input": (By.XPATH, "//input[@id='first-name']"),
        "last_name_input": (By.XPATH, "//input[@id='last-name']"),
        "postal_code_input": (By.XPATH, "//input[@id='postal-code']"),
        "cancel_button": (By.XPATH, "//button[@id='cancel']"),
        "continue_button": (By.XPATH, "//input[@id='continue']"),
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def navigate(self):
        self.driver.get("https://www.saucedemo.com/")

    def get_first_name_input(self):
        locator = self.LOCATORS.get("first_name_input")
        if locator is None:
            raise RuntimeError("Locator 'first_name_input' not found in LOCATORS")
        return self.wait.until(EC.visibility_of_element_located(locator))

    def get_last_name_input(self):
        locator = self.LOCATORS.get("last_name_input")
        if locator is None:
            raise RuntimeError("Locator 'last_name_input' not found in LOCATORS")
        return self.wait.until(EC.visibility_of_element_located(locator))

    def get_postal_code_input(self):
        locator = self.LOCATORS.get("postal_code_input")
        if locator is None:
            raise RuntimeError("Locator 'postal_code_input' not found in LOCATORS")
        return self.wait.until(EC.visibility_of_element_located(locator))

    def get_cancel_button(self):
        locator = self.LOCATORS.get("cancel_button")
        if locator is None:
            raise RuntimeError("Locator 'cancel_button' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def get_continue_button(self):
        locator = self.LOCATORS.get("continue_button")
        if locator is None:
            raise RuntimeError("Locator 'continue_button' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def enter_first_name(self, first_name: str):
        self.get_first_name_input().clear()
        self.get_first_name_input().send_keys(first_name)

    def enter_last_name(self, last_name: str):
        self.get_last_name_input().clear()
        self.get_last_name_input().send_keys(last_name)

    def enter_postal_code(self, postal_code: str):
        self.get_postal_code_input().clear()
        self.get_postal_code_input().send_keys(postal_code)

    def click_continue(self):
        self.get_continue_button().click()

    def switch_to_new_window(self, timeout: int = 10):
        import time
        deadline = time.time() + timeout
        while time.time() < deadline:
            if len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                return
            time.sleep(0.5)
        raise RuntimeError("New window did not appear within timeout")

    def switch_to_main_window(self):
        self.driver.switch_to.window(self.driver.window_handles[0])
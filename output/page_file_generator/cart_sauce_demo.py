from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class CartSauceDemo:
    LOCATORS = {
        "remove_sauce_labs_backpack_button": (By.XPATH, "//button[@id='remove-sauce-labs-backpack']"),
        "remove_sauce_labs_bike_light_button": (By.XPATH, "//button[@id='remove-sauce-labs-bike-light']"),
        "continue_shopping_button": (By.XPATH, "//button[@id='continue-shopping']"),
        "checkout_button": (By.XPATH, "//button[@id='checkout']"),
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def navigate(self):
        self.driver.get("https://www.saucedemo.com/")

    def get_remove_sauce_labs_backpack_button(self):
        locator = self.LOCATORS.get("remove_sauce_labs_backpack_button")
        if locator is None:
            raise RuntimeError("Locator 'remove_sauce_labs_backpack_button' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def get_remove_sauce_labs_bike_light_button(self):
        locator = self.LOCATORS.get("remove_sauce_labs_bike_light_button")
        if locator is None:
            raise RuntimeError("Locator 'remove_sauce_labs_bike_light_button' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def get_continue_shopping_button(self):
        locator = self.LOCATORS.get("continue_shopping_button")
        if locator is None:
            raise RuntimeError("Locator 'continue_shopping_button' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def get_checkout_button(self):
        locator = self.LOCATORS.get("checkout_button")
        if locator is None:
            raise RuntimeError("Locator 'checkout_button' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def click_remove_sauce_labs_backpack_button(self):
        self.get_remove_sauce_labs_backpack_button().click()

    def click_remove_sauce_labs_bike_light_button(self):
        self.get_remove_sauce_labs_bike_light_button().click()

    def click_continue_shopping(self):
        self.get_continue_shopping_button().click()

    def click_checkout(self):
        self.get_checkout_button().click()

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
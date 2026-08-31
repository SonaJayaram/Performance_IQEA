from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class CheckoutComplete:
    LOCATORS = {
        "back_to_products_button": (By.XPATH, "//button[@id='back-to-products']"),
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def navigate(self):
        self.driver.get("https://www.saucedemo.com/")

    def get_back_to_products_button(self):
        locator = self.LOCATORS.get("back_to_products_button")
        if locator is None:
            raise RuntimeError("Locator 'back_to_products_button' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def click_back_to_products(self):
        self.get_back_to_products_button().click()

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
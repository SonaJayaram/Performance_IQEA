from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class CheckoutStepTwo:
    LOCATORS = {
        "cancel_button": (By.XPATH, "//button[@id='cancel']"),
        "finish_button": (By.XPATH, "//button[@id='finish']"),
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def navigate(self):
        self.driver.get("https://www.saucedemo.com/")

    def get_cancel_button(self):
        locator = self.LOCATORS.get("cancel_button")
        if locator is None:
            raise RuntimeError("Locator 'cancel_button' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def get_finish_button(self):
        locator = self.LOCATORS.get("finish_button")
        if locator is None:
            raise RuntimeError("Locator 'finish_button' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def click_finish(self):
        self.get_finish_button().click()

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
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
class HomeLogoutSauceDemo:
    LOCATORS = {
        "logout_sidebar_link": (By.XPATH, "//a[@id='logout_sidebar_link']"),
        "reset_sidebar_link": (By.XPATH, "//a[@id='reset_sidebar_link']"),
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def navigate(self):
        self.driver.get("https://www.saucedemo.com/")

    def get_logout_sidebar_link(self):
        locator = self.LOCATORS.get("logout_sidebar_link")
        if locator is None:
            raise RuntimeError("Locator 'logout_sidebar_link' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def get_reset_sidebar_link(self):
        locator = self.LOCATORS.get("reset_sidebar_link")
        if locator is None:
            raise RuntimeError("Locator 'reset_sidebar_link' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def click_logout_sidebar_link(self):
        self.get_logout_sidebar_link().click()

    def change_logout_sidebar_link_value(self, value: str):
        self.get_logout_sidebar_link().click()

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
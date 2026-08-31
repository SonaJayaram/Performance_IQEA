from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ApSauce:
    LOCATORS = {
        "username_input": (By.XPATH, "//input[@id='user-name']"),
        "password_input": (By.XPATH, "//input[@id='password']"),
        "login_button": (By.XPATH, "//input[@id='login-button']"),
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def navigate(self):
        self.driver.get("https://www.saucedemo.com/")

    def get_username_input(self):
        locator = self.LOCATORS.get("username_input")
        if locator is None:
            raise RuntimeError("Locator 'username_input' not found in LOCATORS")
        return self.wait.until(EC.visibility_of_element_located(locator))

    def get_password_input(self):
        locator = self.LOCATORS.get("password_input")
        if locator is None:
            raise RuntimeError("Locator 'password_input' not found in LOCATORS")
        return self.wait.until(EC.visibility_of_element_located(locator))

    def get_login_button(self):
        locator = self.LOCATORS.get("login_button")
        if locator is None:
            raise RuntimeError("Locator 'login_button' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def enter_username(self, username: str):
        self.get_username_input().clear()
        self.get_username_input().send_keys(username)

    def enter_password(self, password: str):
        self.get_password_input().clear()
        self.get_password_input().send_keys(password)

    def click_login(self):
        self.get_login_button().click()

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
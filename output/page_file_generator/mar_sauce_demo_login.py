from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class mar_sauce_demo_login:
    LOCATORS = {
        "user_name_input": (By.XPATH, "//input[@id='user-name']"),
        "password_input": (By.XPATH, "//input[@id='password']"),
        "login_button": (By.XPATH, "//input[@id='login-button']"),
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def get_user_name_input(self):
        key = "user_name_input"
        if key not in self.LOCATORS:
            raise RuntimeError(f"Locator '{key}' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(self.LOCATORS[key]))

    def get_password_input(self):
        key = "password_input"
        if key not in self.LOCATORS:
            raise RuntimeError(f"Locator '{key}' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(self.LOCATORS[key]))

    def get_login_button(self):
        key = "login_button"
        if key not in self.LOCATORS:
            raise RuntimeError(f"Locator '{key}' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(self.LOCATORS[key]))
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class sauce_demo_login_page:
    LOCATORS = {
        "user_name_input": (By.XPATH, "//input[@id='user-name']"),
        "password_input": (By.XPATH, "//input[@id='password']"),
        "login_button": (By.XPATH, "//input[@id='login-button']")
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def get_user_name_input(self):
        if "user_name_input" not in self.LOCATORS:
            raise RuntimeError("Locator 'user_name_input' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(self.LOCATORS["user_name_input"]))

    def get_password_input(self):
        if "password_input" not in self.LOCATORS:
            raise RuntimeError("Locator 'password_input' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(self.LOCATORS["password_input"]))

    def get_login_button(self):
        if "login_button" not in self.LOCATORS:
            raise RuntimeError("Locator 'login_button' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(self.LOCATORS["login_button"]))
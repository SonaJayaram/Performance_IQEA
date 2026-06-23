from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

LOCATORS = {
    "username_input": (By.XPATH, "//*[@id='user-name']"),
    "password_input": (By.XPATH, "//input[@id='password']"),
    "login_button": (By.XPATH, "//*[@id='login-button']"),
}

class mar_19_suce:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def get_username_input(self):
        if "username_input" not in LOCATORS:
            raise RuntimeError("Locator 'username_input' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(LOCATORS["username_input"]))

    def get_password_input(self):
        if "password_input" not in LOCATORS:
            raise RuntimeError("Locator 'password_input' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(LOCATORS["password_input"]))

    def get_login_button(self):
        if "login_button" not in LOCATORS:
            raise RuntimeError("Locator 'login_button' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(LOCATORS["login_button"]))
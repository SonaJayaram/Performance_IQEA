from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class sauce_demo_new_login:
    def __init__(self, driver):
        self.driver = driver
        self.user_name_input = (By.ID, 'user-name')
        self.password_input = (By.ID, 'password')
        self.login_button = (By.ID, 'login-button')

    def get_user_name_input(self):
        return WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located(self.user_name_input))

    def get_password_input(self):
        return WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located(self.password_input))

    def get_login_button(self):
        return WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.login_button))
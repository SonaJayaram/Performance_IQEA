from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class mckesson_Glove_Liners:
    def __init__(self, driver):
        self.driver = driver
        self.accept_cookies_button = (By.ID, "accept-cookies")
        self.glove_liner_flow_button = (By.XPATH, "//a[contains(text(), 'Glove Liners')]")

    def accept_cookies(self):
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.accept_cookies_button)).click()

    def click_glove_liner_flow(self):
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.glove_liner_flow_button)).click()

    def get_element(self, locator):
        return WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(locator))
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class mckesson_compression_gloves:
    def __init__(self, driver):
        self.driver = driver
        self.accept_cookies_button = (By.ID, "accept-cookies")
        self.compression_gloves_page = (By.XPATH, "//a[contains(text(), 'Compression Gloves')]")

    def get_accept_cookies_button(self):
        return WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.accept_cookies_button))

    def open_compression_gloves_page(self):
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.compression_gloves_page)).click()

    def get_element(self, locator):
        return WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(locator))
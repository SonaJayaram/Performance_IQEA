from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class mckesson_exam_gloves:
    def __init__(self, driver):
        self.driver = driver
        self.accept_cookies_button = (By.ID, "accept-cookies")
        self.gloves_link = (By.XPATH, "//a[contains(text(), 'Gloves')]")
        self.exam_gloves_link = (By.XPATH, "//a[contains(text(), 'Exam Gloves')]")

    def get_accept_cookies_button(self):
        return WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.accept_cookies_button))

    def get_gloves_link(self):
        return WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.gloves_link))

    def get_exam_gloves_link(self):
        return WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.exam_gloves_link))

    def get_element(self, locator):
        return WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(locator))
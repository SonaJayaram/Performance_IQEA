from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Mckesson_home_1:
    def __init__(self, driver):
        self.driver = driver
        self.glove_button = (By.XPATH, "//a[contains(text(), 'Gloves')]")

    def click_glove(self):

        self.driver
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.glove_button)).click()

    def get_element(self, locator):
        return WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(locator))
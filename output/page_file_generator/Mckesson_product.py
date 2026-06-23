from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Mckesson_product:
    def __init__(self, driver):
        self.driver = driver

    def get_element(self, xpath):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
        return self.driver.find_element(By.XPATH, xpath)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Mckesson_compare:
    def __init__(self, driver):
        self.driver = driver
        self.compare_button = "//button[@id='compare-button']"
        self.compare_products_link = "//a[@id='compare-products-link']"

    def get_compare_button(self):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self.compare_button)))
        return self.driver.find_element(By.XPATH, self.compare_button)

    def get_compare_products_link(self):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self.compare_products_link)))
        return self.driver.find_element(By.XPATH, self.compare_products_link)
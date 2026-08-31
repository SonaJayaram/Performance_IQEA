from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Mckesson_Home:
    def __init__(self, driver):
        self.driver = driver
        self.search_icon = "//li//i[@class='fas fa-search']"
        self.search_input = "(//input[contains(@placeholder,'What can we help you find?')])[2]"
        self.search_button = "(//span[@class='fas fa-search'])[2]"
        self.compare_button_first = "(//a[contains(text(), 'Compare')])[4]"
        self.compare_button_second = "(//a[contains(text(), 'Compare')])[5]"
        self.compare_products = "//a[@id='compare-products-link']"
        self.glove_button="//a[contains(text(),'Gloves')]"

    def get_search_icon(self):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self.search_icon)))
        return self.driver.find_element(By.XPATH, self.search_icon)

    def get_search_input(self):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self.search_input)))
        return self.driver.find_element(By.XPATH, self.search_input)

    def get_gloves_button(self):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self.glove_button)))
        return self.driver.find_element(By.XPATH, self.glove_button)
    def get_search_button(self):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self.search_button)))
        return self.driver.find_element(By.XPATH, self.search_button)

    def get_compare_button_first(self):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self.compare_button_first)))
        return self.driver.find_element(By.XPATH, self.compare_button_first)

    def get_compare_button_second(self):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self.compare_button_second)))
        return self.driver.find_element(By.XPATH, self.compare_button_second)

    def get_compare_products(self):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self.compare_products)))
        return self.driver.find_element(By.XPATH, self.compare_products)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class mckesson_compression_gloves:
    LOCATORS = {
        "all_products_link": (By.XPATH, "//a[text()='All Products (99)']"),
        "privacy_statement_link": (By.XPATH, "//a[text()='More information about your privacy, opens in a new tab']"),
        "accept_cookies_button": (By.XPATH, "//button[@id='onetrust-accept-btn-handler']"),
        "gloves_category_link": (By.XPATH, "//a[text()='Gloves']"),
        "compression_gloves_link": (By.XPATH, "//a[text()='Compression Gloves (99)']"),
        "exam_gloves_link": (By.XPATH, "//a[text()='Exam Gloves (828)']"),
        "finger_cots_link": (By.XPATH, "//a[text()='Finger Cots (17)']"),
        "glove_liners_link": (By.XPATH, "//a[text()='Glove Liners (57)']"),
        "beige_gloves_link": (By.XPATH, "//a[text()='Beige (1)']")
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def get_element(self, key):
        locator = self.LOCATORS.get(key)
        if not locator:
            raise RuntimeError(f"Locator '{key}' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def open_compression_gloves_page(self):
        self.get_element("gloves_category_link").click()
        self.get_element("compression_gloves_link").click()
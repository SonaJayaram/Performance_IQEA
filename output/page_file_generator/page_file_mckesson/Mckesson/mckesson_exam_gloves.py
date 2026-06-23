from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class mckesson_exam_gloves:
    LOCATORS = {
        "all_products_link": (By.XPATH, "//a[text()='All Products (828)']"),
        "privacy_statement_link": (By.XPATH, "//a[contains(text(), 'More information about your privacy')]"),
        "accept_cookies_button": (By.XPATH, "//button[@id='onetrust-accept-btn-handler']"),
        "gloves_link": (By.XPATH, "//a[text()='Gloves']"),
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
        if key not in self.LOCATORS:
            raise RuntimeError(f"Locator '{key}' not found in LOCATORS")
        return self.wait.until(EC.presence_of_element_located(self.LOCATORS[key]))

    def get_all_products_link(self):
        return self.get_element("all_products_link")

    def get_privacy_statement_link(self):
        return self.get_element("privacy_statement_link")

    def get_accept_cookies_button(self):
        return self.get_element("accept_cookies_button")

    def get_gloves_link(self):
        return self.get_element("gloves_link")

    def get_compression_gloves_link(self):
        return self.get_element("compression_gloves_link")

    def get_exam_gloves_link(self):
        return self.get_element("exam_gloves_link")

    def get_finger_cots_link(self):
        return self.get_element("finger_cots_link")

    def get_glove_liners_link(self):
        return self.get_element("glove_liners_link")

    def get_beige_gloves_link(self):
        return self.get_element("beige_gloves_link")
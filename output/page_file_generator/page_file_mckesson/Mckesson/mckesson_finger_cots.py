from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class mckesson_finger_cots:
    LOCATORS = {
        "all_products": (By.XPATH, "//a[text()='All Products (17)']"),
        "privacy_statement": (
            By.XPATH,
            "//a[@aria-label='More information about your privacy, opens in a new tab']",
        ),
        "accept_cookies": (By.ID, "onetrust-accept-btn-handler"),
        "gloves": (By.XPATH, "//a[text()='Gloves']"),
        "compression_gloves": (
            By.XPATH,
            "//a[text()='Compression Gloves (99)']",
        ),
        "exam_gloves": (By.XPATH, "//a[text()='Exam Gloves (828)']"),
        "finger_cots": (By.XPATH, "//a[text()='Finger Cots (17)']"),
        "glove_liners": (By.XPATH, "//a[text()='Glove Liners (57)']"),
        "beige": (By.XPATH, "//a[text()='Beige (1)']"),
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def get_element(self, key):
        if key not in self.LOCATORS:
            raise RuntimeError(f"Locator '{key}' not found in LOCATORS")
        return self.wait.until(EC.presence_of_element_located(self.LOCATORS[key]))

    def switch_to_new_window(self):
        self.driver.switch_to.window(self.driver.window_handles[-1])
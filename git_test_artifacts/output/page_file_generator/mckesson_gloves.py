from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class mckesson_gloves:

    LOCATORS = {
        "compression_gloves": (By.XPATH, "//a[text()='Compression Gloves (99)']"),
        "exam_gloves": (By.XPATH, "//a[text()='Exam Gloves (828)']"),
        "finger_cots": (By.XPATH, "//a[text()='Finger Cots (17)']"),
        "glove_liners": (By.XPATH, "//a[text()='Glove Liners (57)']")
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def get_element(self, key):
        if key not in self.LOCATORS:
            raise RuntimeError(f"Locator '{key}' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(self.LOCATORS[key]))
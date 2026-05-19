from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class mckesson_Glove_Liners:
    LOCATORS = {
        "beige_option": (By.XPATH, "//a[text()='Beige (1)']"),
        "all_products_option": (By.XPATH, "//a[text()='All Products (57)']"),
        "privacy_statement": (By.XPATH, "//a[contains(@aria-label, 'More information about your privacy, opens in a new tab')]"),
        "accept_cookies_button": (By.XPATH, "//button[@id='onetrust-accept-btn-handler']"),
        "gloves_category": (By.XPATH, "//a[text()='Gloves']"),
        "compression_gloves": (By.XPATH, "//a[text()='Compression Gloves (99)']"),
        "exam_gloves": (By.XPATH, "//a[text()='Exam Gloves (828)']"),
        "finger_cots": (By.XPATH, "//a[text()='Finger Cots (17)']"),
        "glove_liners": (By.XPATH, "//a[text()='Glove Liners (57)']"),
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def get_element(self, key):
        if key not in self.LOCATORS:
            raise RuntimeError(f"Locator '{key}' not found in LOCATORS")
        return self.wait.until(EC.presence_of_element_located(self.LOCATORS[key]))

    def switch_to_new_window(self):
        current_window = self.driver.current_window_handle
        all_windows = self.driver.window_handles
        for window in all_windows:
            if window != current_window:
                self.driver.switch_to.window(window)
                break

    def accept_cookies(self):
        self.get_element("accept_cookies_button").click()

    def click_glove_liner_flow(self):
        self.get_element("gloves_category").click()
        self.get_element("glove_liners").click()
        self.get_element("beige_option").click()
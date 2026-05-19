from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Equfix_home_page_selenium:
    LOCATORS = {
        "place_an_alert_btn": (By.XPATH, "//a[contains(@class, 'btn') and text()='PLACE AN ALERT']"),
        "close_btn": (By.XPATH, "//button[@name='close']")
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def wait_for_element(self, locator_key):
        if locator_key not in self.LOCATORS:
            raise RuntimeError(f"Locator for '{locator_key}' not found.")
        return self.wait.until(EC.presence_of_element_located(self.LOCATORS[locator_key]))

    def click_element(self, locator_key):
        element = self.wait_for_element(locator_key)
        element.click()

    def enter_text(self, locator_key, text):
        element = self.wait_for_element(locator_key)
        element.clear()
        element.send_keys(text)

    def switch_to_new_window(self):
        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[-1])

    def place_an_alert(self):
        self.switch_to_new_window()
        self.click_element("place_an_alert_btn")
        alert_btn = self.wait_for_element("place_an_alert_btn")
        self.enter_text("place_an_alert_btn", "PLACE AN ALERT")
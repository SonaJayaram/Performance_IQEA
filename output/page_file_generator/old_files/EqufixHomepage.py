from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver


class Equfix_home_page:
    LOCATORS = {
        "place_an_alert": (By.XPATH, "//a[contains(@class, 'btn') and text()='PLACE AN ALERT']"),
        "close_button": (By.XPATH, "//button[@name='close']")
    }

    def __init__(self, driver: WebDriver, timeout: int = 10):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def wait_for_element(self, locator):
        return self.wait.until(EC.presence_of_element_located(locator))

    def click(self, locator):
        self.wait_for_element(locator).click()

    def enter_text(self, locator, text):
        element = self.wait_for_element(locator)
        element.clear()
        element.send_keys(text)

    def switch_to_window_by_index(self, index: int):
        window_handles = self.driver.window_handles
        if index < len(window_handles):
            self.driver.switch_to.window(window_handles[index])
        else:
            raise IndexError(f"Index {index} is out of range for available windows.")

    def switch_to_window_by_handle(self, handle: str):
        self.driver.switch_to.window(handle)

    def switch_to_window_matching_url(self, url: str):
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if self.driver.current_url == url:
                return
        raise RuntimeError(f"No window found matching URL: {url}")

    def switch_to_new_window(self, expected_url: str = None):
        all_window_handles = self.driver.window_handles
        if len(all_window_handles) > 1:
            self.driver.switch_to.window(all_window_handles[-1])

    def click_place_an_alert(self):
        # Click the 'Place an Alert' button
        self.click(self.LOCATORS["place_an_alert"])

        # Wait for the new tab/window or page load to complete
        WebDriverWait(self.driver, 15).until(
            lambda d: len(d.window_handles) > 1 or d.execute_script("return document.readyState") == "complete"
        )


    def click_close_button(self):
        self.click(self.LOCATORS["close_button"])

    def perform_equifax_home_page_flow(self):
        # Derived from user actions
        # Switch to the new window
        self.switch_to_new_window("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/")
        # Click "Place an Alert" button
        self.click_place_an_alert()
        # Note: Changing the button text dynamically is not typical. Ignoring that step. 

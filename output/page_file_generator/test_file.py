from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

class GPA_Login:
    LOCATORS = {
        "userid_input": (By.XPATH, "//input[@id='userid']"),
        "identifier_field": (By.XPATH, "//input[@id='identifier']"),
        "submit_button": (By.XPATH, "//button[@id='submit']"),
        "credentials_passcode_field": (By.XPATH, "//input[@id='credentials.passcode']"),
        "verify_button": (By.XPATH, "//button[text()='Verify']"),
        "security_question_answer_field": (By.XPATH, "//input[@id='credentials.answer']")
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

    def wait_for_element(self, locator):
        return self.wait.until(EC.presence_of_element_located(locator))

    def click(self, locator):
        element = self.wait_for_element(locator)
        element.click()

    def enter_text(self, locator, text):
        element = self.wait_for_element(locator)
        element.clear()
        element.send_keys(text)

    def switch_to_window_by_index(self, index):
        handles = self.driver.window_handles
        if index < len(handles):
            self.driver.switch_to.window(handles[index])
        else:
            raise RuntimeError(f"Window index {index} out of range.")

    def switch_to_window_by_handle(self, handle):
        self.driver.switch_to.window(handle)

    def switch_to_window_matching_url(self, url):
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if self.driver.current_url == url:
                return
        raise RuntimeError(f"No window found with URL: {url}")

    def switch_to_new_window(self, url=None):
        handles_before = set(self.driver.window_handles)
        self.wait.until(lambda driver: len(driver.window_handles) > len(handles_before))
        new_handles = set(self.driver.window_handles) - handles_before
        if new_handles:
            self.driver.switch_to.window(new_handles.pop())
            if url and self.driver.current_url != url:
                raise RuntimeError(f"Switched to a new window, but URL does not match. Expected: {url}, Found: {self.driver.current_url}")

    def enter_userid(self, userid):
        self.wait_for_element(self.LOCATORS["userid_input"])
        self.enter_text(self.LOCATORS["userid_input"], userid)

    def click_identifier_field(self):
        self.wait_for_element(self.LOCATORS["identifier_field"])
        self.click(self.LOCATORS["identifier_field"])

    def enter_identifier(self, identifier):
        self.wait_for_element(self.LOCATORS["identifier_field"])
        self.enter_text(self.LOCATORS["identifier_field"], identifier)

    def click_submit_button(self):
        self.wait_for_element(self.LOCATORS["submit_button"])
        self.click(self.LOCATORS["submit_button"])

    def enter_credentials_passcode(self, passcode):
        self.wait_for_element(self.LOCATORS["credentials_passcode_field"])
        self.enter_text(self.LOCATORS["credentials_passcode_field"], passcode)

    def click_verify_button(self):
        self.wait_for_element(self.LOCATORS["verify_button"])
        self.click(self.LOCATORS["verify_button"])

    def enter_security_question_answer(self, answer):
        self.wait_for_element(self.LOCATORS["security_question_answer_field"])
        self.enter_text(self.LOCATORS["security_question_answer_field"], answer)

    def perform_login_flow(self, userid, identifier, passcode, security_answer):
        self.enter_userid(userid)
        self.click_identifier_field()
        self.enter_identifier(identifier)
        self.click_submit_button()
        self.enter_credentials_passcode(passcode)
        self.click_submit_button()
        self.enter_security_question_answer(security_answer)
        self.click_verify_button()
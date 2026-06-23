import time

from playwright.sync_api import Page, Locator

class sfdc_homepage:
    def __init__(self, page: Page):
        self.page = page
        self.username_field = page.locator("xpath=//input[@id='username']")
        self.password_field = page.locator("xpath=//input[@id='password']")
        self.login_button = page.locator("xpath=//input[@id='Login']")
        self.verification_code_field = page.locator("xpath=//input[@id='emc']")
        self.verify_button = page.locator("xpath=//input[@id='save']")
        self.contacts_tab = page.locator("xpath=//span[text()='Contacts']")

    def wait_for_element(self, locator_key: str):
        if not hasattr(self, locator_key):
            raise RuntimeError(f"Locator '{locator_key}' not defined.")
        getattr(self, locator_key).wait_for()

    def enter_text(self, locator_key: str, text: str):
        self.wait_for_element(locator_key)
        getattr(self, locator_key).fill(text)

    def click_element(self, locator_key: str):
        self.wait_for_element(locator_key)
        getattr(self, locator_key).click()

    def switch_to_new_window(self):
        pages = self.page.context.pages
        if len(pages) > 1:
            return pages[-1]
        return self.page

    def login(self, username: str, password: str):
        self.enter_text('username_field', username)
        self.enter_text('password_field', password)
        self.click_element('login_button')
        # Save authentication state


    def verify_identity(self, verification_code: str):
        new_page = self.switch_to_new_window()
        new_page.locator("xpath=//input[@id='emc']").wait_for()
        self.verification_code_field = new_page.locator("xpath=//input[@id='emc']")
        self.verify_button = new_page.locator("xpath=//input[@id='save']")
        #self.enter_text('verification_code_field', verification_code)
        time.sleep(20)
        self.click_element('verify_button')

    def click_contacts_tab(self):
        self.click_element('contacts_tab')
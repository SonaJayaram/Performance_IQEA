from playwright.sync_api import Page, Locator

class sfdc_otp:
    def __init__(self, page: Page):
        self.page = page
        self.username_field = page.locator("xpath=//input[@type='text']")
        self.password_field = page.locator("xpath=//input[@type='text']")
        self.login_button = page.locator("xpath=//input[@type='submit']")
        self.verification_code_field = page.locator("xpath=//input[@type='text']")
        self.verify_button = page.locator("xpath=//input[@type='submit']")
    
    def wait_for_element(self, locator: Locator):
        locator.wait_for()

    def click_element(self, locator: Locator):
        self.wait_for_element(locator)
        locator.click()

    def enter_text(self, locator: Locator, text: str):
        self.wait_for_element(locator)
        locator.fill(text)

    def switch_to_new_window(self):
        pages = self.page.context.pages
        if len(pages) > 1:
            return pages[-1]
        return self.page

    def login(self, username: str, password: str):
        if not self.username_field or not self.password_field or not self.login_button:
            raise RuntimeError("Required locators for login are missing.")
        self.enter_text(self.username_field, username)
        self.enter_text(self.password_field, password)
        self.click_element(self.login_button)

    def enter_verification_code(self, verification_code: str):
        new_page = self.switch_to_new_window()
        verification_code_field = new_page.locator("xpath=//input[@type='text']")
        verify_button = new_page.locator("xpath=//input[@type='submit']")
        if not verification_code_field or not verify_button:
            raise RuntimeError("Required locators for verification are missing.")
        self.enter_text(verification_code_field, verification_code)
        self.click_element(verify_button)
from playwright.sync_api import Page, Locator

class Sfdc_login:
    def __init__(self, page: Page):
        self.page = page
        self.username_field = page.locator("xpath=//input[@id='username']")
        self.password_field = page.locator("xpath=//input[@id='password']")
        self.login_button = page.locator("xpath=//input[@id='Login']")

    def wait_for_element(self, locator_key: str):
        if not hasattr(self, locator_key):
            raise RuntimeError(f"Locator key '{locator_key}' not found.")
        getattr(self, locator_key).wait_for()

    def enter_text(self, locator_key: str, text: str):
        if not hasattr(self, locator_key):
            raise RuntimeError(f"Locator key '{locator_key}' not found.")
        getattr(self, locator_key).fill(text)

    def click_element(self, locator_key: str):
        if not hasattr(self, locator_key):
            raise RuntimeError(f"Locator key '{locator_key}' not found.")
        getattr(self, locator_key).click()

    def switch_to_new_window(self):
        pages = self.page.context.pages
        if len(pages) > 1:
            return pages[-1]
        return self.page

    def login(self, username: str, password: str):
        self.wait_for_element("username_field")
        self.enter_text("username_field", username)
        self.wait_for_element("password_field")
        self.enter_text("password_field", password)
        self.wait_for_element("login_button")
        self.click_element("login_button")
        return self.switch_to_new_window()
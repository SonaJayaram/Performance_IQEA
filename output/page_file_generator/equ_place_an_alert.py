from playwright.sync_api import Page, Locator

class equ_place_an_alert:
    def __init__(self, page: Page):
        self.page = page
        self.last_name = page.locator("xpath=//input[@id='lastName']")
        self.dob = page.locator("xpath=//input[@id='dob']")
        self.close_button = page.locator("xpath=//button[@class='close']")
        self.continue_button = page.locator("xpath=//button[@id='continue-button']")
        self.zip_code = page.locator("xpath=//input[@id='zip']")
    
    def wait_for_element(self, key: str):
        locator = getattr(self, key, None)
        if not locator:
            raise RuntimeError(f"Locator '{key}' is not defined in the page object.")
        locator.wait_for()
    
    def click_element(self, key: str):
        self.wait_for_element(key)
        locator = getattr(self, key)
        locator.click()

    def enter_text(self, key: str, text: str):
        self.wait_for_element(key)
        locator = getattr(self, key)
        locator.fill(text)
    
    def switch_to_new_window(self):
        pages = self.page.context.pages
        if len(pages) > 1:
            return pages[-1]
        return self.page
    
    def perform_actions(self):
        self.switch_to_new_window()
        self.click_element("last_name")
        self.enter_text("last_name", "test")
        self.enter_text("dob", "04/22/1990")
        self.enter_text("zip_code", "67567")
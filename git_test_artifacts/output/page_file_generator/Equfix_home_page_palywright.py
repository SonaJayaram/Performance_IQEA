from playwright.sync_api import Page, Locator

class Equfix_home_page_palywright:
    def __init__(self, page: Page):
        self.page = page
        self.place_an_alert_btn = page.locator("xpath=//a[contains(@class, 'btn') and text()='PLACE AN ALERT']")
        self.close_button = page.locator("xpath=//button[@name='close']")

    def wait_for_element(self, locator_key: str):
        if not hasattr(self, locator_key):
            raise RuntimeError(f"Locator '{locator_key}' is not defined in the page object model.")
        locator: Locator = getattr(self, locator_key)
        locator.wait_for()

    def click_element(self, locator_key: str):
        self.wait_for_element(locator_key)
        locator: Locator = getattr(self, locator_key)
        locator.click()

    def switch_to_new_window(self):
        pages = self.page.context.pages
        if len(pages) > 1:
            return pages[-1]
        return self.page

    def place_an_alert(self):
        self.click_element('place_an_alert_btn')

    def close_alert(self):
        self.click_element('close_button')
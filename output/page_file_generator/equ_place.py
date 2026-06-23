from playwright.sync_api import Page, Locator

class equ_place:
    def __init__(self, page: Page):
        self.page = page
        self.first_name_id = page.locator("xpath=//input[@id='firstNameId']")
        self.last_name = page.locator("xpath=//input[@id='lastName']")
        self.dob = page.locator("xpath=//input[@id='dob']")
    
    def wait_for_element(self, locator: Locator):
        if not locator:
            raise RuntimeError("Locator not provided for wait_for_element.")
        locator.wait_for()

    def click_element(self, locator: Locator):
        if not locator:
            raise RuntimeError("Locator not provided for click_element.")
        self.wait_for_element(locator)
        locator.click()

    def enter_text(self, locator: Locator, text: str):
        if not locator:
            raise RuntimeError("Locator not provided for enter_text.")
        self.wait_for_element(locator)
        locator.fill(text)

    def switch_to_new_window(self):
        pages = self.page.context.pages
        if len(pages) > 1:
            return pages[-1]
        return self.page

    def enter_first_name(self, text: str):
        self.enter_text(self.first_name_id, text)

    def enter_last_name(self, text: str):
        self.enter_text(self.last_name, text)

    def enter_dob(self, text: str):
        self.enter_text(self.dob, text)
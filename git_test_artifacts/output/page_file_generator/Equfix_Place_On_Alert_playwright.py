from playwright.sync_api import Page, Locator

class Equfix_Place_On_Alert_playwright:
    def __init__(self, page: Page):
        self.page = page
        self.continue_button = page.locator("xpath=//button[@id='continue-button']")
        self.zip = page.locator("xpath=//input[@id='zip']")
        self.efx_dropdown_label = page.locator("xpath=//button[@id='efx-dropdown-label-753393']")
        self.city = page.locator("xpath=//input[@id='city']")
        self.address_line_2 = page.locator("xpath=//input[@id='addressLine2Id']")
        self.address = page.locator("xpath=//input[@id='address']")
        self.phone_number = page.locator("xpath=//input[@id='phoneNumber']")
        self.ssn = page.locator("xpath=//input[@id='ssn']")
        self.dob = page.locator("xpath=//input[@id='dob']")
        self.last_name = page.locator("xpath=//input[@id='lastName']")
        self.first_name_id = page.locator("xpath=//input[@id='firstNameId']")

    def wait_for_element(self, locator_key: str):
        locator = getattr(self, locator_key, None)
        if not locator:
            raise RuntimeError(f"Locator {locator_key} not found.")
        locator.wait_for()
        return locator

    def click_element(self, locator_key: str):
        locator = self.wait_for_element(locator_key)
        locator.click()

    def enter_text(self, locator_key: str, text: str):
        locator = self.wait_for_element(locator_key)
        locator.fill(text)

    def switch_to_new_window(self):
        pages = self.page.context.pages
        if len(pages) > 1:
            return pages[-1]
        return self.page

    def place_alert(self):
        self.click_element("continue_button")
        self.click_element("efx_dropdown_label")
        current_page = self.switch_to_new_window()
        self.page = current_page
        self.enter_text("ssn", "***-**-7575")
        self.click_element("last_name")
        self.enter_text("last_name", "test")
        self.click_element("phone_number")
        self.enter_text("phone_number", "768-676-****")
        self.click_element("dob")
        self.enter_text("dob", "04/22/1990")
        self.click_element("address")
        self.enter_text("address", "test")
        self.click_element("city")
        self.enter_text("city", "test")
        self.click_element("address_line_2")
        self.enter_text("address_line_2", "test")
        self.click_element("efx_dropdown_label") # Assuming select state dropdown
        self.click_element("efx_dropdown_label") # Assuming "Alaska" is selected
        self.enter_text("zip", "67567")
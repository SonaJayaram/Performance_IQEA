from playwright.sync_api import sync_playwright

class EqufixPlaceOnAlertPlaywright:
    def __init__(self, page):
        self.page = page
        
        # Locators
        self.continue_button = page.locator("xpath=//button[@id='continue-button']")
        self.zip = page.locator("xpath=//input[@id='zip']")
        self.efx_dropdown_label = page.locator("xpath=//button[@id='efx-dropdown-label-753393']")
        self.city = page.locator("xpath=//input[@id='city']")
        self.address_line2 = page.locator("xpath=//input[@id='addressLine2Id']")
        self.address = page.locator("xpath=//input[@id='address']")
        self.phone_number = page.locator("xpath=//input[@id='phoneNumber']")
        self.ssn = page.locator("xpath=//input[@id='ssn']")
        self.dob = page.locator("xpath=//input[@id='dob']")
        self.last_name = page.locator("xpath=//input[@id='lastName']")
        self.first_name = page.locator("xpath=//input[@id='firstNameId']")

    # Helper methods
    def wait_for_element(self, locator):
        locator.wait_for()
    
    def click(self, locator):
        self.wait_for_element(locator)
        locator.click()

    def enter_text(self, locator, text):
        self.wait_for_element(locator)
        if not locator:
            raise RuntimeError("Cannot enter text into a missing locator.")
        locator.fill(text)
    
    def switch_to_window_by_index(self, index):
        pages = self.page.context.pages
        if 0 <= index < len(pages):
            pages[index].bring_to_front()
        else:
            raise RuntimeError("Invalid window index.")
    
    def switch_to_window_by_handle(self, handle):
        pages = self.page.context.pages
        for p in pages:
            if p == handle:
                p.bring_to_front()
                return
        raise RuntimeError("Window handle not found.")
    
    def switch_to_window_matching_url(self, url):
        pages = self.page.context.pages
        for p in pages:
            if p.url == url:
                p.bring_to_front()
                return
        raise RuntimeError("No window matches the given URL.")
    
    def switch_to_new_window(self, url):
        old_pages = self.page.context.pages
        self.page.context.wait_for_event("page")
        new_pages = self.page.context.pages
        if len(new_pages) > len(old_pages):
            new_page = new_pages[-1]
            if new_page.url == url or new_page:
                new_page.bring_to_front()
        else:
            raise RuntimeError("No new window detected.")

    # Action methods
    def click_continue_button(self):
        self.click(self.continue_button)
    
    def enter_zip(self, zip_code):
        self.enter_text(self.zip, zip_code)
    
    def click_efx_dropdown(self):
        self.click(self.efx_dropdown_label)
    
    def enter_city(self, city_name):
        self.enter_text(self.city, city_name)
    
    def enter_address_line2(self, address_line2):
        self.enter_text(self.address_line2, address_line2)
    
    def enter_address(self, address_text):
        self.enter_text(self.address, address_text)
    
    def enter_phone_number(self, phone_number):
        self.enter_text(self.phone_number, phone_number)
    
    def enter_ssn(self, ssn):
        self.click(self.ssn)
        self.enter_text(self.ssn, ssn)
    
    def enter_dob(self, dob):
        self.enter_text(self.dob, dob)
    
    def enter_last_name(self, last_name):
        self.enter_text(self.last_name, last_name)
    
    def enter_first_name(self, first_name):
        self.enter_text(self.first_name, first_name)
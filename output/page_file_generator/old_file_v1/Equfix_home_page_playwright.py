from playwright.sync_api import Page

class EqufixHomePagePlaywright:
    def __init__(self, page: Page):
        self.page = page
        # Locators
        self.place_an_alert = page.locator("xpath=//a[contains(@class, 'btn') and text()='PLACE AN ALERT']")
        self.close_button = page.locator("xpath=//button[@name='close']")
        self.banner_description = page.locator("xpath=//*[contains(@class, 'banner-description')]")
        self.first_name = page.locator("xpath=//*[@name='firstName']")
        self.ssn = page.locator("xpath=//*[@name='ssn']")
        self.last_name = page.locator("xpath=//*[@name='lastName']")
        self.phone_number = page.locator("xpath=//*[@name='phoneNumber']")
        self.date_of_birth = page.locator("xpath=//*[@name='dateOfBirthMasked']")
        self.address_line1 = page.locator("xpath=//*[@name='addressLine1']")
        self.city_name = page.locator("xpath=//*[@name='cityName']")
        self.address_line2 = page.locator("xpath=//*[@name='addressLine2']")
        self.state_dropdown = page.locator("xpath=//*[@id='efx-dropdown-label-372614']")
        self.ak_option = page.locator("xpath=//*[text()='AK']")
        self.zip_code = page.locator("xpath=//*[@name='zipCode']")
        self.learn = page.locator("xpath=//*[text()='learn']")
        self.business = page.locator("xpath=//*[text()='Business']")
        self.api_developer_portal = page.locator("xpath=//*[text()='API Developer Portal']")
        self.become_a_customer = page.locator("xpath=//*[contains(@class, 'Become a Customer')]")
        self.user_guide = page.locator("xpath=//*[text()='User Guide']")
        self.register = page.locator("xpath=//*[text()='Register']")
        self.first_name_register = page.locator("xpath=//*[@name='first_name[0][value]']")
        self.last_name_register = page.locator("xpath=//*[@name='last_name[0][value]']")
        self.company_name = page.locator("xpath=//*[@name='field_company[0][value]']")
        self.email = page.locator("xpath=//*[@name='mail']")
        self.about_us = page.locator("xpath=//*[text()='aboutus']")
        self.leadership = page.locator("xpath=//*[text()='Leadership']")
        self.board_of_directors = page.locator("xpath=//*[text()='tab-1420970-1']")

    # General helper methods
    def wait_for_element(self, locator):
        locator.wait_for()

    def click(self, locator):
        self.wait_for_element(locator)
        locator.click()

    def enter_text(self, locator, text):
        self.wait_for_element(locator)
        locator.fill(text)

    def switch_to_window_by_index(self, index):
        pages = self.page.context.pages
        if index < len(pages):
            self.page = pages[index]
        else:
            raise RuntimeError(f"No window found with index {index}")

    def switch_to_window_by_handle(self, handle):
        pages = self.page.context.pages
        for p in pages:
            if p.is_visible():
                self.page = p
                return
        raise RuntimeError(f"No window found with handle {handle}")

    def switch_to_window_matching_url(self, url):
        pages = self.page.context.pages
        for p in pages:
            if p.url == url:
                self.page = p
                return
        raise RuntimeError(f"No window found matching URL {url}")

    def switch_to_new_window(self, url):
        existing_pages = self.page.context.pages
        self.page.context.wait_for_event("page")
        new_pages = self.page.context.pages
        new_window = [p for p in new_pages if p not in existing_pages]
        if new_window:
            self.page = new_window[0]
            if url and self.page.url != url:
                raise RuntimeError(f"New window does not match expected URL: {url}")
        else:
            raise RuntimeError("No new window was opened")

    # Action methods
    def click_place_an_alert(self):
        self.click(self.place_an_alert)

    def close_banner(self):
        self.click(self.close_button)

    def update_banner_description(self, text):
        self.enter_text(self.banner_description, text)

    def fill_personal_info(self, first_name, ssn, last_name, phone_number, dob, address1, city, address2, state, zip_code):
        self.enter_text(self.first_name, first_name)
        self.enter_text(self.ssn, ssn)
        self.enter_text(self.last_name, last_name)
        self.enter_text(self.phone_number, phone_number)
        self.enter_text(self.date_of_birth, dob)
        self.enter_text(self.address_line1, address1)
        self.enter_text(self.city_name, city)
        self.enter_text(self.address_line2, address2)
        self.click(self.state_dropdown)
        self.click(self.ak_option)
        self.enter_text(self.zip_code, zip_code)

    def click_learn(self):
        self.click(self.learn)

    def click_business(self):
        self.click(self.business)

    def click_api_developer_portal(self):
        self.click(self.api_developer_portal)

    def click_become_a_customer(self):
        self.click(self.become_a_customer)

    def click_user_guide(self):
        self.click(self.user_guide)

    def click_register(self):
        self.click(self.register)

    def fill_registration_form(self, first_name, last_name, company, email):
        self.enter_text(self.first_name_register, first_name)
        self.enter_text(self.last_name_register, last_name)
        self.enter_text(self.company_name, company)
        self.enter_text(self.email, email)

    def click_about_us(self):
        self.click(self.about_us)

    def click_leadership(self):
        self.click(self.leadership)

    def update_board_of_directors(self, text):
        self.enter_text(self.board_of_directors, text)
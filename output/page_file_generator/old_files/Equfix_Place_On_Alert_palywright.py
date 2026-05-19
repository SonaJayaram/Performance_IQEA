from playwright.sync_api import Page


class equifax_actions:

    def __init__(self, page: Page):
        self.page = page
        self.continue_button = page.locator("xpath=//button[@id='continue-button']")
        self.zip_code = page.locator("xpath=//input[@id='zip']")
        self.dropdown_label = page.locator("xpath=//button[@id='efx-dropdown-label-753393']")
        self.city = page.locator("xpath=//input[@id='city']")
        self.address_line_2 = page.locator("xpath=//input[@id='addressLine2Id']")
        self.address_line_1 = page.locator("xpath=//input[@id='address']")
        self.phone_number = page.locator("xpath=//input[@id='phoneNumber']")
        self.ssn = page.locator("xpath=//input[@id='ssn']")
        self.date_of_birth = page.locator("xpath=//input[@id='dob']")
        self.last_name = page.locator("xpath=//input[@id='lastName']")
        self.first_name = page.locator("xpath=//input[@id='firstNameId']")

    def wait_for_element(self, locator):
        locator.wait_for()

    def click(self, locator):
        self.wait_for_element(locator)
        locator.click()

    def enter_text(self, locator, text):
        self.wait_for_element(locator)
        locator.fill(text)

    def switch_to_window_by_index(self, index):
        all_pages = self.page.context.pages
        if index < 0 or index >= len(all_pages):
            raise IndexError("Invalid window index.")
        self.page = all_pages[index]
        self.page.bring_to_front()

    def switch_to_window_by_handle(self, handle):
        all_pages = self.page.context.pages
        for page in all_pages:
            if page == handle:
                self.page = page
                self.page.bring_to_front()
                return
        raise RuntimeError(f"No window found for handle: {handle}")

    def switch_to_new_window(self, url=None):
        with self.page.context.expect_page() as new_page:
            pass
        new_page = new_page.value
        new_page.bring_to_front()
        if url and new_page.url != url:
            raise RuntimeError(f"New window URL '{new_page.url}' does not match expected URL '{url}'")
        self.page = new_page

    def switch_to_window_matching_url(self, url):
        all_pages = self.page.context.pages
        for page in all_pages:
            if page.url == url:
                self.page = page
                self.page.bring_to_front()
                return
        raise RuntimeError(f"No window found with URL: {url}")

    def click_continue_button(self):
        self.click(self.continue_button)

    def enter_zip(self, text):
        self.enter_text(self.zip_code, text)

    def click_dropdown_label(self):
        self.click(self.dropdown_label)

    def enter_city(self, text):
        self.enter_text(self.city, text)

    def enter_address_line_2(self, text):
        self.enter_text(self.address_line_2, text)

    def enter_address_line_1(self, text):
        self.enter_text(self.address_line_1, text)

    def enter_phone_number(self, text):
        self.enter_text(self.phone_number, text)

    def click_ssn(self):
        self.click(self.ssn)

    def enter_ssn(self, text):
        self.enter_text(self.ssn, text)

    def enter_last_name(self, text):
        self.enter_text(self.last_name, text)

    def enter_first_name(self, text):
        self.enter_text(self.first_name, text)

    def enter_date_of_birth(self, text):
        self.enter_text(self.date_of_birth, text)
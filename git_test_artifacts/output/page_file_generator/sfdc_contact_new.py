from playwright.sync_api import Page, Locator

class sfdc_contact_new:
    def __init__(self, page: Page):
        self.page = page
        self.new_button = page.locator("xpath=//button[contains(text(),'New')]")
        self.last_name_field = page.locator("xpath=//input[@name='lastName']")
        self.email_field = page.locator("xpath=//input[@name='Email']")
        self.assistant_name_field = page.locator("xpath=//input[@name='AssistantName']")
        self.bio_field = page.locator("xpath=//input[@name='Bio__c']")
        self.assistant_phone_field = page.locator("xpath=//input[@name='AssistantPhone']")
        self.save_edit_button = page.locator("xpath=//button[@name='SaveEdit']")

    def wait_for_element(self, locator_key: str):
        locator = getattr(self, locator_key, None)
        if not locator:
            raise RuntimeError(f"Locator {locator_key} not found")
        locator.wait_for()

    def click_element(self, locator_key: str):
        locator = getattr(self, locator_key, None)
        if not locator:
            raise RuntimeError(f"Locator {locator_key} not found")
        locator.click()

    def enter_text(self, locator_key: str, text: str):
        locator = getattr(self, locator_key, None)
        if not locator:
            raise RuntimeError(f"Locator {locator_key} not found")
        locator.fill(text)

    def switch_to_new_window(self):
        pages = self.page.context.pages
        if len(pages) > 1:
            return pages[-1]
        return self.page

    def click_new_button(self):
        self.wait_for_element("new_button")
        self.click_element("new_button")

    def enter_last_name(self, last_name: str):
        self.wait_for_element("last_name_field")
        self.enter_text("last_name_field", last_name)

    def enter_email(self, email: str):
        self.wait_for_element("email_field")
        self.enter_text("email_field", email)

    def enter_assistant_name(self, assistant_name: str):
        self.wait_for_element("assistant_name_field")
        self.enter_text("assistant_name_field", assistant_name)

    def enter_bio(self, bio: str):
        self.wait_for_element("bio_field")
        self.enter_text("bio_field", bio)

    def enter_assistant_phone(self, assistant_phone: str):
        self.wait_for_element("assistant_phone_field")
        self.enter_text("assistant_phone_field", assistant_phone)

    def click_save_edit_button(self):
        self.wait_for_element("save_edit_button")
        self.click_element("save_edit_button")
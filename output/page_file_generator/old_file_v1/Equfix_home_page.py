from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Equfix_home_page:
    LOCATORS = {
        "place_alert_button": (By.XPATH, "//a[contains(@class, 'btn') and text()='PLACE AN ALERT']"),
        "close_button": (By.XPATH, "//button[@name='close']"),
        "banner_description": (By.ID, "banner-description"),
        "ketch_icon": (By.CLASS_NAME, "ketch-h-6 ketch-w-6 !ketch-fill-[--k-banner-header-returnButton-icon-color]"),
        "first_name_field": (By.NAME, "firstName"),
        "ssn_field": (By.NAME, "ssn"),
        "last_name_field": (By.NAME, "lastName"),
        "phone_number_field": (By.NAME, "phoneNumber"),
        "dob_field": (By.NAME, "dateOfBirthMasked"),
        "address_line1_field": (By.NAME, "addressLine1"),
        "city_name_field": (By.NAME, "cityName"),
        "address_line2_field": (By.NAME, "addressLine2"),
        "state_dropdown_label": (By.ID, "efx-dropdown-label-372614"),
        "state_ak_option": (By.XPATH, "//div[text()='AK']"),
        "zip_code_field": (By.NAME, "zipCode"),
        "learn_link": (By.ID, "learn"),
        "business_link": (By.ID, "Business"),
        "api_dev_portal_link": (By.ID, "API Developer Portal"),
        "become_customer_section": (By.ID, "Become a Customer"),
        "user_guide_button": (By.ID, "User Guide"),
        "register_button": (By.ID, "Register"),
        "first_name_register_field": (By.NAME, "first_name[0][value]"),
        "last_name_register_field": (By.NAME, "last_name[0][value]"),
        "company_register_field": (By.NAME, "field_company[0][value]"),
        "email_register_field": (By.NAME, "mail"),
        "about_us_link": (By.ID, "aboutus"),
        "leadership_link": (By.ID, "Leadership"),
        "board_of_directors_tab": (By.ID, "tab-1420970-1")
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def wait_for_element(self, locator_key):
        locator = self.LOCATORS.get(locator_key)
        if not locator:
            raise RuntimeError(f"Locator {locator_key} not found in LOCATORS dictionary.")
        return self.wait.until(EC.presence_of_element_located(locator))

    def click(self, locator_key):
        element = self.wait_for_element(locator_key)
        element.click()

    def enter_text(self, locator_key, text):
        locator = self.LOCATORS.get(locator_key)
        if not locator:
            raise RuntimeError(f"Locator {locator_key} not found in LOCATORS dictionary.")
        element = self.wait_for_element(locator_key)
        element.clear()
        element.send_keys(text)

    def switch_to_window_by_index(self, index):
        windows = self.driver.window_handles
        if index >= len(windows):
            raise RuntimeError(f"Window index {index} is out of range.")
        self.driver.switch_to.window(windows[index])

    def switch_to_window_by_handle(self, handle):
        self.driver.switch_to.window(handle)

    def switch_to_window_matching_url(self, url):
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if self.driver.current_url == url:
                return
        raise RuntimeError(f"No window found with URL: {url}")

    def switch_to_new_window(self):
        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[-1])
    # Example Action Methods
    def place_alert(self):
        self.click("PLACE AN ALERT")

    def close_banner(self):
        self.click("close_button")

    def enter_banner_description(self, description):
        self.enter_text("banner_description", description)

    def click_learn_link(self):
        self.click("learn_link")

    def click_business_link(self):
        self.click("business_link")

    def fill_personal_info(self, first_name, last_name, ssn, phone, dob, address1, address2, city, state, zip_code):
        self.enter_text("first_name_field", first_name)
        self.enter_text("last_name_field", last_name)
        self.enter_text("ssn_field", ssn)
        self.enter_text("phone_number_field", phone)
        self.enter_text("dob_field", dob)
        self.enter_text("address_line1_field", address1)
        self.enter_text("address_line2_field", address2)
        self.enter_text("city_name_field", city)
        self.click("state_dropdown_label")
        self.click("state_ak_option")
        self.enter_text("zip_code_field", zip_code)

    def navigate_to_api_portal(self):
        self.click("api_dev_portal_link")
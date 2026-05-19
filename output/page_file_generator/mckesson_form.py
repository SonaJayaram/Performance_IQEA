from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class mckesson_form:
    LOCATORS = {
        "first_name_input": (By.XPATH, "//input[@id='FirstName']"),
        "last_name_input": (By.XPATH, "//input[@id='LastName']"),
        "email_input": (By.XPATH, "//input[@id='Email']"),
        "company_input": (By.XPATH, "//input[@id='Company']"),
        "mktowebsite_input": (By.XPATH, "//input[@id='mKTOWebsite']"),
        "phone_input": (By.XPATH, "//input[@id='Phone']"),
        "title_input": (By.XPATH, "//input[@id='Title']"),
        "city_input": (By.XPATH, "//input[@id='City']"),
        "state_dropdown": (By.XPATH, "//select[@id='State']"),
        "mkto_checkbox_0": (By.XPATH, "//input[@id='mktoCheckbox_23066_0']"),
        "mkto_checkbox_1": (By.XPATH, "//input[@id='mktoCheckbox_23066_1']"),
        "mkto_checkbox_2": (By.XPATH, "//input[@id='mktoCheckbox_23066_2']"),
        "mkto_checkbox_3": (By.XPATH, "//input[@id='mktoCheckbox_23066_3']"),
        "mkto_radio_0": (By.XPATH, "//input[@id='mktoRadio_23069_0']"),
        "primary_customer_number_input": (By.XPATH, "//input[@id='Primary_Customer_Number__c']"),
        "submit_button": (By.XPATH, "//button[@type='submit']")
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def get_element(self, key):
        if key not in self.LOCATORS:
            raise RuntimeError(f"Locator '{key}' not found in LOCATORS")
        return self.wait.until(EC.presence_of_element_located(self.LOCATORS[key]))

    def get_first_name_input(self):
        return self.get_element("first_name_input")

    def get_last_name_input(self):
        return self.get_element("last_name_input")

    def get_email_input(self):
        return self.get_element("email_input")

    def get_company_input(self):
        return self.get_element("company_input")

    def get_mktowebsite_input(self):
        return self.get_element("mktowebsite_input")

    def get_phone_input(self):
        return self.get_element("phone_input")

    def get_title_input(self):
        return self.get_element("title_input")

    def get_city_input(self):
        return self.get_element("city_input")

    def get_state_dropdown(self):
        return self.get_element("state_dropdown")

    def get_mkto_checkbox_0(self):
        return self.get_element("mkto_checkbox_0")

    def get_mkto_checkbox_1(self):
        return self.get_element("mkto_checkbox_1")

    def get_mkto_checkbox_2(self):
        return self.get_element("mkto_checkbox_2")

    def get_mkto_checkbox_3(self):
        return self.get_element("mkto_checkbox_3")

    def get_mkto_radio_0(self):
        return self.get_element("mkto_radio_0")

    def get_primary_customer_number_input(self):
        return self.get_element("primary_customer_number_input")

    def get_submit_button(self):
        return self.get_element("submit_button")
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class equi_place_on_alert:
    LOCATORS = {
        "first_name_input": (By.XPATH, "//input[@id='firstNameId']"),
        "last_name_input": (By.XPATH, "//input[@id='lastName']"),
        "dob_input": (By.XPATH, "//input[@id='dob']"),
        "ssn_input": (By.XPATH, "//input[@id='ssn']"),
        "phone_number_input": (By.XPATH, "//input[@id='phoneNumber']"),
        "address_input": (By.XPATH, "//input[@id='address']"),
        "address_line2_input": (By.XPATH, "//input[@id='addressLine2Id']"),
        "city_input": (By.XPATH, "//input[@id='city']")
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

    def get_dob_input(self):
        return self.get_element("dob_input")

    def get_ssn_input(self):
        return self.get_element("ssn_input")

    def get_phone_number_input(self):
        return self.get_element("phone_number_input")

    def get_address_input(self):
        return self.get_element("address_input")

    def get_address_line2_input(self):
        return self.get_element("address_line2_input")

    def get_city_input(self):
        return self.get_element("city_input")
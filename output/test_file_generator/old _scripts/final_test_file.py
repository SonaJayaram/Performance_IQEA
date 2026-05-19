import pytest
import allure
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from output.page_file_generator.EqufixHomepage import EqufixHomePage
from output.page_file_generator.EqufixPlaceOnAlert import EqufixPlaceOnAlert

@pytest.fixture(scope="function")
def setup():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

def wait_for_element(driver, locator, timeout=10):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))

def click_via_locator(driver, locator):
    element = wait_for_element(driver, locator)
    element.click()

def enter_text_via_locator(driver, locator, text):
    element = wait_for_element(driver, locator)
    element.clear()
    element.send_keys(text)

@allure.step("Load action data from recorded actions")
def load_action_data():
    return {
        "ssn": "***-**-6868",
        "last_name": "test",
        "phone_number": "878-676-****",
        "dob": "04/22/1990",
        "address_line_1": "test",
        "city": "test",
        "address_line_2": "test",
        "state": "Arkansas",
        "zip_code": "67876"
    }

@allure.feature("Place Fraud Alert")
@allure.story("TC01 - Place Fraud Alert (Positive Flow)")
def test_place_fraud_alert_positive_flow(setup):
    driver = setup
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    driver.get(base_url)

    home_page = EqufixHomePage(driver)
    place_on_alert_page = EqufixPlaceOnAlert(driver)

    with allure.step("Click on 'Place an Alert' and switch to new window"):
        home_page.click_place_an_alert()
        original_window = driver.current_window_handle
        #WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        for handle in driver.window_handles:
            if handle != original_window:
                driver.switch_to.window(handle)
                break

    with allure.step("Perform alert placement flow"):
        data = load_action_data()
        place_on_alert_page.perform_alert_placement_flow(**data)

    with allure.step("Verify successful alert placement"):
        success_message_locator = (By.XPATH, "//div[contains(text(), 'Alert placed successfully')]")
        assert wait_for_element(driver, success_message_locator), "Success message is not displayed"

@allure.feature("Place Fraud Alert")
@allure.story("TC02 - Place Alert - Invalid SSN")
def test_place_alert_invalid_ssn(setup):
    driver = setup
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    driver.get(base_url)

    home_page = EqufixHomePage(driver)
    place_on_alert_page = EqufixPlaceOnAlert(driver)

    with allure.step("Click on 'Place an Alert' and switch to new window"):
        home_page.click_place_an_alert()
        original_window = driver.current_window_handle
       # WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        for handle in driver.window_handles:
            if handle != original_window:
                driver.switch_to.window(handle)
                break

    with allure.step("Perform alert placement flow with invalid SSN"):
        data = load_action_data()
        data["ssn"] = "123-45-6789"  # Invalid SSN
        place_on_alert_page.perform_alert_placement_flow(**data)

    with allure.step("Verify error message for invalid SSN"):
        error_message_locator = (By.XPATH, "//div[contains(text(), 'Invalid SSN')]")
        assert wait_for_element(driver, error_message_locator), "Error message for invalid SSN is not displayed"

@allure.feature("Place Fraud Alert")
@allure.story("TC10 - Place Alert - Missing ZIP Code")
def test_place_alert_missing_zip_code(setup):
    driver = setup
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    driver.get(base_url)

    home_page = EqufixHomePage(driver)
    place_on_alert_page = EqufixPlaceOnAlert(driver)

    with allure.step("Click on 'Place an Alert' and switch to new window"):
        home_page.click_place_an_alert()
        original_window = driver.current_window_handle
        #WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        for handle in driver.window_handles:
            if handle != original_window:
                driver.switch_to.window(handle)
                break

    with allure.step("Perform alert placement flow with missing ZIP Code"):
        data = load_action_data()
        data["zip_code"] = ""  # Missing ZIP Code
        place_on_alert_page.perform_alert_placement_flow(**data)

    with allure.step("Verify error message for missing ZIP Code"):
        error_message_locator = (By.XPATH, "//div[contains(text(), 'ZIP Code is required')]")
        assert wait_for_element(driver, error_message_locator), "Error message for missing ZIP Code is not displayed"
import pytest
import allure
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from output.page_file_generator.EqufixHomepage import Equfix_home_page
from output.page_file_generator.EqufixPlaceOnAlert import Equfix_Place_On_Alert

# Constants
BASE_URL = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"

# Fixtures
@pytest.fixture(scope="function")
def setup_browser():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(), options=options)
    driver.implicitly_wait(5)
    yield driver
    driver.quit()

# Helper Functions
def switch_to_new_window(driver, original_window):
    if len(driver.window_handles) > 1:
        new_window = [handle for handle in driver.window_handles if handle != original_window][0]
        driver.switch_to.window(new_window)
        return new_window
    return None

def wait_for_element(driver, locator, timeout=10):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))

def click_via_locator(driver, locator):
    element = wait_for_element(driver, locator)
    element.click()

def enter_text_via_locator(driver, locator, text):
    element = wait_for_element(driver, locator)
    element.clear()
    element.send_keys(text)

# Test Cases
@allure.feature("Equifax Fraud Alert Placement")
@allure.story("TC01 - Place an Alert - Successful Form Submission")
def test_place_alert_successful_submission(setup_browser):
    driver = setup_browser


    # Step 1: Navigate to the base URL
    with allure.step("Navigate to Equifax Fraud Alert page"):
        driver.get(BASE_URL)
    original_window = driver.current_window_handle
    # Step 2: Initialize Page Objects
    home_page = Equfix_home_page(driver)
    alert_page = Equfix_Place_On_Alert(driver)

    # Step 3: Perform actions on the home page
    with allure.step("Perform actions on the home page"):
        home_page.click_place_an_alert()
        new_window = switch_to_new_window(driver, original_window)
        assert new_window, "Failed to switch to the new window."
        assert "https://my.equifax.com/consumer-registration/UCSC/#/personal-info" in driver.current_url, \
            "Failed to navigate to the alert placement page."

    # Step 4: Fill out the alert placement form
    with allure.step("Fill out the alert placement form"):
        alert_page.enter_first_name("John")
        alert_page.enter_last_name("Doe")
        alert_page.enter_ssn("123-45-6789")
        alert_page.enter_dob("01/01/1990")
        alert_page.enter_address("123 Main St")
        alert_page.enter_address_line_2("Apt 4B")
        alert_page.enter_city("Atlanta")
        alert_page.enter_zip_code("30301")
        alert_page.enter_phone_number("404-555-1234")
        alert_page.click_continue_button()

    # Step 5: Verify successful submission
    with allure.step("Verify successful submission"):
        success_message_locator = (By.XPATH, "//div[contains(text(), 'Your alert has been placed successfully')]")
        success_message = wait_for_element(driver, success_message_locator)
        assert success_message.is_displayed(), "Success message not displayed."

    # Step 6: Close the new window and switch back
    with allure.step("Close the new window and switch back to the original window"):
        driver.close()
        driver.switch_to.window(original_window)

@allure.feature("Equifax Fraud Alert Placement")
@allure.story("TC02 - Place an Alert - Empty First Name Validation")
def test_empty_first_name_validation(setup_browser):
    driver = setup_browser
    original_window = driver.current_window_handle

    # Step 1: Navigate to the base URL
    with allure.step("Navigate to Equifax Fraud Alert page"):
        driver.get(BASE_URL)


    # Step 2: Initialize Page Objects
    home_page = Equfix_home_page(driver)
    alert_page = Equfix_Place_On_Alert(driver)

    # Step 3: Perform actions on the home page
    with allure.step("Perform actions on the home page"):
        home_page.click_place_an_alert()
        new_window = switch_to_new_window(driver, original_window)
        assert new_window, "Failed to switch to the new window."
        assert "https://my.equifax.com/consumer-registration/UCSC/#/personal-info" in driver.current_url, \
            "Failed to navigate to the alert placement page."

    # Step 4: Leave the first name field empty and attempt submission
    with allure.step("Leave the first name field empty and attempt submission"):
        alert_page.enter_last_name("Doe")
        alert_page.enter_ssn("123-45-6789")
        alert_page.enter_dob("01/01/1990")
        alert_page.enter_address("123 Main St")
        alert_page.enter_address_line_2("Apt 4B")
        alert_page.enter_city("Atlanta")
        alert_page.enter_zip_code("30301")
        alert_page.enter_phone_number("404-555-1234")
        alert_page.click_continue_button()

    # Step 5: Verify validation error
    with allure.step("Verify validation error for empty first name"):
        error_message_locator = (By.XPATH, "//div[contains(text(), 'First name is required')]")
        error_message = wait_for_element(driver, error_message_locator)
        assert error_message.is_displayed(), "Validation error for empty first name not displayed."

    # Step 6: Close the new window and switch back
    with allure.step("Close the new window and switch back to the original window"):
        driver.close()
        driver.switch_to.window(original_window)

@allure.feature("Equifax Fraud Alert Placement")
@allure.story("TC04 - Place Fraud Alert (Negative - Invalid SSN Format)")
def test_invalid_ssn_format(setup_browser):
    driver = setup_browser
    original_window = driver.current_window_handle

    # Step 1: Navigate to the base URL
    with allure.step("Navigate to Equifax Fraud Alert page"):
        driver.get(BASE_URL)

    # Step 2: Initialize Page Objects
    home_page = Equfix_home_page(driver)
    alert_page = Equfix_Place_On_Alert(driver)

    # Step 3: Perform actions on the home page
    with allure.step("Perform actions on the home page"):
        home_page.click_place_an_alert()
        new_window = switch_to_new_window(driver, original_window)
        assert new_window, "Failed to switch to the new window."
        assert "https://my.equifax.com/consumer-registration/UCSC/#/personal-info" in driver.current_url, \
            "Failed to navigate to the alert placement page."

    # Step 4: Enter invalid SSN and attempt submission
    with allure.step("Enter invalid SSN and attempt submission"):
        alert_page.enter_first_name("John")
        alert_page.enter_last_name("Doe")
        alert_page.enter_ssn("123-45-678")  # Invalid SSN format
        alert_page.enter_dob("01/01/1990")
        alert_page.enter_address("123 Main St")
        alert_page.enter_address_line_2("Apt 4B")
        alert_page.enter_city("Atlanta")
        alert_page.enter_zip_code("30301")
        alert_page.enter_phone_number("404-555-1234")
        alert_page.click_continue_button()

    # Step 5: Verify validation error
    with allure.step("Verify validation error for invalid SSN format"):
        error_message_locator = (By.XPATH, "//div[contains(text(), 'Invalid SSN format')]")
        error_message = wait_for_element(driver, error_message_locator)
        assert error_message.is_displayed(), "Validation error for invalid SSN format not displayed."

    # Step 6: Close the new window and switch back
    with allure.step("Close the new window and switch back to the original window"):
        driver.close()
        driver.switch_to.window(original_window)

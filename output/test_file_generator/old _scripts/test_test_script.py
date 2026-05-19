import pytest
import allure
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from output.page_file_generator.EqufixHomepage import Equfix_home_page
from output.page_file_generator.EqufixPlaceOnAlert import Equfix_Place_On_Alert


@pytest.fixture(scope="function")
def setup_driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()


@allure.step("Wait for element to be visible")
def wait_for_element(driver, locator, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))
    except TimeoutException:
        pytest.fail(f"Element with locator {locator} not found within {timeout} seconds")


@allure.step("Click element via locator")
def click_via_locator(driver, locator):
    element = wait_for_element(driver, locator)
    element.click()


@allure.step("Enter text via locator")
def enter_text_via_locator(driver, locator, text):
    element = wait_for_element(driver, locator)
    element.clear()
    element.send_keys(text)


@allure.step("Switch to new window")
def switch_to_new_window(driver):
    original_window = driver.current_window_handle
    for handle in driver.window_handles:
        if handle != original_window:
            driver.switch_to.window(handle)
            break


@allure.step("Switch back to original window")
def switch_back_to_original_window(driver, original_window):
    driver.close()
    driver.switch_to.window(original_window)


@allure.feature("Place an Alert")
@allure.story("TC01 - Place an Alert - Successful Form Submission")
def test_place_alert_successful_form_submission(setup_driver):
    driver = setup_driver
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    driver.get(base_url)

    # Initialize Page Objects
    home_page = Equfix_home_page(driver)
    alert_page = Equfix_Place_On_Alert(driver)

    # Step 1: Perform actions on the home page
    with allure.step("Perform Equifax home page flow"):
        home_page.click_place_an_alert()
        switch_to_new_window(driver)
        assert driver.current_url == "https://my.equifax.com/consumer-registration/UCSC/#/personal-info", \
            "Failed to navigate to the alert placement page"

    # Step 2: Fill out the alert placement form
    with allure.step("Fill out the alert placement form"):
        alert_page.enter_ssn("***-**-7575")
        alert_page.enter_last_name("test")
        alert_page.enter_phone_number("768-676-****")
        alert_page.enter_dob("04/22/1990")
        alert_page.enter_address("test")
        alert_page.enter_city("test")
        alert_page.enter_address_line_2("test")
        alert_page.select_state_alaska()
        alert_page.enter_zip_code("67567")
        alert_page.click_continue_button()

    # Step 3: Verify successful submission
    with allure.step("Verify successful form submission"):
        success_message_locator = (By.XPATH, "//div[contains(text(), 'Your alert has been placed successfully')]")
        success_message = wait_for_element(driver, success_message_locator)
        assert success_message.is_displayed(), "Success message not displayed"


@allure.feature("Place an Alert")
@allure.story("TC02 - Place Fraud Alert (Negative - Missing First Name)")
def test_place_alert_missing_first_name(setup_driver):
    driver = setup_driver
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    driver.get(base_url)

    # Initialize Page Objects
    home_page = Equfix_home_page(driver)
    alert_page = Equfix_Place_On_Alert(driver)

    # Step 1: Perform actions on the home page
    with allure.step("Perform Equifax home page flow"):
        home_page.click_place_an_alert()
        switch_to_new_window(driver)
        assert driver.current_url == "https://my.equifax.com/consumer-registration/UCSC/#/personal-info", \
            "Failed to navigate to the alert placement page"

    # Step 2: Fill out the alert placement form with missing first name
    with allure.step("Fill out the alert placement form with missing first name"):
        alert_page.enter_ssn("***-**-7575")
        alert_page.enter_last_name("test")
        alert_page.enter_phone_number("768-676-****")
        alert_page.enter_dob("04/22/1990")
        alert_page.enter_address("test")
        alert_page.enter_city("test")
        alert_page.enter_address_line_2("test")
        alert_page.select_state_alaska()
        alert_page.enter_zip_code("67567")
        alert_page.click_continue_button()

    # Step 3: Verify error message for missing first name
    with allure.step("Verify error message for missing first name"):
        error_message_locator = (By.XPATH, "//div[contains(text(), 'First name is required')]")
        error_message = wait_for_element(driver, error_message_locator)
        assert error_message.is_displayed(), "Error message for missing first name not displayed"

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import allure
from output.page_file_generator.EqufixHomepage import Equfix_home_page
from output.page_file_generator.EqufixPlaceOnAlert import Equfix_Place_On_Alert


@pytest.fixture(scope="function")
def setup_driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()


@allure.step("Launch application and navigate to base URL")
def launch_application(driver, base_url):
    driver.get(base_url)


@allure.step("Switch to new window")
def switch_to_new_window(driver):
    original_window = driver.current_window_handle
    WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
    for handle in driver.window_handles:
        if handle != original_window:
            driver.switch_to.window(handle)
            break


@allure.step("Close current window and switch back to original")
def close_window_and_switch_back(driver, original_window):
    driver.close()
    driver.switch_to.window(original_window)


@allure.step("Wait for element and click")
def click_via_locator(driver, locator):
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(locator)).click()
    except TimeoutException:
        raise AssertionError(f"Element with locator {locator} not clickable")


@allure.step("Wait for element and enter text")
def enter_text_via_locator(driver, locator, text):
    try:
        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located(locator))
        element.clear()
        element.send_keys(text)
    except TimeoutException:
        raise AssertionError(f"Element with locator {locator} not found to enter text")


@allure.feature("Place Fraud Alert")
@allure.story("TC01 - Place Fraud Alert (Positive Flow)")
def test_place_fraud_alert_positive_flow(setup_driver):
    driver = setup_driver
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    equfix_home_page = Equfix_home_page(driver)
    equfix_place_on_alert = Equfix_Place_On_Alert(driver)

    with allure.step("Step 1: Launch application"):
        launch_application(driver, base_url)

    with allure.step("Step 2: Perform Equifax home page flow"):
        equfix_home_page.perform_equifax_home_page_flow()

    with allure.step("Step 3: Switch to new window for alert placement"):
        switch_to_new_window(driver)

    with allure.step("Step 4: Perform alert placement flow"):
        equfix_place_on_alert.perform_alert_placement_flow()

    with allure.step("Step 5: Validate successful alert placement"):
        success_message_locator = (By.XPATH, "//div[contains(text(), 'Alert placed successfully')]")
        assert WebDriverWait(driver, 10).until(EC.visibility_of_element_located(success_message_locator)), \
            "Success message is not displayed"


@allure.feature("Place Fraud Alert")
@allure.story("TC13 - Place Fraud Alert (Negative - Invalid ZIP Code Format)")
def test_place_fraud_alert_invalid_zip(setup_driver):
    driver = setup_driver
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    equfix_home_page = Equfix_home_page(driver)
    equfix_place_on_alert = Equfix_Place_On_Alert(driver)

    with allure.step("Step 1: Launch application"):
        launch_application(driver, base_url)

    with allure.step("Step 2: Perform Equifax home page flow"):
        equfix_home_page.perform_equifax_home_page_flow()

    with allure.step("Step 3: Switch to new window for alert placement"):
        switch_to_new_window(driver)

    with allure.step("Step 4: Enter invalid ZIP code and validate error"):
        equfix_place_on_alert.enter_zip_code("123")
        equfix_place_on_alert.click_continue_button()
        error_message_locator = (By.XPATH, "//div[contains(text(), 'Invalid ZIP code format')]")
        assert WebDriverWait(driver, 10).until(EC.visibility_of_element_located(error_message_locator)), \
            "Error message for invalid ZIP code is not displayed"


@allure.feature("Place Fraud Alert")
@allure.story("TC10 - Place Fraud Alert (Negative - Invalid Phone Number Format)")
def test_place_fraud_alert_invalid_phone(setup_driver):
    driver = setup_driver
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    equfix_home_page = Equfix_home_page(driver)
    equfix_place_on_alert = Equfix_Place_On_Alert(driver)

    with allure.step("Step 1: Launch application"):
        launch_application(driver, base_url)

    with allure.step("Step 2: Perform Equifax home page flow"):
        equfix_home_page.perform_equifax_home_page_flow()

    with allure.step("Step 3: Switch to new window for alert placement"):
        switch_to_new_window(driver)

    with allure.step("Step 4: Enter invalid phone number and validate error"):
        equfix_place_on_alert.enter_phone_number("12345")
        equfix_place_on_alert.click_continue_button()
        error_message_locator = (By.XPATH, "//div[contains(text(), 'Invalid phone number format')]")
        assert WebDriverWait(driver, 10).until(EC.visibility_of_element_located(error_message_locator)), \
            "Error message for invalid phone number is not displayed"

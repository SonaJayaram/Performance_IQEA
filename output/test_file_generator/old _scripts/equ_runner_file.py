import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from output.page_file_generator.EqufixHomepage import EqufixHomepage
from output.page_file_generator.Equfixplaceanalert import Equfixplaceanalert
import allure
import time


@pytest.fixture(scope="function")
def setup():
    # Initialize WebDriver
    driver = webdriver.Chrome()
    driver.maximize_window()
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    driver.get(base_url)
    yield driver
    driver.quit()


@allure.step("Wait for element to be visible")
def wait_for_element(driver, locator, timeout=10):
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))


@allure.step("Click element via locator")
def click_via_locator(driver, locator):
    element = wait_for_element(driver, locator)
    element.click()


@allure.step("Enter text via locator")
def enter_text_via_locator(driver, locator, text):
    element = wait_for_element(driver, locator)
    element.clear()
    element.send_keys(text)


@allure.feature("Place Fraud Alert")
@allure.story("TC01 - Place Fraud Alert (Positive Flow)")
def test_place_fraud_alert_positive_flow(setup):
    driver = setup
    homepage = EqufixHomepage(driver)
    place_alert_page = Equfixplaceanalert(driver)

    with allure.step("Perform Equifax homepage flow"):
        homepage.click_place_an_alert()
        homepage.switch_to_new_window()

    with allure.step("Fill out fraud alert form"):
        place_alert_page.enter_ssn("***-**-6686")
        place_alert_page.enter_last_name("test")
        place_alert_page.enter_phone_number("786-876-****")
        place_alert_page.enter_date_of_birth("04/22/1990")
        place_alert_page.enter_address_line1("test")
        place_alert_page.enter_address_line2("test")
        place_alert_page.enter_city("test")
        place_alert_page.select_state("Alaska")
        place_alert_page.enter_zip_code("78686")
        place_alert_page.proceed_to_next_step()

    with allure.step("Verify success message"):
        success_message_locator = (By.XPATH, "//div[contains(text(), 'Success')]")
        assert wait_for_element(driver, success_message_locator), "Success message is not displayed"


@allure.feature("Place Fraud Alert")
@allure.story("TC02 - Place Fraud Alert (Negative Flow - Missing First Name)")
def test_place_fraud_alert_missing_first_name(setup):
    driver = setup
    homepage = EqufixHomepage(driver)
    place_alert_page = Equfixplaceanalert(driver)

    with allure.step("Perform Equifax homepage flow"):
        homepage.click_place_an_alert()
        homepage.switch_to_new_window()

    with allure.step("Fill out fraud alert form with missing first name"):
        place_alert_page.enter_ssn("***-**-6686")
        place_alert_page.enter_last_name("test")
        place_alert_page.enter_phone_number("786-876-****")
        place_alert_page.enter_date_of_birth("04/22/1990")
        place_alert_page.enter_address_line1("test")
        place_alert_page.enter_address_line2("test")
        place_alert_page.enter_city("test")
        place_alert_page.select_state("Alaska")
        place_alert_page.enter_zip_code("78686")
        place_alert_page.proceed_to_next_step()

    with allure.step("Verify error message for missing first name"):
        error_message_locator = (By.XPATH, "//div[contains(text(), 'First Name is required')]")
        assert wait_for_element(driver, error_message_locator), "Error message for missing first name is not displayed"


@allure.feature("Place Fraud Alert")
@allure.story("TC02 - Place Alert - Invalid SSN")
def test_place_alert_invalid_ssn(setup):
    driver = setup
    homepage = EqufixHomepage(driver)
    place_alert_page = Equfixplaceanalert(driver)

    with allure.step("Perform Equifax homepage flow"):
        homepage.click_place_an_alert()
        homepage.switch_to_new_window()

    with allure.step("Fill out fraud alert form with invalid SSN"):
        place_alert_page.enter_ssn("123-45-678")
        place_alert_page.enter_last_name("test")
        place_alert_page.enter_phone_number("786-876-****")
        place_alert_page.enter_date_of_birth("04/22/1990")
        place_alert_page.enter_address_line1("test")
        place_alert_page.enter_address_line2("test")
        place_alert_page.enter_city("test")
        place_alert_page.select_state("Alaska")
        place_alert_page.enter_zip_code("78686")
        place_alert_page.proceed_to_next_step()

    with allure.step("Verify error message for invalid SSN"):
        error_message_locator = (By.XPATH, "//div[contains(text(), 'Invalid SSN')]")
        assert wait_for_element(driver, error_message_locator), "Error message for invalid SSN is not displayed"
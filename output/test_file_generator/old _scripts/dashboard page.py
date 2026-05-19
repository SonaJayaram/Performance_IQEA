import pytest
import allure
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from output.page_file_generator.EqufixHomepage import EqufixHomePage
from output.page_file_generator.EqufixPlaceOnAlert import EqufixPlaceOnAlert

@pytest.fixture(scope="function")
def setup_driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

@pytest.fixture(scope="function")
def base_url():
    return "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"

def load_action_data():
    return {
        "ssn": "***-**-7575",
        "last_name": "test",
        "phone_number": "76-676-****",
        "dob": "04/22/1990",
        "address_line_1": "test",
        "city": "test",
        "address_line_2": "test",
        "state": "Alaska",
        "zip_code": ""
    }


@allure.feature("Place Fraud Alert")
@allure.story("TC13 - Place Fraud Alert (Negative - Invalid ZIP Code Format)")
def test_place_fraud_alert_invalid_zip(setup_driver, base_url):
    driver = setup_driver
    driver.get(base_url)
    equfix_home_page = EqufixHomePage(driver)
    equfix_place_on_alert = EqufixPlaceOnAlert(driver)

    with allure.step("Click on 'Place an Alert' button"):
        equfix_home_page.click_place_an_alert()

    with allure.step("Switch to new window for alert placement"):
        equfix_home_page.switch_to_new_window()

    data = load_action_data()
    data["zip_code"] = "INVALID"

    with allure.step("Fill in alert placement form with invalid ZIP code"):
        equfix_place_on_alert.enter_ssn(data["ssn"])
        equfix_place_on_alert.enter_last_name(data["last_name"])
        equfix_place_on_alert.enter_phone_number(data["phone_number"])
        equfix_place_on_alert.enter_dob(data["dob"])
        equfix_place_on_alert.enter_address(data["address_line_1"])
        equfix_place_on_alert.enter_city(data["city"])
        equfix_place_on_alert.enter_address_line_2(data["address_line_2"])
        equfix_place_on_alert.select_state_alaska()
        equfix_place_on_alert.enter_zip_code(data["zip_code"])

    with allure.step("Submit the alert placement form"):
        equfix_place_on_alert.click_continue_button()

    with allure.step("Verify error message for invalid ZIP code is displayed"):
        error_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'enter_zip_code')]"))
        )
        assert error_message.is_displayed(), "Error message for invalid ZIP code is not displayed"

@allure.feature("Place Fraud Alert")
@allure.story("TC10 - Place Fraud Alert (Negative - Invalid Phone Number Format)")
def test_place_fraud_alert_invalid_phone(setup_driver, base_url):
    driver = setup_driver
    driver.get(base_url)
    equfix_home_page = EqufixHomePage(driver)
    equfix_place_on_alert = EqufixPlaceOnAlert(driver)

    with allure.step("Click on 'Place an Alert' button"):
        equfix_home_page.click_place_an_alert()

    with allure.step("Switch to new window for alert placement"):
        equfix_home_page.switch_to_new_window()

    data = load_action_data()
    data["phone_number"] = "INVALID"

    with allure.step("Fill in alert placement form with invalid phone number"):
        equfix_place_on_alert.enter_ssn(data["ssn"])
        equfix_place_on_alert.enter_last_name(data["last_name"])
        equfix_place_on_alert.enter_phone_number(data["phone_number"])
        equfix_place_on_alert.enter_dob(data["dob"])
        equfix_place_on_alert.enter_address(data["address_line_1"])
        equfix_place_on_alert.enter_city(data["city"])
        equfix_place_on_alert.enter_address_line_2(data["address_line_2"])
        equfix_place_on_alert.select_state_alaska()
        equfix_place_on_alert.enter_zip_code(data["zip_code"])

    with allure.step("Submit the alert placement form"):
        equfix_place_on_alert.click_continue_button()

    with allure.step("Verify error message for invalid phone number is displayed"):
        error_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'enter_zip_code')]"))
        )
        assert error_message.is_displayed(), "Error message for invalid phone number is not displayed"
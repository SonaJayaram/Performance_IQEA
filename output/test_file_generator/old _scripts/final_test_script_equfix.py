import pytest
import allure
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from output.page_file_generator.Equfixplaceanalert import Equfixplaceanalert
from output.page_file_generator.EqufixHomepage import EqufixHomePage

@pytest.fixture(scope="function")
def setup():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

def load_action_data(file_name):
    # Simulate loading data from recorded user actions
    if file_name == "equfix_place_on_alert_actions.txt":
        return {
            "ssn": "***-**-7575",
            "last_name": "test",
            "phone_number": "768-676-****",
            "date_of_birth": "04/22/1990",
            "address_line1": "test",
            "address_line2": "test",
            "city": "test",
            "state": "Alaska",
            "zip_code": "67567"
        }
    return {}

@allure.feature("Place Fraud Alert")
@allure.story("TC01 - Place Fraud Alert (Positive Flow)")
def test_place_fraud_alert_positive_flow(setup):
    driver = setup
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    driver.get(base_url)

    homepage = EqufixHomePage(driver)
    place_alert_page = Equfixplaceanalert(driver)

    with allure.step("Click on 'Place an Alert' button"):
        homepage.click_place_an_alert()

    with allure.step("Switch to new window for alert placement"):
        original_window = driver.current_window_handle
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
        new_window = [handle for handle in driver.window_handles if handle != original_window][0]
        driver.switch_to.window(new_window)
        assert "https://my.equifax.com/consumer-registration/UCSC/#/personal-info" in driver.current_url, \
            "Failed to switch to the alert placement window"

    with allure.step("Fill in the alert placement form"):
        data = load_action_data("equfix_place_on_alert_actions.txt")
        place_alert_page.enter_ssn(data["ssn"])
        place_alert_page.enter_last_name(data["last_name"])
        place_alert_page.enter_phone_number(data["phone_number"])
        place_alert_page.enter_date_of_birth(data["date_of_birth"])
        place_alert_page.enter_address_line1(data["address_line1"])
        place_alert_page.enter_address_line2(data["address_line2"])
        place_alert_page.enter_city(data["city"])
        place_alert_page.select_state(data["state"])
        place_alert_page.enter_zip_code(data["zip_code"])

    with allure.step("Submit the alert placement form"):
        place_alert_page.proceed_to_next_step()

    with allure.step("Verify successful alert placement"):
        success_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Success')]"))
        )
        assert success_message.is_displayed(), "Success message is not displayed"

@allure.feature("Place Fraud Alert")
@allure.story("TC02 - Place Alert - Invalid SSN")
def test_place_alert_invalid_ssn(setup):
    driver = setup
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    driver.get(base_url)

    homepage = EqufixHomePage(driver)
    place_alert_page = Equfixplaceanalert(driver)

    with allure.step("Click on 'Place an Alert' button"):
        homepage.click_place_an_alert()

    with allure.step("Switch to new window for alert placement"):
        original_window = driver.current_window_handle
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
        new_window = [handle for handle in driver.window_handles if handle != original_window][0]
        driver.switch_to.window(new_window)


    with allure.step("Fill in the alert placement form with invalid SSN"):
        place_alert_page.enter_ssn("123-45-6789")  # Invalid SSN
        place_alert_page.enter_last_name("test")
        place_alert_page.enter_phone_number("768-676-****")
        place_alert_page.enter_date_of_birth("04/22/1990")
        place_alert_page.enter_address_line1("test")
        place_alert_page.enter_address_line2("test")
        place_alert_page.enter_city("test")
        place_alert_page.select_state("Alaska")
        place_alert_page.enter_zip_code("67567")

    with allure.step("Submit the alert placement form"):
        place_alert_page.proceed_to_next_step()

    with allure.step("Verify error message for invalid SSN"):
        error_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Invalid SSN')]"))
        )
        assert error_message.is_displayed(), "Error message for invalid SSN is not displayed"

@allure.feature("Place Fraud Alert")
@allure.story("TC07 - Place Alert - Missing City")
def test_place_alert_missing_city(setup):
    driver = setup
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    driver.get(base_url)

    homepage = EqufixHomePage(driver)
    place_alert_page = Equfixplaceanalert(driver)

    with allure.step("Click on 'Place an Alert' button"):
        homepage.click_place_an_alert()

    with allure.step("Switch to new window for alert placement"):
        original_window = driver.current_window_handle
        #WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
        new_window = [handle for handle in driver.window_handles if handle != original_window][0]
        driver.switch_to.window(new_window)


    with allure.step("Fill in the alert placement form with missing city"):
        place_alert_page.enter_ssn("***-**-7575")
        place_alert_page.enter_last_name("test")
        place_alert_page.enter_phone_number("768-676-****")
        place_alert_page.enter_date_of_birth("04/22/1990")
        place_alert_page.enter_address_line1("test")
        place_alert_page.enter_address_line2("test")
        place_alert_page.enter_city("")  # Missing city
        place_alert_page.select_state("Alaska")
        place_alert_page.enter_zip_code("67567")

    with allure.step("Submit the alert placement form"):
        place_alert_page.proceed_to_next_step()

    with allure.step("Verify error message for missing city"):
        error_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'City is required')]"))
        )
        assert error_message.is_displayed(), "Error message for missing city is not displayed"
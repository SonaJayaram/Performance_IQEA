from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.window import WindowTypes
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import pytest
import allure
from output.page_file_generator.EqufixPlaceOnAlert import EqufixPlaceOnAlert
from output.page_file_generator.EqufixHomepage import EqufixHomePage

@pytest.fixture(scope="function")
def setup():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(), options=options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

@allure.feature("Equifax Alert Placement")
@allure.story("TC04 - Place Alert - Invalid Phone Number")
def test_place_alert_invalid_phone_number(setup):
    driver = setup
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    driver.get(base_url)
    equfix_homepage = EqufixHomePage(driver)
    equfix_place_on_alert = EqufixPlaceOnAlert(driver)

    with allure.step("Click on 'Place an Alert' button"):
        equfix_homepage.click_place_an_alert()

    with allure.step("Switch to new window"):
        equfix_homepage.switch_to_new_window()

    with allure.step("Perform alert placement flow with invalid phone number"):
        equfix_place_on_alert.enter_first_name("test")
        equfix_place_on_alert.enter_last_name("test")
        equfix_place_on_alert.enter_ssn("***-**-6686")
        equfix_place_on_alert.enter_phone_number("2143")
        equfix_place_on_alert.enter_dob("04/22/1990")
        equfix_place_on_alert.enter_address("test")
        equfix_place_on_alert.enter_city("test")
        equfix_place_on_alert.enter_address_line_2("test")
        equfix_place_on_alert.enter_zip_code("78686")
        equfix_place_on_alert.click_continue_button()

    with allure.step("Verify error message for invalid phone number"):
        # Scroll to top (if message appears near top)
        driver.execute_script("window.scrollTo(0, 0);")

        try:
            # Try to locate the error message element
            error_message = driver.find_element(By.XPATH, "//span[contains(text(), 'Please enter 10 digits')]")
            assert error_message.is_displayed(), "❌ Error message for invalid phone number is not displayed"
            allure.attach("Error message displayed successfully", name="UI Verification",
                          attachment_type=allure.attachment_type.TEXT)
        except NoSuchElementException:
            # Fail the test if element not found
            assert False, "❌ Error message element not found on UI"
@allure.feature("Equifax Alert Placement")
@allure.story("TC04 - Place an Alert - Empty SSN Validation")
def test_place_alert_empty_ssn_validation(setup):
    driver = setup
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    driver.get(base_url)
    equfix_homepage = EqufixHomePage(driver)
    equfix_place_on_alert = EqufixPlaceOnAlert(driver)

    with allure.step("Click on 'Place an Alert' button"):
        equfix_homepage.click_place_an_alert()

    with allure.step("Switch to new window"):
        equfix_homepage.switch_to_new_window()

    with allure.step("Perform alert placement flow with empty SSN"):
        equfix_place_on_alert.enter_first_name("test")
        equfix_place_on_alert.enter_last_name("test")
        equfix_place_on_alert.enter_ssn("")  # Empty SSN
        equfix_place_on_alert.enter_phone_number("786-876-1234")
        equfix_place_on_alert.enter_dob("04/22/1990")
        equfix_place_on_alert.enter_address("test")
        equfix_place_on_alert.enter_city("test")
        equfix_place_on_alert.enter_address_line_2("test")
        equfix_place_on_alert.enter_zip_code("78686")
        equfix_place_on_alert.click_continue_button()

    with allure.step("Verify error message for empty SSN"):
        driver.execute_script("window.scrollTo(0, 0);")
        error_message = equfix_place_on_alert.wait_for_element((By.XPATH, "//span[contains(text(), 'Please enter 9 digits.')]"))
        assert error_message.is_displayed(), "Error message for empty SSN is not displayed"

@allure.feature("Equifax Alert Placement")
@allure.story("TC05 - Place Alert - Future Date of Birth")
def test_place_alert_future_dob(setup):
    driver = setup
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    driver.get(base_url)
    equfix_homepage = EqufixHomePage(driver)
    equfix_place_on_alert = EqufixPlaceOnAlert(driver)

    with allure.step("Click on 'Place an Alert' button"):
        equfix_homepage.click_place_an_alert()

    with allure.step("Switch to new window"):
        equfix_homepage.switch_to_new_window()

    with allure.step("Perform alert placement flow with future date of birth"):
        equfix_place_on_alert.enter_first_name("test")
        equfix_place_on_alert.enter_last_name("test")
        equfix_place_on_alert.enter_ssn("***-**-6686")
        equfix_place_on_alert.enter_phone_number("786-876-1234")
        equfix_place_on_alert.enter_dob("04/22/2090")  # Future DOB
        equfix_place_on_alert.enter_address("test")
        equfix_place_on_alert.enter_city("test")
        equfix_place_on_alert.enter_address_line_2("test")
        equfix_place_on_alert.enter_zip_code("78686")
        equfix_place_on_alert.click_continue_button()

    with allure.step("Verify error message for future date of birth"):
        driver.execute_script("window.scrollTo(0, 0);")
        error_message = equfix_place_on_alert.wait_for_element((By.XPATH, "//span[contains(text(), 'You must be 18 or older to register for myEquifax.')]"))
        assert error_message.is_displayed(), "Error message for future date of birth is not displayed"
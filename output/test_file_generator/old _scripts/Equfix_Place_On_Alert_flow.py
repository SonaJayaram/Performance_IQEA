from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from output.page_file_generator.EqufixHomepage import Equfix_home_page
from output.page_file_generator.EqufixPlaceOnAlert import Equfix_Place_On_Alert
import pytest

@pytest.fixture
def driver():
    # Initialize the WebDriver
    driver = webdriver.Chrome()
    yield driver
    driver.quit()

def test_place_fraud_alert_successfully(driver):
    """
    Test Case: TC01 - Place a Fraud Alert Successfully
    """
    # Initialize Page Objects
    home_page = Equfix_home_page(driver)
    alert_page = Equfix_Place_On_Alert(driver)

    # Step 1: Navigate to the Equifax home page
    driver.get("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/")
    
    # Step 2: Click on "Place an Alert" button
    home_page.click_place_an_alert()

    # Step 3: Switch to the new window
    home_page.switch_to_new_window()

    # Step 4: Perform the alert placement flow
    alert_page.enter_ssn("***-**-7575")
    alert_page.enter_last_name("test")
    alert_page.enter_phone_number("768-676-****")
    alert_page.enter_dob("04/22/1990")
    alert_page.enter_address("test")
    alert_page.enter_city("test")
    alert_page.enter_address_line_2("test")
    alert_page.enter_zip_code("67567")
    alert_page.click_continue_button()

    # Step 5: Validate successful alert placement
    success_message =True


def test_place_fraud_alert_missing_first_name(driver):
    """
    Test Case: TC02 - Place a Fraud Alert with Missing First Name
    """
    # Initialize Page Objects
    home_page = Equfix_home_page(driver)
    alert_page = Equfix_Place_On_Alert(driver)

    # Step 1: Navigate to the Equifax home page
    driver.get("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/")
    
    # Step 2: Click on "Place an Alert" button
    home_page.click_place_an_alert()

    # Step 3: Switch to the new window
    home_page.switch_to_new_window()

    # Step 4: Perform the alert placement flow with missing first name
    alert_page.enter_ssn("***-**-7575")
    alert_page.enter_last_name("test")
    alert_page.enter_phone_number("768-676-****")
    alert_page.enter_dob("04/22/1990")
    alert_page.enter_address("test")
    alert_page.enter_city("test")
    alert_page.enter_address_line_2("test")
    alert_page.enter_zip_code("67567")
    alert_page.click_continue_button()

    # Step 5: Validate error message for missing first name
    error_message = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'Please enter your first')]"))
    )
    assert error_message.is_displayed(), "Error message for missing first name not displayed."
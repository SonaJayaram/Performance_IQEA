from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from output.page_file_generator.EqufixHomepage import Equfix_home_page
from output.page_file_generator.EqufixPlaceOnAlert import Equfix_Place_On_Alert
import pytest

@pytest.fixture(scope="function")
def driver():
    # Initialize the WebDriver
    driver = webdriver.Chrome()
    yield driver
    driver.quit()

@pytest.fixture(scope="function")
def equfix_home_page(driver):
    # Initialize the Equfix_home_page object
    return Equfix_home_page(driver)

@pytest.fixture(scope="function")
def equfix_place_on_alert(driver):
    # Initialize the Equfix_Place_On_Alert object
    return Equfix_Place_On_Alert(driver)

def test_tc01_place_fraud_alert_positive_flow(driver, equfix_home_page, equfix_place_on_alert):
    # Step 1: Launch the application
    driver.get("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/")
    
    # Step 2: Wait for the "Place an Alert" button and click it
    equfix_home_page.wait_for_element(By.XPATH, "//button[contains(text(), 'Place an Alert')]")
    equfix_home_page.click_place_an_alert()
    
    # Step 3: Switch to the new window
    equfix_home_page.switch_to_new_window()
    
    # Step 4: Enter SSN
    equfix_place_on_alert.enter_ssn("***-**-7575")
    
    # Step 5: Enter Last Name
    equfix_place_on_alert.enter_last_name("test")
    
    # Step 6: Enter Phone Number
    equfix_place_on_alert.enter_phone_number("768-676-****")
    
    # Step 7: Enter Date of Birth
    equfix_place_on_alert.enter_dob("04/22/1990")
    
    # Step 8: Enter Address Line 1
    equfix_place_on_alert.enter_address("test")
    
    # Step 9: Enter City
    equfix_place_on_alert.enter_city("test")
    
    # Step 10: Enter Address Line 2
    equfix_place_on_alert.enter_address_line_2("test")
    
    # Step 11: Select State (Alaska)
    equfix_place_on_alert.select_state_alaska()
    
    # Step 12: Enter Zip Code
    equfix_place_on_alert.enter_zip_code("67567")
    
    # Step 13: Click Continue Button
    equfix_place_on_alert.click_continue_button()
    
    # Step 14: Validate successful alert placement
    success_message = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Alert placed successfully')]"))
    )
    assert success_message.is_displayed(), "Success message not displayed"

def test_tc02_place_fraud_alert_negative_flow_missing_first_name(driver, equfix_home_page, equfix_place_on_alert):
    # Step 1: Launch the application
    driver.get("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/")
    
    # Step 2: Wait for the "Place an Alert" button and click it
    equfix_home_page.wait_for_element(By.XPATH, "//button[contains(text(), 'Place an Alert')]")
    equfix_home_page.click_place_an_alert()
    
    # Step 3: Switch to the new window
    equfix_home_page.switch_to_new_window()
    
    # Step 4: Enter SSN
    equfix_place_on_alert.enter_ssn("***-**-7575")
    
    # Step 5: Enter Last Name
    equfix_place_on_alert.enter_last_name("test")
    
    # Step 6: Enter Phone Number
    equfix_place_on_alert.enter_phone_number("768-676-****")
    
    # Step 7: Enter Date of Birth
    equfix_place_on_alert.enter_dob("04/22/1990")
    
    # Step 8: Enter Address Line 1
    equfix_place_on_alert.enter_address("test")
    
    # Step 9: Enter City
    equfix_place_on_alert.enter_city("test")
    
    # Step 10: Enter Address Line 2
    equfix_place_on_alert.enter_address_line_2("test")
    
    # Step 11: Select State (Alaska)
    equfix_place_on_alert.select_state_alaska()
    
    # Step 12: Enter Zip Code
    equfix_place_on_alert.enter_zip_code("67567")
    
    # Step 13: Click Continue Button
    equfix_place_on_alert.click_continue_button()
    
    # Step 14: Validate error message for missing first name
    error_message = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'First Name is required')]"))
    )
    assert error_message.is_displayed(), "Error message for missing first name not displayed"
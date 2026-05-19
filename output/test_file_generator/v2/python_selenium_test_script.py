from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import allure
import pytest

from output.page_file_generator.Equfix_Place_On_Alert_selenium import Equfix_Place_On_Alert
from output.page_file_generator.Equfix_home_page_palywright import Equfix_home_page


@pytest.fixture(scope="function")
def setup():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()


def switch_to_new_window(driver):
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])


def helper_click_element(driver, locator):
    with allure.step(f"Clicking on element with locator: {locator}"):
        try:
           driver.find_element(By.XPATH, locator).click()
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name="Error Screenshot", attachment_type=allure.attachment_type.PNG)
            raise e


def helper_enter_text(driver, locator, text):
    with allure.step(f"Entering text '{text}' into element with locator: {locator}"):
        try:
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, locator)))
            element.clear()
            element.send_keys(text)
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name="Error Screenshot", attachment_type=allure.attachment_type.PNG)
            raise e


@allure.epic("Equifax Automation")
@allure.feature("Place an Alert")
@allure.story("TC01 - Place an Alert - Successful Form Submission")
def test_place_alert_successful_submission(setup):
    driver = setup
    equfix_home_page = Equfix_home_page(driver)
    equfix_place_on_alert = Equfix_Place_On_Alert(driver)

    with allure.step("Navigating to Equifax home page"):
        driver.get("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/")
        allure.attach(driver.get_screenshot_as_png(), name="Home Page", attachment_type=allure.attachment_type.PNG)

    with allure.step("Closing banner"):
        equfix_home_page.close_banner()

    with allure.step("Clicking on 'Place an Alert'"):
        equfix_home_page.place_alert()

    with allure.step("Switching to new window"):
        switch_to_new_window(driver)

    with allure.step("Filling out personal information"):
        equfix_place_on_alert.fill_first_name("test")
        equfix_place_on_alert.fill_last_name("test")
        equfix_place_on_alert.fill_ssn("***-**-6686")
        helper_enter_text(driver, "input[name='phoneNumber']", "786-876-****")
        helper_enter_text(driver, "input[name='dateOfBirthMasked']", "04/22/1990")
        helper_enter_text(driver, "input[name='addressLine1']", "test")
        helper_enter_text(driver, "input[name='cityName']", "test")
        helper_enter_text(driver, "input[name='addressLine2']", "test")


        helper_enter_text(driver, "input[name='zipCode']", "78686")



    with allure.step("Validating successful submission"):

        allure.attach(driver.get_screenshot_as_png(), name="Success Message", attachment_type=allure.attachment_type.PNG)


@allure.epic("Equifax Automation")
@allure.feature("Place an Alert")
@allure.story("TC04 - Place an Alert - Empty SSN Validation")
def test_place_alert_empty_ssn_validation(setup):
    driver = setup
    equfix_home_page = Equfix_home_page(driver)
    equfix_place_on_alert = Equfix_Place_On_Alert(driver)

    with allure.step("Navigating to Equifax home page"):
        driver.get("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/")
        allure.attach(driver.get_screenshot_as_png(), name="Home Page", attachment_type=allure.attachment_type.PNG)


    with allure.step("Clicking on 'Place an Alert'"):
        equfix_home_page.place_alert()

    with allure.step("Switching to new window"):
        switch_to_new_window(driver)

    with allure.step("Filling out personal information without SSN"):
        equfix_place_on_alert.fill_first_name("test")
        equfix_place_on_alert.fill_last_name("test")
        helper_enter_text(driver, "input[name='phoneNumber']", "786-876-****")
        helper_enter_text(driver, "input[name='dateOfBirthMasked']", "04/22/1990")
        helper_enter_text(driver, "input[name='addressLine1']", "test")
        helper_enter_text(driver, "input[name='cityName']", "test")
        helper_enter_text(driver, "input[name='addressLine2']", "test")
        helper_enter_text(driver, "input[name='zipCode']", "78686")

    with allure.step("Submitting the form"):
        helper_click_element(driver, "button[type='submit']")
        allure.attach(driver.get_screenshot_as_png(), name="Form Submitted", attachment_type=allure.attachment_type.PNG)

    with allure.step("Validating empty SSN error message"):
        error_message = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class,'error-message')]"))).text
        assert "SSN is required" in error_message
        allure.attach(driver.get_screenshot_as_png(), name="Error Message", attachment_type=allure.attachment_type.PNG)


@allure.epic("Equifax Automation")
@allure.feature("Place an Alert")
@allure.story("TC04 - Place Alert - Invalid Phone Number")
def test_place_alert_invalid_phone_number(setup):
    driver = setup
    equfix_home_page = Equfix_home_page(driver)
    equfix_place_on_alert = Equfix_Place_On_Alert(driver)

    with allure.step("Navigating to Equifax home page"):
        driver.get("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/")
        allure.attach(driver.get_screenshot_as_png(), name="Home Page", attachment_type=allure.attachment_type.PNG)


    with allure.step("Clicking on 'Place an Alert'"):
        equfix_home_page.place_alert()

    with allure.step("Switching to new window"):
        switch_to_new_window(driver)

    with allure.step("Filling out personal information with invalid phone number"):
        equfix_place_on_alert.fill_first_name("test")
        equfix_place_on_alert.fill_last_name("test")
        equfix_place_on_alert.fill_ssn("***-**-6686")
        helper_enter_text(driver, "input[name='phoneNumber']", "2123")
        helper_enter_text(driver, "input[name='dateOfBirthMasked']", "04/22/1990")


    with allure.step("Submitting the form"):
        helper_click_element(driver, "button[type='submit']")
        allure.attach(driver.get_screenshot_as_png(), name="Form Submitted", attachment_type=allure.attachment_type.PNG)

    with allure.step("Validating invalid phone number error message"):
        error_message = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class,'error-message')]"))).text
        assert "Invalid phone number" in error_message
        allure.attach(driver.get_screenshot_as_png(), name="Error Message", attachment_type=allure.attachment_type.PNG)
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from allure_commons.types import AttachmentType
import allure
from output.page_file_generator.EqufixHomepage import EqufixHomepage
from output.page_file_generator.EqufixPlaceOnAlert import EqufixPlaceOnAlert

@pytest.fixture(scope="function")
def setup():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(), options=options)
    driver.implicitly_wait(5)
    yield driver
    driver.quit()

@allure.step("Switch to new window")
def switch_to_new_window(driver):
    original_window = driver.current_window_handle
    WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
    for window_handle in driver.window_handles:
        if window_handle != original_window:
            driver.switch_to.window(window_handle)
            break

@allure.step("Enter text in field")
def enter_text_via_locator(driver, locator, text):
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located(locator))
    element.clear()
    element.send_keys(text)

@allure.step("Click element")
def click_via_locator(driver, locator):
    element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(locator))
    element.click()

@allure.feature("Place Alert")
@allure.story("TC07 - Place Alert - Missing City")
def test_place_alert_missing_city(setup):
    driver = setup
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    driver.get(base_url)

    homepage = EqufixHomepage(driver)
    place_on_alert = EqufixPlaceOnAlert(driver)

    with allure.step("Perform Equifax homepage flow"):
        homepage.click_place_an_alert()
        switch_to_new_window(driver)

    with allure.step("Perform alert placement flow with missing city"):
        place_on_alert.enter_first_name("test")
        place_on_alert.enter_last_name("test")
        place_on_alert.enter_ssn("***-**-6686")
        place_on_alert.enter_phone_number("786-876-****")
        place_on_alert.enter_dob("04/22/1990")
        place_on_alert.enter_address("test")
        place_on_alert.enter_address_line_2("test")
        place_on_alert.select_state_alaska()
        place_on_alert.enter_zip_code("78686")
        place_on_alert.click_continue_button()

    with allure.step("Verify error message for missing city"):
        error_message_locator = (By.XPATH, "//div[contains(text(), 'City is required')]")
        error_message = WebDriverWait(driver, 10).until(EC.presence_of_element_located(error_message_locator))
        assert error_message.is_displayed(), "Error message for missing city is not displayed"

@allure.feature("Place Alert")
@allure.story("TC01 - Place Alert - Successful DataEntry")
def test_place_alert_successful_data_entry(setup):
    driver = setup
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    driver.get(base_url)

    homepage = EqufixHomepage(driver)
    place_on_alert = EqufixPlaceOnAlert(driver)

    with allure.step("Perform Equifax homepage flow"):
        homepage.click_place_an_alert()
        switch_to_new_window(driver)

    with allure.step("Perform alert placement flow with valid data"):
        place_on_alert.enter_first_name("test")
        place_on_alert.enter_last_name("test")
        place_on_alert.enter_ssn("***-**-6686")
        place_on_alert.enter_phone_number("786-876-****")
        place_on_alert.enter_dob("04/22/1990")
        place_on_alert.enter_address("test")
        place_on_alert.enter_address_line_2("test")
        place_on_alert.enter_city("test")
        place_on_alert.select_state_alaska()
        place_on_alert.enter_zip_code("78686")
        place_on_alert.click_continue_button()

    with allure.step("Verify success message"):
        success_message_locator = (By.XPATH, "//div[contains(text(), 'Alert placed successfully')]")
        success_message = WebDriverWait(driver, 10).until(EC.presence_of_element_located(success_message_locator))
        assert success_message.is_displayed(), "Success message is not displayed"

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        if "setup" in item.fixturenames:
            driver = item.funcargs["setup"]
            allure.attach(driver.get_screenshot_as_png(), name="screenshot", attachment_type=AttachmentType.PNG)
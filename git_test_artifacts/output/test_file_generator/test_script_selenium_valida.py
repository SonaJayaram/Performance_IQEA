import pytest
import allure
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from output.page_file_generator.Equfix_home_page_selenium import Equfix_home_page_selenium
from output.page_file_generator.Equfix_Place_On_Alert_selenium import Equfix_Place_On_Alert_selenium

@pytest.fixture(scope="function")
def driver_setup():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    # 🔥 Load your base URL here
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    driver.get(base_url)
    home_page = Equfix_home_page_selenium(driver)
    alert_page = Equfix_Place_On_Alert_selenium(driver)
    yield driver, home_page, alert_page
    driver.quit()

def switch_to_new_window(driver, timeout=10):
    with allure.step("Switching to new window"):
        try:
            WebDriverWait(driver, timeout).until(lambda d: len(d.window_handles) > 1)
            driver.switch_to.window(driver.window_handles[-1])
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name="Switch Window Error", attachment_type=allure.attachment_type.PNG)
            raise RuntimeError("New window did not appear within timeout") from e

def helper_enter_text(driver, locator, text, step_name):
    with allure.step(f"Entering text '{text}' into element {locator}"):
        try:
            element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, locator)))
            element.clear()
            element.send_keys(text)
            allure.attach(driver.get_screenshot_as_png(), name=step_name, attachment_type=allure.attachment_type.PNG)
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name=f"{step_name}_error", attachment_type=allure.attachment_type.PNG)
            raise e

def helper_click_element(driver, locator, step_name):
    with allure.step(f"Clicking on element {locator}"):
        try:
            element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, locator)))
            element.click()
            allure.attach(driver.get_screenshot_as_png(), name=step_name, attachment_type=allure.attachment_type.PNG)
        except Exception as e:
            try:
                driver.execute_script("arguments[0].click();", element)
                allure.attach(driver.get_screenshot_as_png(), name=f"{step_name}_js_click", attachment_type=allure.attachment_type.PNG)
            except Exception as js_e:
                allure.attach(driver.get_screenshot_as_png(), name=f"{step_name}_error", attachment_type=allure.attachment_type.PNG)
                raise js_e

@pytest.mark.parametrize("test_data", [
    {
        "test_case_name": "TC03 - Place Alert - Missing Last Name",
        "ssn": "***-**-7575",
        "last_name": "",
        "phone_number": "768-676-****",
        "dob": "04/22/1990",
        "address_line1": "test",
        "city": "test",
        "state": "Alaska",
        "zip_code": "67567",
        "expected_error": "Please enter your last name (1-25 Characters)"
    },
    {
        "test_case_name": "TC04 - Place Alert - Invalid Phone Number",
        "ssn": "***-**-7575",
        "last_name": "test",
        "phone_number": "invalid-phone",
        "dob": "04/22/1990",
        "address_line1": "test",
        "city": "test",
        "state": "Alaska",
        "zip_code": "67567",
        "expected_error": "Please enter 10 digits."
    },
    {
        "test_case_name": "TC02 - Place Alert - Invalid SSN",
        "ssn": "invalid-ssn",
        "last_name": "test",
        "phone_number": "768-676-****",
        "dob": "04/22/1990",
        "address_line1": "test",
        "city": "test",
        "state": "Alaska",
        "zip_code": "67567",
        "expected_error": "Please enter 9 digits."
    }
])
def test_place_alert(driver_setup, test_data):
    driver, home_page, alert_page = driver_setup
    with allure.step(f"Starting test case: {test_data['test_case_name']}"):
        try:
            home_page.click_element("place_an_alert_btn")
            switch_to_new_window(driver)

            helper_enter_text(driver, "//input[@id='ssn']", test_data["ssn"], "Enter SSN")
            helper_enter_text(driver, "//input[@id='lastName']", test_data["last_name"], "Enter Last Name")
            helper_enter_text(driver, "//input[@id='phoneNumber']", test_data["phone_number"], "Enter Phone Number")


            with allure.step("Submitting the form"):
                helper_click_element(driver, "//button[@id='continue-button']", "Click Submit Button")

            with allure.step("Validating error message"):
                expected = test_data["expected_error"]

                # XPath that searches ANY element containing the expected error text
                xpath = f"//*[contains(normalize-space(text()), \"{expected}\")]"

                element = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, xpath))
                )

                actual = element.text

                allure.attach(driver.get_screenshot_as_png(), name="Error Message",
                              attachment_type=allure.attachment_type.PNG)

                assert expected in actual, f"Expected '{expected}' but found '{actual}'"
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name="Test Failure", attachment_type=allure.attachment_type.PNG)
            allure.attach(driver.page_source, name="Page Source", attachment_type=allure.attachment_type.HTML)
            raise e
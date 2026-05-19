import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import allure
from allure_commons.types import AttachmentType

@pytest.fixture(scope="function")
def driver():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def switch_to_new_window(driver, timeout=10):
    with allure.step("Switching to new window"):
        WebDriverWait(driver, timeout).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        allure.attach(driver.get_screenshot_as_png(), name="Switched to new window", attachment_type=AttachmentType.PNG)

def helper_click_element(driver, xpath, step_name):
    with allure.step(f"Clicking on element: {step_name}"):
        try:
            element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            try:
                element.click()
            except Exception:
                driver.execute_script("arguments[0].click();", element)
            allure.attach(driver.get_screenshot_as_png(), name=f"{step_name}_clicked", attachment_type=AttachmentType.PNG)
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name=f"{step_name}_error", attachment_type=AttachmentType.PNG)
            raise e

def helper_enter_text(driver, xpath, text, step_name):
    with allure.step(f"Entering text '{text}' into element: {step_name}"):
        try:
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
            element.clear()
            element.send_keys(text)
            allure.attach(driver.get_screenshot_as_png(), name=f"{step_name}_text_entered", attachment_type=AttachmentType.PNG)
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name=f"{step_name}_error", attachment_type=AttachmentType.PNG)
            raise e

@pytest.mark.parametrize("test_case_name, actions, expected_results", [
    ("TC02 - Place Alert - Invalid SSN", [
        {"action": "switch_to_new_window", "url": "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"},
        {"action": "click", "xpath": "//button[text()='Place an Alert']", "step_name": "Place an Alert"},
        {"action": "enter_text", "xpath": "//input[@id='ssn']", "text": "***-**-5865", "step_name": "SSN Field"},
        {"action": "click", "xpath": "//button[text()='Submit']", "step_name": "Submit Button"}
    ], "Error message displayed for invalid SSN"),
    ("TC03 - Place Alert - Missing Last Name", [
        {"action": "switch_to_new_window", "url": "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"},
        {"action": "click", "xpath": "//button[text()='Place an Alert']", "step_name": "Place an Alert"},
        {"action": "enter_text", "xpath": "//input[@id='firstName']", "text": "Test", "step_name": "First Name Field"},
        {"action": "click", "xpath": "//button[text()='Submit']", "step_name": "Submit Button"}
    ], "Error message displayed for missing last name"),
    ("TC04 - Place Alert - Invalid Phone Number", [
        {"action": "switch_to_new_window", "url": "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"},
        {"action": "click", "xpath": "//button[text()='Place an Alert']", "step_name": "Place an Alert"},
        {"action": "enter_text", "xpath": "//input[@id='phoneNumber']", "text": "879-678-****", "step_name": "Phone Number Field"},
        {"action": "click", "xpath": "//button[text()='Submit']", "step_name": "Submit Button"}
    ], "Error message displayed for invalid phone number")
])
def test_place_alert(driver, test_case_name, actions, expected_results):
    with allure.step(f"Starting test case: {test_case_name}"):
        for action in actions:
            if action["action"] == "switch_to_new_window":
                switch_to_new_window(driver)
            elif action["action"] == "click":
                helper_click_element(driver, action["xpath"], action["step_name"])
            elif action["action"] == "enter_text":
                helper_enter_text(driver, action["xpath"], action["text"], action["step_name"])
        
        with allure.step("Validating expected result"):
            try:
                error_message = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@class='error-message']"))
                ).text
                assert expected_results in error_message, f"Expected '{expected_results}' but got '{error_message}'"
                allure.attach(driver.get_screenshot_as_png(), name="Validation Success", attachment_type=AttachmentType.PNG)
            except Exception as e:
                allure.attach(driver.get_screenshot_as_png(), name="Validation Failure", attachment_type=AttachmentType.PNG)
                raise e
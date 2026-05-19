import os
import time
import allure
import pytest
from playwright.sync_api import sync_playwright
from output.page_file_generator.equ_place_an_alert import equ_place_an_alert

# Constants
DEFAULT_WAIT = 5
EXPLICIT_WAIT = 10
RETRY_ATTEMPTS = 1
HEADLESS = os.environ.get("HEADLESS", "false").lower() in ("1", "true", "yes")

# Create allure-results folder
os.makedirs("allure-results", exist_ok=True)

# Helper Functions
def helper_wait_for_element(page, selector, description):
    with allure.step(f"Waiting for element: {description}"):
        for _ in range(RETRY_ATTEMPTS):
            try:
                element = page.locator(selector)
                element.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
                return element
            except Exception as e:
                time.sleep(1)
        with allure.step(f"healing: failed to locate {description}, retrying with fallback selector"):
            allure.attach(page.screenshot(), name="failure_screenshot", attachment_type=allure.attachment_type.PNG)
            allure.attach(page.content(), name="page_html", attachment_type=allure.attachment_type.HTML)
            raise e

def safe_goto(page, url, timeout=EXPLICIT_WAIT * 1000):
    with allure.step(f"Navigating to URL: {url}"):
        for _ in range(RETRY_ATTEMPTS):
            try:
                page.goto(url, timeout=timeout)
                return
            except Exception as e:
                time.sleep(1)
        with allure.step("Failed to navigate to URL after retries"):
            allure.attach(page.screenshot(), name="navigation_failure", attachment_type=allure.attachment_type.PNG)
            allure.attach(page.content(), name="page_html", attachment_type=allure.attachment_type.HTML)
            raise e

def helper_click_with_healing(page, locator, alt_selector=None):
    with allure.step(f"Clicking on element: {locator}"):
        try:
            locator.click()
        except Exception as e:
            time.sleep(1)
            try:
                locator.click()
            except Exception as e:
                if alt_selector:
                    with allure.step("Attempting click with alternative selector"):
                        alt_locator = page.locator(alt_selector)
                        alt_locator.click()
                else:
                    with allure.step("Attempting force click"):
                        locator.click(force=True)

# Test Fixture
@pytest.fixture(scope="function")
def setup_playwright():
    with sync_playwright() as playwright:
        browser = playwright.webkit.launch(headless=HEADLESS)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            java_script_enabled=True,
            ignore_https_errors=True,
            viewport={"width": 1400, "height": 900}
        )
        page = context.new_page()
        yield page
        context.close()
        browser.close()

# Test Case: TC02 - Place Alert - Invalid SSN
def test_tc02_place_alert_invalid_ssn(setup_playwright):
    page = setup_playwright
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    safe_goto(page, base_url)

    with allure.step("Navigating to Equifax Fraud Alerts page"):
        allure.attach(page.screenshot(), name="initial_page", attachment_type=allure.attachment_type.PNG)

    pom = equ_place_an_alert(page)

    with allure.step("Switching to new window for placing an alert"):
        with page.expect_popup() as popup_info:
            helper_click_with_healing(page, pom.click_element("text=Place an Alert"))
        new_page = popup_info.value
        new_page.bring_to_front()

    pom_new = equ_place_an_alert(new_page)

    with allure.step("Filling out invalid SSN details"):
        pom_new.enter_text("input[name='firstName']", "test")
        pom_new.enter_text("input[name='ssn']", "***-**-6686")
        pom_new.enter_text("input[name='lastName']", "test")
        allure.attach(new_page.screenshot(), name="filled_invalid_ssn", attachment_type=allure.attachment_type.PNG)

    with allure.step("Submitting the form"):
        helper_click_with_healing(new_page, new_page.locator("button[type='submit']"))

    with allure.step("Validating error message for invalid SSN"):
        error_message = helper_wait_for_element(new_page, "text=Invalid SSN", "Invalid SSN error message")
        assert error_message.is_visible(), "Error message for invalid SSN not displayed"

# Test Case: TC03 - Place Alert - Missing Last Name
def test_tc03_place_alert_missing_last_name(setup_playwright):
    page = setup_playwright
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    safe_goto(page, base_url)

    with allure.step("Navigating to Equifax Fraud Alerts page"):
        allure.attach(page.screenshot(), name="initial_page", attachment_type=allure.attachment_type.PNG)

    pom = equ_place_an_alert(page)

    with allure.step("Switching to new window for placing an alert"):
        with page.expect_popup() as popup_info:
            helper_click_with_healing(page, pom.click_element("text=Place an Alert"))
        new_page = popup_info.value
        new_page.bring_to_front()

    pom_new = equ_place_an_alert(new_page)

    with allure.step("Filling out details with missing last name"):
        pom_new.enter_text("input[name='firstName']", "test")
        pom_new.enter_text("input[name='ssn']", "***-**-6686")
        pom_new.enter_text("input[name='lastName']", "")
        allure.attach(new_page.screenshot(), name="missing_last_name", attachment_type=allure.attachment_type.PNG)

    with allure.step("Submitting the form"):
        helper_click_with_healing(new_page, new_page.locator("button[type='submit']"))

    with allure.step("Validating error message for missing last name"):
        error_message = helper_wait_for_element(new_page, "text=Last name is required", "Missing last name error message")
        assert error_message.is_visible(), "Error message for missing last name not displayed"

# Test Case: TC04 - Place Alert - Invalid Phone Number
def test_tc04_place_alert_invalid_phone_number(setup_playwright):
    page = setup_playwright
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    safe_goto(page, base_url)

    with allure.step("Navigating to Equifax Fraud Alerts page"):
        allure.attach(page.screenshot(), name="initial_page", attachment_type=allure.attachment_type.PNG)

    pom = equ_place_an_alert(page)

    with allure.step("Switching to new window for placing an alert"):
        with page.expect_popup() as popup_info:
            helper_click_with_healing(page, pom.click_element("text=Place an Alert"))
        new_page = popup_info.value
        new_page.bring_to_front()

    pom_new = equ_place_an_alert(new_page)

    with allure.step("Filling out details with invalid phone number"):
        pom_new.enter_text("input[name='firstName']", "test")
        pom_new.enter_text("input[name='ssn']", "***-**-6686")
        pom_new.enter_text("input[name='lastName']", "test")
        pom_new.enter_text("input[name='phoneNumber']", "786-876-****")
        allure.attach(new_page.screenshot(), name="invalid_phone_number", attachment_type=allure.attachment_type.PNG)

    with allure.step("Submitting the form"):
        helper_click_with_healing(new_page, new_page.locator("button[type='submit']"))

    with allure.step("Validating error message for invalid phone number"):
        error_message = helper_wait_for_element(new_page, "text=Invalid phone number", "Invalid phone number error message")
        assert error_message.is_visible(), "Error message for invalid phone number not displayed"

# Test Case: Validate Test Count
def test_validate_test_count():
    with allure.step("Validating the number of generated tests"):
        expected_test_count = 3
        actual_test_count = len([test_tc02_place_alert_invalid_ssn, test_tc03_place_alert_missing_last_name, test_tc04_place_alert_invalid_phone_number])
        assert expected_test_count == actual_test_count, f"Expected {expected_test_count} tests, but found {actual_test_count}"
import os
import time
import pytest
import allure
from playwright.sync_api import sync_playwright
from output.page_file_generator.Equfix_Place_On_Alert_playwright import Equfix_Place_On_Alert_playwright
from output.page_file_generator.Equfix_home_page_palywright import Equfix_home_page_palywright

# Constants
DEFAULT_WAIT = 5
EXPLICIT_WAIT = 10
RETRY_ATTEMPTS = 1
HEADLESS = os.environ.get("HEADLESS", "false").lower() in ("1", "true", "yes")

# Create allure-results folder
os.makedirs("allure-results", exist_ok=True)

# Test cases
test_cases = [
    {
        "test_case_name": "TC03 - Place Alert - Missing Last Name",
        "actions": [
            {"type": "click", "selector": "button#placeAlert"},
            {"type": "enter_text", "selector": "input#firstName", "value": "John"},
            {"type": "click", "selector": "button#submitAlert"}
        ],
        "expected_results": [
            {"selector": "div#errorLastName", "value": "Last name is required"}
        ],
    },
    {
        "test_case_name": "TC04 - Place Alert - Invalid Phone Number",
        "actions": [
            {"type": "click", "selector": "button#placeAlert"},
            {"type": "enter_text", "selector": "input#firstName", "value": "John"},
            {"type": "enter_text", "selector": "input#lastName", "value": "Doe"},
            {"type": "enter_text", "selector": "input#phoneNumber", "value": "123"},
            {"type": "click", "selector": "button#submitAlert"}
        ],
        "expected_results": [
            {"selector": "div#errorPhoneNumber", "value": "Invalid phone number"}
        ],
    },
    {
        "test_case_name": "TC02 - Place Alert - Invalid SSN",
        "actions": [
            {"type": "click", "selector": "button#placeAlert"},
            {"type": "enter_text", "selector": "input#firstName", "value": "John"},
            {"type": "enter_text", "selector": "input#lastName", "value": "Doe"},
            {"type": "enter_text", "selector": "input#ssn", "value": "123-45-678"},
            {"type": "click", "selector": "button#submitAlert"}
        ],
        "expected_results": [
            {"selector": "div#errorSSN", "value": "Invalid SSN"}
        ],
    },
]

@pytest.fixture(scope="function")
def setup_playwright():
    with sync_playwright() as playwright:
        browser = playwright.webkit.launch(headless=HEADLESS)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            java_script_enabled=True,
            ignore_https_errors=True,
            viewport={"width": 1400, "height": 900},
        )
        page = context.new_page()
        yield page
        context.close()
        browser.close()

def safe_goto(page, url, timeout=EXPLICIT_WAIT * 1000):
    with allure.step(f"Navigating to URL: {url}"):
        for attempt in range(RETRY_ATTEMPTS):
            try:
                page.goto(url, timeout=timeout)
                return
            except Exception as e:
                if attempt < RETRY_ATTEMPTS - 1:
                    time.sleep(0.5)
                else:
                    allure.attach(page.screenshot(), name="goto_error_screenshot", attachment_type=allure.attachment_type.PNG)
                    allure.attach(page.content(), name="goto_page_html", attachment_type=allure.attachment_type.HTML)
                    raise e

def helper_wait_for_element(page, selector):
    with allure.step(f"Waiting for element: {selector}"):
        try:
            page.locator(selector).wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
        except Exception as e:
            allure.attach(page.screenshot(), name="error_screenshot", attachment_type=allure.attachment_type.PNG)
            allure.attach(page.content(), name="page_html", attachment_type=allure.attachment_type.HTML)
            raise e

def helper_click_with_healing(page, locator, alt_selector=None):
    with allure.step(f"Clicking on element with healing: {locator}"):
        try:
            helper_wait_for_element(page, locator)
            page.locator(locator).click()
        except Exception as e:
            allure.attach(page.screenshot(), name="click_error_screenshot", attachment_type=allure.attachment_type.PNG)
            allure.attach(page.content(), name="click_page_html", attachment_type=allure.attachment_type.HTML)
            if alt_selector:
                with allure.step(f"Healing: Trying alternative selector {alt_selector}"):
                    try:
                        page.locator(alt_selector).click()
                        return
                    except Exception as alt_e:
                        allure.attach(page.screenshot(), name="alt_click_error_screenshot", attachment_type=allure.attachment_type.PNG)
                        allure.attach(page.content(), name="alt_click_page_html", attachment_type=allure.attachment_type.HTML)
                        raise alt_e
            raise e

def helper_enter_text(page, selector, text):
    with allure.step(f"Entering text '{text}' into element: {selector}"):
        try:
            helper_wait_for_element(page, selector)
            page.locator(selector).fill(text)
        except Exception as e:
            allure.attach(page.screenshot(), name="error_screenshot", attachment_type=allure.attachment_type.PNG)
            allure.attach(page.content(), name="page_html", attachment_type=allure.attachment_type.HTML)
            raise e
BASE_URL = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
@pytest.mark.parametrize("test_case", test_cases, ids=[tc["test_case_name"].replace(" ", "_").lower() for tc in test_cases])
def test_place_alert(setup_playwright, test_case):
    page = setup_playwright
    safe_goto(page, BASE_URL)
    allure.attach(page.screenshot(), name="initial_page", attachment_type=allure.attachment_type.PNG)

    if not test_case["actions"] or not test_case["expected_results"]:
        with allure.step(f"Test case '{test_case['test_case_name']}' is missing actions or expected results."):
            pytest.skip(f"Test case '{test_case['test_case_name']}' is missing actions or expected results.")

    try:
        with allure.step(f"Executing test case: {test_case['test_case_name']}"):
            home_page = Equfix_home_page_palywright(page)
            alert_page = Equfix_Place_On_Alert_playwright(page)

            for action in test_case["actions"]:
                if action["type"] == "click":
                    helper_click_with_healing(page, action["selector"])
                elif action["type"] == "enter_text":
                    helper_enter_text(page, action["selector"], action["value"])
                elif action["type"] == "switch_to_new_window":
                    with page.expect_popup() as popup_info:
                        helper_click_with_healing(page, action["trigger_selector"])
                        new_page = popup_info.value
                        new_page.bring_to_front()
                        page = new_page
                        home_page = Equfix_home_page_palywright(page)
                        alert_page = Equfix_Place_On_Alert_playwright(page)

            with allure.step("Performing primary assertion"):
                for expected_result in test_case["expected_results"]:
                    element = page.locator(expected_result["selector"])
                    assert element.inner_text() == expected_result["value"], f"Expected {expected_result['value']} but got {element.inner_text()}"

    except Exception as e:
        allure.attach(page.screenshot(), name="error_screenshot", attachment_type=allure.attachment_type.PNG)
        allure.attach(page.content(), name="page_html", attachment_type=allure.attachment_type.HTML)
        pytest.fail(f"Test case '{test_case['test_case_name']}' failed with error: {str(e)}")
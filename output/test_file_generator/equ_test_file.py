import os
import time
import allure
import pytest
from playwright.sync_api import sync_playwright, Page, expect
from output.page_file_generator.Equfix_Place_On_Alert_playwright import Equfix_Place_On_Alert_playwright
from output.page_file_generator.Equfix_home_page_palywright import Equfix_home_page_palywright

# Constants
DEFAULT_WAIT = 5
EXPLICIT_WAIT = 10
RETRY_ATTEMPTS = 1
HEADLESS = os.environ.get("HEADLESS", "false").lower() in ("1", "true", "yes")

# Create allure-results folder
os.makedirs("allure-results", exist_ok=True)

# Helper functions
def helper_wait_for_element(page: Page, selector: str):
    with allure.step(f"Waiting for element: {selector}"):
        for _ in range(RETRY_ATTEMPTS):
            try:
                element = page.locator(selector)
                element.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
                return element
            except Exception as e:
                time.sleep(0.5)
        with allure.step(f"healing: failed to find element {selector}, retrying with fallback"):
            allure.attach(page.screenshot(), name="screenshot", attachment_type=allure.attachment_type.PNG)
            allure.attach(page.content(), name="page_html", attachment_type=allure.attachment_type.HTML)
            raise AssertionError(f"Element with selector {selector} not found after retries.")

def helper_click_with_healing(page: Page, locator, alt_selector=None):
    with allure.step(f"Clicking element with healing: {locator}"):
        try:
            locator.click()
        except Exception as e:
            time.sleep(0.5)
            try:
                locator.click()
            except Exception as e:
                if alt_selector:
                    with allure.step(f"Trying alternative selector: {alt_selector}"):
                        alt_locator = page.locator(alt_selector)
                        alt_locator.click()
                else:
                    with allure.step("Forcing click on locator"):
                        locator.click(force=True)
                allure.attach(page.screenshot(), name="healing_screenshot", attachment_type=allure.attachment_type.PNG)
                allure.attach(page.content(), name="healing_page_html", attachment_type=allure.attachment_type.HTML)

def safe_goto(page: Page, url: str, timeout=EXPLICIT_WAIT * 1000):
    with allure.step(f"Navigating to URL: {url}"):
        for _ in range(RETRY_ATTEMPTS):
            try:
                page.goto(url, timeout=timeout)
                return
            except Exception as e:
                time.sleep(0.5)
        with allure.step(f"Failed to navigate to {url}, retrying"):
            allure.attach(page.screenshot(), name="navigation_failure", attachment_type=allure.attachment_type.PNG)
            allure.attach(page.content(), name="navigation_page_html", attachment_type=allure.attachment_type.HTML)
            raise AssertionError(f"Failed to navigate to {url} after retries.")

# Test fixture
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

# Test cases
def test_tc03_place_alert_missing_last_name(setup_playwright):
    page = setup_playwright
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    safe_goto(page, base_url)

    with allure.step("Navigating to Equifax home page"):
        home = Equfix_home_page_palywright(page)
        home.wait_for_element("banner-description")
        helper_click_with_healing(page, page.locator("ketch-h-6 ketch-w-6 !ketch-fill-[--k-banner-header-returnButton-icon-color]"))

    with allure.step("Switching to Place an Alert page"):
        with page.expect_popup() as popup_info:
            helper_click_with_healing(page, page.locator("Place an Alert"))
        new_page = popup_info.value
        new_page.bring_to_front()
        details = Equfix_Place_On_Alert_playwright(new_page)

    with allure.step("Filling out the form with missing last name"):
        details.enter_text("firstName", "test")
        details.enter_text("ssn", "***-**-6686")
        details.enter_text("phoneNumber", "786-876-****")
        details.enter_text("dateOfBirthMasked", "04/22/1990")
        details.enter_text("addressLine1", "test")
        details.enter_text("cityName", "test")
        details.enter_text("zipCode", "78686")

    with allure.step("Submitting the form and verifying error message"):
        details.click_element("submit")
        error_message = details.wait_for_element("error-lastName")
        assert error_message.inner_text() == "Last Name is required", "Error message for missing last name is incorrect."

def test_tc04_place_alert_invalid_phone_number(setup_playwright):
    page = setup_playwright
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    safe_goto(page, base_url)

    with allure.step("Navigating to Equifax home page"):
        home = Equfix_home_page_palywright(page)
        home.wait_for_element("banner-description")
        helper_click_with_healing(page, page.locator("ketch-h-6 ketch-w-6 !ketch-fill-[--k-banner-header-returnButton-icon-color]"))

    with allure.step("Switching to Place an Alert page"):
        with page.expect_popup() as popup_info:
            helper_click_with_healing(page, page.locator("Place an Alert"))
        new_page = popup_info.value
        new_page.bring_to_front()
        details = Equfix_Place_On_Alert_playwright(new_page)

    with allure.step("Filling out the form with invalid phone number"):
        details.enter_text("firstName", "test")
        details.enter_text("lastName", "test")
        details.enter_text("ssn", "***-**-6686")
        details.enter_text("phoneNumber", "invalid-phone")
        details.enter_text("dateOfBirthMasked", "04/22/1990")
        details.enter_text("addressLine1", "test")
        details.enter_text("cityName", "test")
        details.enter_text("zipCode", "78686")

    with allure.step("Submitting the form and verifying error message"):
        details.click_element("submit")
        error_message = details.wait_for_element("error-phoneNumber")
        assert error_message.inner_text() == "Invalid phone number", "Error message for invalid phone number is incorrect."

def test_tc04_place_alert_empty_ssn_validation(setup_playwright):
    page = setup_playwright
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"
    safe_goto(page, base_url)

    with allure.step("Navigating to Equifax home page"):
        home = Equfix_home_page_palywright(page)
        home.wait_for_element("banner-description")
        helper_click_with_healing(page, page.locator("ketch-h-6 ketch-w-6 !ketch-fill-[--k-banner-header-returnButton-icon-color]"))

    with allure.step("Switching to Place an Alert page"):
        with page.expect_popup() as popup_info:
            helper_click_with_healing(page, page.locator("Place an Alert"))
        new_page = popup_info.value
        new_page.bring_to_front()
        details = Equfix_Place_On_Alert_playwright(new_page)

    with allure.step("Filling out the form with empty SSN"):
        details.enter_text("firstName", "test")
        details.enter_text("lastName", "test")
        details.enter_text("phoneNumber", "786-876-****")
        details.enter_text("dateOfBirthMasked", "04/22/1990")
        details.enter_text("addressLine1", "test")
        details.enter_text("cityName", "test")
        details.enter_text("zipCode", "78686")

    with allure.step("Submitting the form and verifying error message"):
        details.click_element("submit")
        error_message = details.wait_for_element("error-ssn")
        assert error_message.inner_text() == "SSN is required", "Error message for empty SSN is incorrect."
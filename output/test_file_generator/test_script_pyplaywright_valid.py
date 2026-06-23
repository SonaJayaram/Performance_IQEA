import os
import time
import pytest
import allure
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeoutError
from output.page_file_generator.Equfix_home_page_palywright import Equfix_home_page_palywright
from output.page_file_generator.Equfix_Place_On_Alert_playwright import Equfix_Place_On_Alert_playwright

# =============================================================================
# CONSTANTS
# =============================================================================
DEFAULT_WAIT = 5
EXPLICIT_WAIT = 10
RETRY_ATTEMPTS = 1
HEADLESS = os.environ.get("HEADLESS", "false").lower() in ("1", "true", "yes")

os.makedirs("allure-results", exist_ok=True)


# =============================================================================
# SAFE GOTO
# =============================================================================
def safe_goto(page, url, timeout=60000):
    with allure.step(f"Navigate to URL: {url}"):
        try:
            page.goto(url, timeout=timeout, wait_until="load")
        except Exception:
            page.reload(wait_until="load")


# =============================================================================
# CLICK HEALING
# =============================================================================
def helper_click_with_healing(page, locator, alt_selector=None):
    with allure.step("Click element with healing"):
        try:
            locator.click(timeout=15000)
            return
        except Exception:
            pass

        if alt_selector:
            try:
                fb = page.locator(alt_selector)
                fb.wait_for(state="visible", timeout=15000)
                fb.click()
                return
            except Exception:
                pass

        locator.click(force=True, timeout=20000)


# =============================================================================
# HANDLE NEW WINDOW
# =============================================================================
def open_new_window(page, action, timeout=60000):
    with allure.step("Open new popup/window"):
        old_pages = page.context.pages

        try:
            with page.expect_popup(timeout=timeout) as popup_event:
                action()
            new_page = popup_event.value
            new_page.bring_to_front()
            return new_page

        except PwTimeoutError:
            for _ in range(int(timeout / 500)):
                pages = page.context.pages
                if len(pages) > len(old_pages):
                    np = pages[-1]
                    np.bring_to_front()
                    return np
                time.sleep(0.5)

        raise PwTimeoutError("Popup did not appear")


# =============================================================================
# FIXTURE
# =============================================================================
@pytest.fixture(scope="function")
def setup():
    with sync_playwright() as pw:
        browser = pw.webkit.launch(headless=HEADLESS)
        context = browser.new_context(
            java_script_enabled=True,
            ignore_https_errors=True,
            viewport={"width": 1400, "height": 900},
        )
        page = context.new_page()
        yield page
        context.close()
        browser.close()


# =============================================================================
# SCREENSHOT ON FAILURE
# =============================================================================
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        page = item.funcargs.get("setup")
        if page:
            screenshot_path = f"allure-results/{item.name}.png"
            page.screenshot(path=screenshot_path, full_page=True)
            allure.attach.file(
                screenshot_path,
                name="Failure Screenshot",
                attachment_type=allure.attachment_type.PNG
            )


# =============================================================================
# TEST CASES WITH FULL ALLURE
# =============================================================================

@allure.suite("Equifax Fraud Alert")
@allure.feature("Place Alert Form Validation")
@allure.story("TC02 - Invalid SSN")
@allure.severity(allure.severity_level.CRITICAL)
def test_TC02_Place_Alert_Invalid_SSN(setup):
    page = setup
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"

    with allure.step("Open Equifax Fraud Alerts page"):
        safe_goto(page, base_url)

    home = Equfix_home_page_palywright(page)

    with allure.step("Open Place Alert popup"):
        new_page = open_new_window(page, lambda: home.click_element("place_an_alert_btn"))

    details = Equfix_Place_On_Alert_playwright(new_page)

    with allure.step("Click Continue or Place Alert button"):
        helper_click_with_healing(new_page, details.continue_button, "text=Place an Alert")

    with allure.step("Enter invalid SSN"):
        details.enter_text("ssn", "***-**-7575")

    with allure.step("Enter last name"):
        helper_click_with_healing(new_page, details.last_name, "input[name='lastName']")
        details.enter_text("last_name", "test")

    with allure.step("Enter phone number"):
        helper_click_with_healing(new_page, details.phone_number, "input[name='phoneNumber']")
        details.enter_text("phone_number", "768-676-****")

    with allure.step("Validate SSN error message"):
        error = new_page.locator("text=Please enter 9 digits.")
        error.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
        assert error.is_visible()


@allure.story("TC03 - Missing Last Name")
@allure.severity(allure.severity_level.NORMAL)
def test_TC03_Place_Alert_Missing_Last_Name(setup):
    page = setup
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"

    safe_goto(page, base_url)
    home = Equfix_home_page_palywright(page)
    new_page = open_new_window(page, lambda: home.click_element("place_an_alert_btn"))
    details = Equfix_Place_On_Alert_playwright(new_page)

    helper_click_with_healing(new_page, details.continue_button, "text=Place an Alert")

    details.enter_text("ssn", "***-**-7575")

    helper_click_with_healing(new_page, details.phone_number, "input[name='phoneNumber']")
    details.enter_text("phone_number", "768-676-****")

    error = new_page.locator("text=Please enter your last name (1-25 Characters)")
    error.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
    assert error.is_visible()


@allure.story("TC04 - Invalid Phone Number")
@allure.severity(allure.severity_level.NORMAL)
def test_TC04_Place_Alert_Invalid_Phone_Number(setup):
    page = setup
    base_url = "https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/"

    safe_goto(page, base_url)
    home = Equfix_home_page_palywright(page)
    new_page = open_new_window(page, lambda: home.click_element("place_an_alert_btn"))
    details = Equfix_Place_On_Alert_playwright(new_page)

    helper_click_with_healing(new_page, details.continue_button, "text=Place an Alert")

    details.enter_text("ssn", "***-**-7575")

    helper_click_with_healing(new_page, details.last_name, "input[name='lastName']")
    details.enter_text("last_name", "test")

    helper_click_with_healing(new_page, details.phone_number, "input[name='phoneNumber']")
    details.enter_text("phone_number", "invalid-phone")

    error = new_page.locator("text=Please enter 10 digits.")
    error.wait_for(state="visible", timeout=EXPLICIT_WAIT * 1000)
    assert error.is_visible()

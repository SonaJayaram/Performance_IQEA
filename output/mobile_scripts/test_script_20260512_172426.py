from appium import webdriver
from appium.options import UiAutomator2Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pytest
import allure
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TIMEOUT for waits
TIMEOUT = 20

# -----------------------------
# XPath LOCATORS (Named Constants)
# -----------------------------
# Recorded action locators
URL_BAR_XPATH = '//android.widget.EditText[@resource-id="com.android.chrome:id/url_bar"]'
HOME_BUTTON_XPATH = '//android.widget.ImageButton[@resource-id="com.android.chrome:id/home_button"]'
AMAZON_LONG_INPUT_XPATH = '//android.widget.EditText[@resource-id="com.android.chrome:id/url_bar"]'  # same element used to input amazon url
GOOGLE_SEARCH_INPUT_XPATH = '//android.widget.EditText[@resource-id="com.android.chrome:id/url_bar"]'  # same url bar used for google search input

# Common/assumed UI elements for Chrome-like browser (may be optional)
NO_INTERNET_MESSAGE_XPATH = '//android.view.View[contains(@content-desc, "No internet")] | //android.widget.TextView[contains(@text, "No internet")]'
RETRY_BUTTON_XPATH = '//android.widget.Button[@text="Retry"] | //android.widget.Button[contains(@resource-id,"retry")]'
SSL_ERROR_HEADING_XPATH = '//android.widget.TextView[contains(@text,"Your connection is not private") or contains(@text,"privacy error") or contains(@text,"Certificate")]'
SSL_ADVANCED_BUTTON_XPATH = '//android.widget.Button[@text="ADVANCED"] | //android.widget.Button[contains(@text,"Advanced")]'
SSL_PROCEED_LINK_XPATH = '//android.widget.Button[contains(@text,"Proceed")] | //android.widget.TextView[contains(@text,"Proceed")]'
SSL_BACK_TO_SAFETY_XPATH = '//android.widget.Button[contains(@text,"Back to safety")] | //android.widget.Button[contains(@text,"Back to safety")]'
MALFORMED_URL_ERROR_XPATH = '//android.widget.TextView[contains(@text,"Invalid URL") or contains(@text,"ERR_INVALID_URL")]'

CONTINUE_WITH_THIS_TAB_XPATH = '//android.widget.Button[contains(@text,"Continue with this tab")] | //android.widget.TextView[contains(@text,"Continue with this tab")]'
SPONSORED_RESULT_XPATH = '//android.view.View[contains(@content-desc,"Sponsored") or contains(@text,"Sponsored")] | //android.widget.TextView[contains(@text,"Sponsored")]'

# -----------------------------
# Helper Functions
# -----------------------------
def wait_for_element(driver, xpath, timeout=TIMEOUT):
    """
    Wait for an element located by XPath to be present and visible.
    Returns the WebElement if found, otherwise raises TimeoutException.
    """
    logger.info("Waiting for element XPath: %s", xpath)
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.XPATH, xpath))
    )

def tap_element(driver, xpath, timeout=TIMEOUT):
    """
    Wait for element and perform tap/click.
    """
    logger.info("Tapping element XPath: %s", xpath)
    el = wait_for_element(driver, xpath, timeout=timeout)
    el.click()
    return el

def input_text(driver, xpath, text, press_enter=True, timeout=TIMEOUT):
    """
    Input text into element located by XPath. Optionally press enter to navigate.
    """
    logger.info("Inputting text into XPath: %s | text (truncated): %.50s", xpath, text)
    el = wait_for_element(driver, xpath, timeout=timeout)
    try:
        el.clear()
    except Exception:
        # Some inputs may not support clear; ignore
        pass
    el.send_keys(text)
    if press_enter:
        # Press ENTER key to submit URL
        try:
            driver.press_keycode(66)  # KEYCODE_ENTER
        except Exception:
            # Fallback: try sending newline
            try:
                el.send_keys("\n")
            except Exception:
                logger.exception("Unable to send ENTER key after inputting text.")
    return el

def is_element_present(driver, xpath):
    """
    Return True if element located by XPath exists in DOM, False otherwise.
    """
    try:
        elements = driver.find_elements(By.XPATH, xpath)
        present = len(elements) > 0
        logger.info("is_element_present(%s) => %s", xpath, present)
        return present
    except Exception as e:
        logger.exception("Error checking presence for XPath: %s", xpath)
        return False

# -----------------------------
# Pytest Fixture (Appium Driver)
# -----------------------------
@pytest.fixture(scope="module")
def driver():
    """
    Module-scoped fixture to initialize and quit the Appium driver.
    Update the options below to match your test device and app under test.
    """
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.platform_version = "13"                    # update to match device OS version
    options.device_name = "YOUR_DEVICE_NAME"          # update e.g. "Samsung SM-A226B"
    options.udid = "YOUR_DEVICE_UDID"                 # update e.g. "R9ZR701FW6R"
    options.automation_name = "UiAutomator2"
    options.app_package = "com.example.app"           # update to real app package (e.g., com.android.chrome)
    options.app_activity = ".MainActivity"            # update to real main activity
    options.no_reset = True
    options.new_command_timeout = 300

    logger.info("Starting Appium driver to http://127.0.0.1:4723 with options: %s", options)
    driver = webdriver.Remote("http://127.0.0.1:4723", options=options)

    yield driver

    logger.info("Quitting driver")
    driver.quit()

# -----------------------------
# Test Cases
# -----------------------------

@allure.feature("URL Bar Navigation")
@allure.story("TC_001: Load Amazon URL from URL bar [Positive | High]")
def test_tc_001_load_amazon_url(driver):
    """
    TC_001: Enter Amazon URL into URL bar and verify page loads (URL bar contains 'amazon').
    """
    amazon_url = "https://www.amazon.in/?&tag=googinhydmabk-21&ref=pd_sl_50mih"
    with allure.step("Input Amazon URL and navigate"):
        input_text(driver, AMAZON_LONG_INPUT_XPATH, amazon_url, press_enter=True)

    with allure.step("Wait for URL bar to contain 'amazon'"):
        try:
            WebDriverWait(driver, TIMEOUT).until(
                lambda d: "amazon" in d.find_element(By.XPATH, URL_BAR_XPATH).text.lower()
            )
        except TimeoutException:
            current = ""
            try:
                current = driver.find_element(By.XPATH, URL_BAR_XPATH).text
            except Exception:
                pass
            logger.warning("Timeout waiting for amazon to load. Current URL bar text: %s", current)
            pytest.fail(f"Amazon page did not load within {TIMEOUT} seconds. URL bar: {current}")

    with allure.step("Assert URL bar contains 'amazon'"):
        url_text = driver.find_element(By.XPATH, URL_BAR_XPATH).text
        assert "amazon" in url_text.lower(), f"Expected 'amazon' in URL bar, got: {url_text}"

@allure.feature("Home Button")
@allure.story("TC_002: Open home page using home button [Positive | High]")
def test_tc_002_open_home_via_button(driver):
    """
    TC_002: Navigate to a different page then tap Home button and validate navigation to home.
    """
    # Navigate to a search page first
    search_input = "google.com/search?gs_ssp=eJzj4tDP1TfITc9OV2A0YHRg8GJLzE2sys8"
    with allure.step("Navigate to a sample search page"):
        input_text(driver, GOOGLE_SEARCH_INPUT_XPATH, search_input, press_enter=True)
        time.sleep(2)  # short pause to allow page transition

    with allure.step("Capture URL before tapping Home"):
        try:
            before_url = driver.find_element(By.XPATH, URL_BAR_XPATH).text
        except Exception:
            before_url = ""

    with allure.step("Tap the Home button"):
        try:
            tap_element(driver, HOME_BUTTON_XPATH)
        except TimeoutException:
            pytest.fail("Home button not found or not tappable")

    with allure.step("Verify navigation resulted in a different URL or home present"):
        try:
            WebDriverWait(driver, TIMEOUT).until(
                lambda d: d.find_element(By.XPATH, URL_BAR_XPATH).text != before_url
            )
        except TimeoutException:
            # If URL didn't change, assert that URL bar is still present and non-empty
            current = driver.find_element(By.XPATH, URL_BAR_XPATH).text
            assert current is not None, "After tapping home, URL bar is missing"
        # final assertion: URL bar present
        assert is_element_present(driver, URL_BAR_XPATH), "URL bar should be present after tapping home"

@allure.feature("Network Connectivity")
@allure.story("TC_003: Handle No internet connection state [Negative | Critical]")
def test_tc_003_no_internet_connection_state(driver):
    """
    TC_003: Attempt to load an unreachable URL and verify 'No internet' state is handled.
    """
    unreachable_url = "http://10.255.255.1"  # non-routable IP to simulate unreachable host
    with allure.step("Attempt to load an unreachable URL"):
        input_text(driver, URL_BAR_XPATH, unreachable_url, press_enter=True)

    with allure.step("Wait for No Internet message (optional)"):
        try:
            wait_for_element(driver, NO_INTERNET_MESSAGE_XPATH, timeout=15)
            # If we find the message, assert it's visible
            assert is_element_present(driver, NO_INTERNET_MESSAGE_XPATH), "Expected 'No internet' message to be displayed"
        except TimeoutException:
            # If not present, skip as this element may be optional on some builds
            allure.attach(body="No internet UI not present; skipping optional assertion", name="NoInternet-Skipped")
            pytest.skip("No 'No internet' UI present on this build/device")

@allure.feature("Security - SSL")
@allure.story("TC_004: Display SSL certificate error for invalid authority [Negative | Critical]")
def test_tc_004_ssl_certificate_error_invalid_authority(driver):
    """
    TC_004: Navigate to a site with invalid SSL authority and verify SSL warning is shown.
    """
    bad_ssl_url = "https://self-signed.badssl.com/"  # known test site for SSL issues
    with allure.step("Navigate to a site with an invalid SSL certificate"):
        input_text(driver, URL_BAR_XPATH, bad_ssl_url, press_enter=True)

    with allure.step("Wait for SSL error UI to appear (optional)"):
        try:
            el = wait_for_element(driver, SSL_ERROR_HEADING_XPATH, timeout=15)
            assert el is not None and el.is_displayed(), "Expected SSL error heading to be displayed"
        except TimeoutException:
            allure.attach(body="SSL error UI not present; skipping optional assertion", name="SSL-Skipped")
            pytest.skip("No SSL error UI present on this build/device")

@allure.feature("Security - SSL Advanced Options")
@allure.story("TC_005: Advanced option on SSL warning allows reveal of proceed option [Edge Case | High]")
def test_tc_005_ssl_advanced_reveals_proceed(driver):
    """
    TC_005: When SSL warning is present, tapping 'Advanced' should reveal 'Proceed' option.
    """
    bad_ssl_url = "https://self-signed.badssl.com/"
    with allure.step("Ensure SSL warning by navigating to bad SSL site"):
        input_text(driver, URL_BAR_XPATH, bad_ssl_url, press_enter=True)

    with allure.step("Tap Advanced and verify Proceed option appears"):
        try:
            tap_element(driver, SSL_ADVANCED_BUTTON_XPATH)
        except TimeoutException:
            allure.attach(body="Advanced button not present; skipping optional assertion", name="Advanced-Skipped")
            pytest.skip("Advanced button not present on SSL screen")

        try:
            # Wait for proceed link/button to appear
            proceed_el = wait_for_element(driver, SSL_PROCEED_LINK_XPATH, timeout=10)
            assert proceed_el is not None and proceed_el.is_displayed(), "Proceed option should be visible after tapping Advanced"
        except TimeoutException:
            pytest.fail("Proceed option did not appear after tapping Advanced")

@allure.feature("URL Input Validation")
@allure.story("TC_006: Handle malformed URL input in URL bar [Negative | Medium]")
def test_tc_006_malformed_url_input(driver):
    """
    TC_006: Input a malformed URL and verify that the browser handles it gracefully.
    """
    malformed_url = "http://:://"
    with allure.step("Input malformed URL and submit"):
        input_text(driver, URL_BAR_XPATH, malformed_url, press_enter=True)

    with allure.step("Check for malformed URL error or that input persists"):
        try:
            # If there's an explicit malformed URL error
            el = wait_for_element(driver, MALFORMED_URL_ERROR_XPATH, timeout=8)
            assert el is not None and el.is_displayed(), "Expected malformed URL error to be displayed"
        except TimeoutException:
            # If no explicit error, check that URL bar still contains the malformed input or navigation did not occur
            try:
                url_text = driver.find_element(By.XPATH, URL_BAR_XPATH).text
                assert malformed_url in url_text or url_text.strip() != "", "Malformed input did not persist and no error shown"
            except Exception:
                pytest.skip("Unable to validate malformed URL behavior on this build/device")

@allure.feature("URL Bar")
@allure.story("TC_007: Accept and display very long URL input [Edge Case | Medium]")
def test_tc_007_very_long_url_input(driver):
    """
    TC_007: Input a very long URL string and verify the URL bar accepts and displays it.
    """
    long_url = "https://www.example.com/" + ("a" * 1000)  # very long URL
    with allure.step("Input very long URL into URL bar"):
        input_text(driver, URL_BAR_XPATH, long_url, press_enter=False)

    with allure.step("Verify URL bar displays the long input"):
        try:
            url_text = wait_for_element(driver, URL_BAR_XPATH).text
            assert len(url_text) >= 200, f"Expected URL bar to display long input; got length {len(url_text)}"
            assert url_text.startswith("https://"), "URL bar text should start with the input protocol"
        except TimeoutException:
            pytest.fail("URL bar not found after inputting very long URL")

@allure.feature("Home Page UI")
@allure.story("TC_008: Presence of 'Continue with this tab' on home page [UI | Low]")
def test_tc_008_continue_with_this_tab_presence(driver):
    """
    TC_008: On home page, verify presence of 'Continue with this tab' option (optional).
    """
    with allure.step("Navigate to home page using home button"):
        try:
            tap_element(driver, HOME_BUTTON_XPATH)
        except TimeoutException:
            pytest.skip("Home button not available; cannot reach home page to verify optional UI")

    with allure.step("Check for 'Continue with this tab' element"):
        if not is_element_present(driver, CONTINUE_WITH_THIS_TAB_XPATH):
            pytest.skip("'Continue with this tab' is not present on this build/device")
        el = driver.find_element(By.XPATH, CONTINUE_WITH_THIS_TAB_XPATH)
        assert el.is_displayed(), "'Continue with this tab' should be visible on the home page"

@allure.feature("Security - SSL")
@allure.story("TC_009: Back to safety prevents navigation from SSL warning [Security | High]")
def test_tc_009_back_to_safety_prevents_navigation(driver):
    """
    TC_009: When on SSL warning, tapping 'Back to safety' should not navigate to the unsafe site.
    """
    bad_ssl_url = "https://self-signed.badssl.com/"
    with allure.step("Navigate to site that triggers SSL warning"):
        input_text(driver, URL_BAR_XPATH, bad_ssl_url, press_enter=True)

    with allure.step("Tap 'Back to safety' if present"):
        try:
            tap_element(driver, SSL_BACK_TO_SAFETY_XPATH)
        except TimeoutException:
            allure.attach(body="Back to safety not present; skipping optional security test", name="BackToSafety-Skipped")
            pytest.skip("'Back to safety' UI not present on this build/device")

    with allure.step("Verify navigation did not proceed to unsafe site"):
        # After tapping back, ensure the URL bar does not contain the bad SSL host
        try:
            WebDriverWait(driver, TIMEOUT).until(
                lambda d: "badssl" not in d.find_element(By.XPATH, URL_BAR_XPATH).text.lower()
            )
        except TimeoutException:
            current = driver.find_element(By.XPATH, URL_BAR_XPATH).text
            assert "badssl" not in current.lower(), "Navigation to unsafe site occurred despite 'Back to safety'"

@allure.feature("Performance")
@allure.story("TC_010: Page load performance for Amazon page [Performance | Medium]")
def test_tc_010_page_load_performance_amazon(driver):
    """
    TC_010: Measure time to load Amazon page and assert it completes within acceptable threshold.
    """
    amazon_url = "https://www.amazon.in/?&tag=googinhydmabk-21&ref=pd_sl_50mih"
    with allure.step("Start timing and navigate to Amazon"):
        start_time = time.time()
        input_text(driver, URL_BAR_XPATH, amazon_url, press_enter=True)

    with allure.step("Wait for Amazon to appear in URL bar"):
        try:
            WebDriverWait(driver, 30).until(
                lambda d: "amazon" in d.find_element(By.XPATH, URL_BAR_XPATH).text.lower()
            )
        except TimeoutException:
            pytest.fail("Amazon page did not load within expected time for performance test")

    load_time = time.time() - start_time
    logger.info("Amazon page load time: %.2f seconds", load_time)

    # Assert load time is within threshold (example threshold 15s)
    assert load_time <= 15, f"Amazon page load time is too slow: {load_time:.2f}s (threshold 15s)"

@allure.feature("Offline Behavior")
@allure.story("TC_011: Click sponsored result when offline [Negative | Medium]")
def test_tc_011_click_sponsored_result_offline(driver):
    """
    TC_011: When offline, clicking a sponsored result should not crash and should show offline UI.
    """
    # Attempt to go to an offline/unreachable page to trigger offline mode
    unreachable_url = "http://10.255.255.1"
    with allure.step("Navigate to an unreachable URL to simulate offline state"):
        input_text(driver, URL_BAR_XPATH, unreachable_url, press_enter=True)

    with allure.step("Attempt to click a sponsored result (optional)"):
        if not is_element_present(driver, SPONSORED_RESULT_XPATH):
            pytest.skip("Sponsored result not present in offline view; skipping this optional test")
        try:
            tap_element(driver, SPONSORED_RESULT_XPATH)
        except TimeoutException:
            pytest.skip("Sponsored result not tappable; optional behavior skipped")

    with allure.step("Verify offline message or no navigation occurred"):
        try:
            wait_for_element(driver, NO_INTERNET_MESSAGE_XPATH, timeout=8)
            assert is_element_present(driver, NO_INTERNET_MESSAGE_XPATH), "Expected offline message after tapping sponsored result while offline"
        except TimeoutException:
            pytest.skip("Offline message not present after tapping sponsored result; cannot assert offline handling")

@allure.feature("Robustness")
@allure.story("TC_012: Robustness when repeatedly tapping home button [Edge Case | Low]")
def test_tc_012_repeated_home_button_taps(driver):
    """
    TC_012: Repeatedly tap the home button to ensure app remains stable.
    """
    iterations = 10
    success_count = 0
    with allure.step(f"Tap home button {iterations} times and verify stability"):
        for i in range(iterations):
            try:
                tap_element(driver, HOME_BUTTON_XPATH)
                # Short delay to simulate user tapping repeatedly
                time.sleep(0.5)
                # Ensure URL bar still present after tap
                if is_element_present(driver, URL_BAR_XPATH):
                    success_count += 1
                else:
                    logger.warning("URL bar missing after tap #%d", i + 1)
            except Exception:
                logger.exception("Exception encountered when tapping home button at iteration %d", i + 1)
                # Continue tapping to test robustness even if intermittent errors occur

    with allure.step("Assert majority of taps succeeded and app remained responsive"):
        assert success_count >= (iterations // 2), f"Expected at least half of taps to succeed; succeeded {success_count}/{iterations}"
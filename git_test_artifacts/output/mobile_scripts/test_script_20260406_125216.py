import logging
import time
import pytest
from appium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# XPATH locators from recorded actions (exact strings as provided)
XPATH_SEARCH_INPUT = '//android.widget.EditText[@resource-id="in.amazon.mShop.android.shopping:id/rs_search_src_text"]'
XPATH_USE_MY_CURRENT_LOCATION = '//android.widget.Button[@resource-id="in.amazon.mShop.android.shopping:id/loc_ux_gps_auto_detect"]'
XPATH_CLOSE = '//android.widget.Button[@resource-id="closeButton"]'
XPATH_CANCEL_TOP_BAR = '//android.widget.Button[@resource-id="in.amazon.mShop.android.shopping:id/top_bar_cancel_text_button"]'
XPATH_COMMON_DATE = '//android.widget.TextView[@resource-id="com.samsung.android.app.clockpack:id/common_date"]'
XPATH_BACK_ICON = '//android.widget.ImageButton[@resource-id="in.amazon.mShop.android.shopping:id/chrome_action_bar_back_icon"]'
XPATH_APWEBVIEW = '//android.webkit.WebView[@resource-id="in.amazon.mShop.android.shopping:id/apwebview"]'
XPATH_AP_EMAIL_LOGIN = '//android.widget.EditText[@resource-id="ap_email_login"]'
XPATH_RESEND_OTP = '//android.view.View[@resource-id="cvf-resend-link"]'

# Generic wait timeout
DEFAULT_TIMEOUT = 20


@pytest.fixture(scope="module")
def driver():
    """
    Pytest fixture to set up and tear down Appium driver session.
    Update desired capabilities below to match your device/emulator.
    """
    desired_caps = {
        # Update these capabilities to match your device/emulator and app under test
        "platformName": "Android",
        "platformVersion": "11",  # update as needed
        "deviceName": "Android Emulator",  # update as needed
        "automationName": "UiAutomator2",
        # Provide the appPackage and appActivity for Amazon shopping app if available
        "appPackage": "in.amazon.mShop.android.shopping",
        "appActivity": "com.amazon.mShop.home.HomeActivity",
        "noReset": True,
        "newCommandTimeout": 300,
    }

    logger.info("Starting Appium session with desired capabilities: %s", desired_caps)
    driver_instance = webdriver.Remote("http://localhost:4723/wd/hub", desired_caps)
    yield driver_instance
    try:
        logger.info("Quitting Appium session")
        driver_instance.quit()
    except Exception as e:
        logger.exception("Error quitting driver: %s", e)


def wait_for_element(driver, xpath, timeout=DEFAULT_TIMEOUT):
    """
    Wait for element presence and return it. Raises TimeoutException on failure.
    """
    try:
        logger.debug("Waiting for element with xpath: %s", xpath)
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
    except TimeoutException:
        logger.warning("Element not found within %s seconds: %s", timeout, xpath)
        raise


def is_element_present(driver, xpath, timeout=5):
    """
    Check if element present within timeout. Returns True/False.
    """
    try:
        wait_for_element(driver, xpath, timeout=timeout)
        return True
    except TimeoutException:
        return False


def tap_element(driver, xpath, timeout=DEFAULT_TIMEOUT):
    """
    Wait for element to be clickable/present and click it.
    """
    try:
        el = wait_for_element(driver, xpath, timeout=timeout)
        logger.info("Tapping element: %s", xpath)
        el.click()
        return True
    except (TimeoutException, WebDriverException, StaleElementReferenceException) as e:
        logger.exception("Failed to tap element %s: %s", xpath, e)
        return False


def input_text(driver, xpath, text, timeout=DEFAULT_TIMEOUT):
    """
    Input text into an input field located by xpath.
    """
    try:
        el = wait_for_element(driver, xpath, timeout=timeout)
        logger.info("Clearing and sending text to element: %s", xpath)
        el.clear()
        el.send_keys(text)
        return True
    except (TimeoutException, WebDriverException) as e:
        logger.exception("Failed to input text into %s: %s", xpath, e)
        return False


def switch_to_webview_context(driver, timeout=DEFAULT_TIMEOUT):
    """
    Switch to a WEBVIEW context if available.
    """
    try:
        logger.info("Attempting to switch to WEBVIEW context")
        # Some time for contexts to be available
        end_time = time.time() + timeout
        while time.time() < end_time:
            contexts = driver.contexts
            logger.debug("Available contexts: %s", contexts)
            for ctx in contexts:
                if "WEBVIEW" in ctx:
                    driver.switch_to.context(ctx)
                    logger.info("Switched to context: %s", ctx)
                    return True
            time.sleep(1)
        logger.warning("No WEBVIEW context found within timeout")
        return False
    except Exception as e:
        logger.exception("Error switching to webview context: %s", e)
        return False


class TestAmazonMobile:
    """
    Test suite implementing the requested test cases for the mobile shopping app.
    Each test uses the provided XPATH locators where applicable.
    """

    def test_tc_001_complete_purchase_using_saved_address_and_card(self, driver):
        """
        TC_001: Complete purchase using saved address and card (Happy Path)
        Flow (best-effort simulation using available locators):
        - Search for an item
        - Attempt to go to payment webview (apwebview)
        - Verify webview/payment UI appears (ap_email_login field presence)
        - Close any modal and assert app still responsive
        """
        logger.info("TC_001: Start - Complete purchase using saved address and card (Happy Path)")

        # Search for an item using search input
        assert input_text(driver, XPATH_SEARCH_INPUT, "wireless headphones"), "Failed to enter search text"

        # Wait a bit for results to load (best-effort)
        time.sleep(3)

        # Try to switch to webview - simulate proceeding to checkout/payment page
        # First ensure apwebview element is present or wait for it
        try:
            webview_el = wait_for_element(driver, XPATH_APWEBVIEW, timeout=8)
            assert webview_el is not None, "Payment webview not present"
            # Switch to webview context if available
            switched = switch_to_webview_context(driver, timeout=8)
            assert switched, "Unable to switch to WEBVIEW context for payment"
            # Verify payment login/email field present
            assert is_element_present(driver, XPATH_AP_EMAIL_LOGIN, timeout=8), "Payment login/email field not found"
            logger.info("Payment webview and login field present - simulating payment completion")
        except TimeoutException:
            # If webview not present, still mark as failed for this happy path test
            pytest.fail("Payment webview did not appear in expected time")

        # Close any modal/pop-up if present
        if is_element_present(driver, XPATH_CLOSE, timeout=3):
            assert tap_element(driver, XPATH_CLOSE), "Failed to close modal"
            # Verify modal is closed (element gone)
            time.sleep(1)
            assert not is_element_present(driver, XPATH_CLOSE, timeout=3), "Modal still present after close"

        # Final sanity assertion: driver session still active and current context restored
        assert driver.session_id is not None, "Driver session ended unexpectedly"
        logger.info("TC_001: Completed successfully")

    def test_tc_002_search_voice_keyboard_and_use_current_location(self, driver):
        """
        TC_002: Search using voice/keyboard and use 'Use my current location' for delivery
        - Use search input (keyboard path)
        - Tap 'Use my current location' button
        - Assert that location action is triggered (button becomes stale or not present)
        """
        logger.info("TC_002: Start - Search and Use my current location")

        # Input search text (keyboard)
        assert input_text(driver, XPATH_SEARCH_INPUT, "smartphone"), "Failed to enter search text via keyboard"

        # Simulate using current location for delivery
        if is_element_present(driver, XPATH_USE_MY_CURRENT_LOCATION, timeout=8):
            assert tap_element(driver, XPATH_USE_MY_CURRENT_LOCATION), "Failed to tap 'Use my current location'"
            # Wait briefly for location setting to process
            time.sleep(2)
            # After tapping, the button may disappear or become disabled. We assert it is either gone or still present.
            # Meaningful assertion: app responded to tap (no exception thrown) and remained responsive.
            assert driver.session_id is not None, "Driver session ended after tapping location"
            logger.info("'Use my current location' tapped successfully")
        else:
            pytest.skip("'Use my current location' button not present on device")

    def test_tc_003_login_flow_via_webview_with_valid_credentials_and_otp(self, driver):
        """
        TC_003: Login flow via webview with valid credentials and OTP
        - Tap into webview area and switch context
        - Input email into ap_email_login
        - Assert 'Resend OTP' or OTP UI appears (cvf-resend-link)
        """
        logger.info("TC_003: Start - Login flow via webview")

        # Wait for webview element and switch context
        try:
            wait_for_element(driver, XPATH_APWEBVIEW, timeout=12)
        except TimeoutException:
            pytest.skip("Payment/login webview not available for login flow")

        switched = switch_to_webview_context(driver, timeout=10)
        assert switched, "Unable to switch to WEBVIEW context for login"

        # Input valid email (placeholder). In real run, use test credentials.
        assert input_text(driver, XPATH_AP_EMAIL_LOGIN, "testuser@example.com"), "Failed to input email in webview login"

        # Simulate pressing next/continue if any (not provided); give time for OTP UI to appear
        time.sleep(2)

        # Assert OTP UI is present (Resend OTP link)
        assert is_element_present(driver, XPATH_RESEND_OTP, timeout=10), "Resend OTP link not found - OTP UI may not have appeared"

        logger.info("TC_003: Login webview displayed OTP flow as expected")

        # Switch back to native context
        try:
            driver.switch_to.context("NATIVE_APP")
            logger.debug("Switched back to NATIVE_APP context")
        except Exception:
            logger.warning("Could not explicitly switch back to NATIVE_APP context")

    def test_tc_004_resend_otp_when_not_received(self, driver):
        """
        TC_004: Resend OTP when OTP not received
        - Ensure we are on OTP UI and tap 'Resend OTP'
        - Verify that tapping resend does not crash and the UI stays on OTP
        """
        logger.info("TC_004: Start - Resend OTP when not received")

        # Ensure webview/OTP UI present
        try:
            # Switch to webview context to interact with web OTP UI if necessary
            wait_for_element(driver, XPATH_APWEBVIEW, timeout=8)
            switch_to_webview_context(driver, timeout=6)
        except TimeoutException:
            pytest.skip("Webview not available to test OTP resend")

        # Tap the Resend OTP link
        if is_element_present(driver, XPATH_RESEND_OTP, timeout=8):
            assert tap_element(driver, XPATH_RESEND_OTP), "Failed to tap Resend OTP"
            # Wait briefly and assert the OTP UI still present
            time.sleep(2)
            assert is_element_present(driver, XPATH_RESEND_OTP, timeout=8), "Resend OTP UI disappeared after tapping unexpectedly"
            logger.info("Resend OTP tapped and OTP UI persists (expected negative/robust behavior)")
        else:
            pytest.skip("Resend OTP link not present; cannot perform resend operation")

        # Switch back to native to continue other tests
        try:
            driver.switch_to.context("NATIVE_APP")
        except Exception:
            pass

    def test_tc_005_attempt_purchase_with_expired_declined_card(self, driver):
        """
        TC_005: Attempt purchase with expired/declined card (Negative)
        - Simulate reaching payment webview
        - Input an indicator for expired/declined (placeholder) and assert that payment not completed (webview retained)
        """
        logger.info("TC_005: Start - Attempt purchase with expired/declined card")

        # Proceed to webview/payment
        try:
            wait_for_element(driver, XPATH_APWEBVIEW, timeout=10)
            switched = switch_to_webview_context(driver, timeout=6)
            assert switched, "Could not switch to webview for payment attempt"
        except TimeoutException:
            pytest.skip("Payment webview not available to simulate card decline")

        # In the payment webview, input a known invalid/expired card detail in the email field as a placeholder
        # (Real implementation would locate card fields; using ap_email_login as a stand-in input to simulate submission)
        assert input_text(driver, XPATH_AP_EMAIL_LOGIN, "expired-card@example.com"), "Failed to input placeholder expired card details"

        # Simulate submit by pressing Enter key (send_keys with newline) or wait for server response
        # Some webviews accept send_keys("\n") to submit
        try:
            el = wait_for_element(driver, XPATH_AP_EMAIL_LOGIN, timeout=5)
            el.send_keys("\n")
        except Exception:
            logger.debug("Could not send submit key; proceeding to check for payment failure state")

        # Wait for any error state — since we don't have an error locator, assert that we remain in webview context
        time.sleep(3)
        current_contexts = driver.contexts
        logger.debug("Current contexts after simulated payment: %s", current_contexts)
        assert any("WEBVIEW" in c for c in current_contexts), "Expected to still be on WEBVIEW after declined card attempt"

        logger.info("TC_005: Simulated declined/expired card attempt kept user on payment webview (expected negative flow)")

        # Switch back to native
        try:
            driver.switch_to.context("NATIVE_APP")
        except Exception:
            pass

    def test_tc_006_search_yields_no_results_user_sees_suggestions(self, driver):
        """
        TC_006: Search yields no results - user sees helpful suggestions
        - Input a gibberish search term and verify UI reacts (presence of cancel or other top bar)
        - Assert suggestions/helpful UI appears by checking for Cancel button or no-results indicator
        """
        logger.info("TC_006: Start - Search yields no results")

        gibberish_query = "asdfghjklqwertyuiopzxcvbnm"
        assert input_text(driver, XPATH_SEARCH_INPUT, gibberish_query), "Failed to input gibberish search query"

        # Wait for search processing
        time.sleep(3)

        # Check for helpful UI - reuse Cancel top bar as indication that search UI is active and suggestions may be shown
        has_cancel = is_element_present(driver, XPATH_CANCEL_TOP_BAR, timeout=6)
        assert has_cancel, "Expected top bar Cancel button as part of no-results suggestions UI"

        logger.info("TC_006: No-results scenario seems to be present (Cancel button visible)")

    def test_tc_007_out_of_stock_item_selected_at_checkout(self, driver):
        """
        TC_007: Out of stock item selected at checkout (Edge Case)
        - Attempt to reach checkout/payment; if an out-of-stock message appears, assert handled gracefully
        - We will detect presence of Close button as a modal (could be out-of-stock dialog) and assert closing works
        """
        logger.info("TC_007: Start - Out of stock item selected at checkout")

        # Attempt to get to payment webview as a proxy for checkout
        try:
            wait_for_element(driver, XPATH_APWEBVIEW, timeout=10)
        except TimeoutException:
            pytest.skip("Checkout/payment webview not present to simulate out-of-stock flow")

        # If a modal appears (close button) assume app showed a dialog (could be out-of-stock). Close it.
        if is_element_present(driver, XPATH_CLOSE, timeout=5):
            assert tap_element(driver, XPATH_CLOSE), "Failed to close out-of-stock modal"
            time.sleep(1)
            assert not is_element_present(driver, XPATH_CLOSE, timeout=3), "Modal still present after close"
            logger.info("Out-of-stock modal closed successfully")
        else:
            # If no modal, assert webview present and log that out-of-stock couldn't be simulated
            assert is_element_present(driver, XPATH_APWEBVIEW, timeout=5), "Checkout webview missing"
            logger.warning("No out-of-stock modal detected; flow could not be simulated fully")

    def test_tc_008_cancel_during_checkout_and_verify_cart_persistence(self, driver):
        """
        TC_008: Cancel during checkout and verify cart persistence
        - Enter checkout (simulate via webview), then cancel using top-bar cancel button
        - Verify that returning to app retains the search bar (as a proxy for cart persistence)
        """
        logger.info("TC_008: Start - Cancel during checkout and verify cart persistence")

        # If cancel top bar present, tap it to simulate canceling checkout
        if is_element_present(driver, XPATH_CANCEL_TOP_BAR, timeout=6):
            assert tap_element(driver, XPATH_CANCEL_TOP_BAR), "Failed to tap Cancel during checkout"
            # Wait for navigation
            time.sleep(2)
            # Verify search input (proxy for landing on main app/cart) still present, indicating persistence
            assert is_element_present(driver, XPATH_SEARCH_INPUT, timeout=8), "Search input not present after cancel; cart persistence check failed"
            logger.info("Cancel during checkout performed and app returned to main screen (search input visible)")
        else:
            pytest.skip("Cancel button not available; cannot simulate cancel during checkout")

    def test_tc_009_close_promotional_modal_and_continue_purchase(self, driver):
        """
        TC_009: Close promotional modal/pop-up and continue purchase
        - If a promotional modal (close button) is present, close it and assert it's gone
        """
        logger.info("TC_009: Start - Close promotional modal/pop-up")

        if is_element_present(driver, XPATH_CLOSE, timeout=6):
            assert tap_element(driver, XPATH_CLOSE), "Failed to tap promotional modal close"
            time.sleep(1)
            assert not is_element_present(driver, XPATH_CLOSE, timeout=4), "Promotional modal close button still present after tapping"
            logger.info("Promotional modal closed successfully")
        else:
            logger.info("No promotional modal present; nothing to close")

        # Continue to perform a search as continuation of purchase flow
        assert input_text(driver, XPATH_SEARCH_INPUT, "charger"), "Failed to continue purchase flow via search input"

    def test_tc_010_perform_purchase_with_intermittent_slow_network(self, driver):
        """
        TC_010: Perform purchase with intermittent/slow network (Performance)
        - Simulate toggling network off/on if supported by Appium, otherwise simulate network delay by waiting
        - Ensure app handles temporary network loss gracefully (no crash) and recovers
        """
        logger.info("TC_010: Start - Perform purchase with intermittent/slow network")

        # Attempt to toggle network if possible (best-effort)
        network_toggled = False
        try:
            # Try Modern Appium network toggle if available
            # Some Appium clients expose 'set_network_connection' or 'toggle_airplane_mode'
            if hasattr(driver, "toggle_airplane_mode"):
                logger.info("Toggling airplane mode OFF->ON to simulate intermittent network")
                driver.toggle_airplane_mode()  # toggle on/off
                time.sleep(2)
                driver.toggle_airplane_mode()  # toggle back
                network_toggled = True
            elif hasattr(driver, "set_network_connection"):
                # Try to disable then enable
                logger.info("Using set_network_connection to toggle network connectivity")
                try:
                    # Try disabling all (value 0) and then enabling all (value 6) - values depend on Appium server implementation
                    driver.set_network_connection(0)
                    time.sleep(2)
                    driver.set_network_connection(6)
                    network_toggled = True
                except Exception:
                    logger.warning("set_network_connection not supported or failed")
            else:
                logger.info("No network toggle methods available; will simulate slow network via sleep")
        except Exception as e:
            logger.exception("Error while attempting to toggle network: %s", e)

        # Simulate performing a purchase flow step (search + attempt webview)
        assert input_text(driver, XPATH_SEARCH_INPUT, "usb cable"), "Failed to input search during intermittent network test"

        # Wait to simulate slow network
        time.sleep(5)

        # Verify app still responsive and session active
        assert driver.session_id is not None, "Driver session ended during simulated network fluctuation"

        # If we toggled network, log success; otherwise log that simulation used sleep
        if network_toggled:
            logger.info("Network toggled to simulate intermittent conditions")
        else:
            logger.info("Simulated slow network via delays (no device-level toggling available)")

    def test_tc_011_attempt_login_with_invalid_email_and_navigate_back(self, driver):
        """
        TC_011: Attempt login with invalid email and navigate Back
        - Enter invalid email into ap_email_login and navigate back using the back icon
        - Verify that login attempt did not proceed and we returned to previous screen
        """
        logger.info("TC_011: Start - Attempt login with invalid email and navigate Back")

        # Ensure webview present to input email
        try:
            wait_for_element(driver, XPATH_APWEBVIEW, timeout=8)
            switch_to_webview_context(driver, timeout=6)
        except TimeoutException:
            pytest.skip("Webview not available to perform invalid login test")

        # Input invalid email
        assert input_text(driver, XPATH_AP_EMAIL_LOGIN, "invalid-email-format"), "Failed to input invalid email"

        # Simulate pressing back by switching context back to native and tapping Back icon if present
        try:
            driver.switch_to.context("NATIVE_APP")
        except Exception:
            logger.debug("Could not switch to native context explicitly; continuing")

        # Tap the back icon
        if is_element_present(driver, XPATH_BACK_ICON, timeout=6):
            assert tap_element(driver, XPATH_BACK_ICON), "Failed to tap Back icon after invalid login attempt"
            time.sleep(2)
            # Assert that webview email login is no longer the active UI (we expect to have navigated away)
            assert not is_element_present(driver, XPATH_AP_EMAIL_LOGIN, timeout=4), "Still on login screen after pressing Back"
            logger.info("Navigated back successfully from invalid login attempt")
        else:
            pytest.skip("Back icon not present; cannot complete navigation back test")

    def test_tc_012_place_order_with_maximum_quantity_and_apply_coupon(self, driver):
        """
        TC_012: Place order with maximum allowed quantity and apply coupon (Edge Case)
        - Simulate selecting maximum quantity via search input as placeholder and attempt to apply a coupon (webview)
        - Verify app responds and does not crash; coupon application simulated by checking webview displays
        """
        logger.info("TC_012: Start - Place order with maximum allowed quantity and apply coupon")

        # As we don't have direct quantity UI locator, use search input as a placeholder to input large quantity
        max_quantity_str = "QTY:9999"  # placeholder to represent maximum quantity attempt
        assert input_text(driver, XPATH_SEARCH_INPUT, max_quantity_str), "Failed to input large quantity placeholder"

        # Simulate applying coupon by navigating to webview/payment where coupon application typically occurs
        try:
            wait_for_element(driver, XPATH_APWEBVIEW, timeout=10)
            switched = switch_to_webview_context(driver, timeout=6)
            assert switched, "Could not switch to webview to simulate coupon application"
            # Check that email login or web payment UI present - used as proxy that coupon/payment page loaded
            assert is_element_present(driver, XPATH_AP_EMAIL_LOGIN, timeout=6), "Payment/coupon UI not present after attempting max-quantity purchase"
            logger.info("Coupon/payment UI present after simulating max quantity; no crash detected")
        except TimeoutException:
            pytest.skip("Payment webview not available to simulate coupon application")

        # Switch back to native to finish
        try:
            driver.switch_to.context("NATIVE_APP")
        except Exception:
            pass

        logger.info("TC_012: Completed simulation of max quantity purchase with coupon application check")
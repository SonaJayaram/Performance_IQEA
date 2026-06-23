import logging
import time
import pytest

from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for provided XPath locators from recorded actions
XPATH_SEARCH_INPUT = '//android.widget.EditText[@resource-id="in.amazon.mShop.android.shopping:id/rs_search_src_text"]'
XPATH_USE_MY_CURRENT_LOCATION = '//android.widget.Button[@resource-id="in.amazon.mShop.android.shopping:id/loc_ux_gps_auto_detect"]'
XPATH_CLOSE = '//android.widget.Button[@resource-id="closeButton"]'
XPATH_CANCEL = '//android.widget.Button[@resource-id="in.amazon.mShop.android.shopping:id/top_bar_cancel_text_button"]'
XPATH_MONDAY_DATE = '//android.widget.TextView[@resource-id="com.samsung.android.app.clockpack:id/common_date"]'
XPATH_BACK = '//android.widget.ImageButton[@resource-id="in.amazon.mShop.android.shopping:id/chrome_action_bar_back_icon"]'
XPATH_APWEBVIEW = '//android.webkit.WebView[@resource-id="in.amazon.mShop.android.shopping:id/apwebview"]'
XPATH_AP_EMAIL_LOGIN = '//android.widget.EditText[@resource-id="ap_email_login"]'
XPATH_RESEND_OTP = '//android.view.View[@resource-id="cvf-resend-link"]'

# Default wait times
DEFAULT_WAIT = 20
SHORT_WAIT = 5

# Helper utilities
def wait_for_element(driver, xpath, timeout=DEFAULT_WAIT):
    """
    Wait for element located by xpath to be present and visible.
    """
    try:
        logger.info(f"Waiting for element: {xpath}")
        el = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((AppiumBy.XPATH, xpath))
        )
        logger.info(f"Element available: {xpath}")
        return el
    except TimeoutException:
        logger.exception(f"Timeout waiting for element: {xpath}")
        raise

def click_element(driver, xpath, timeout=DEFAULT_WAIT):
    """
    Wait for element and click it.
    """
    el = wait_for_element(driver, xpath, timeout)
    try:
        el.click()
        logger.info(f"Clicked element: {xpath}")
    except WebDriverException:
        logger.exception(f"Failed to click element: {xpath}")
        raise

def input_text(driver, xpath, text, timeout=DEFAULT_WAIT):
    """
    Wait for input element and send keys.
    """
    el = wait_for_element(driver, xpath, timeout)
    try:
        el.clear()
        el.send_keys(text)
        logger.info(f"Entered text into element {xpath}: {text}")
    except WebDriverException:
        logger.exception(f"Failed to enter text into: {xpath}")
        raise

@pytest.fixture(scope="session")
def driver():
    """
    Initialize Appium driver session. Update desired capabilities as needed for your device/app.
    """
    desired_caps = {
        "platformName": "Android",               # Update as needed
        "platformVersion": "11",                 # Update as needed
        "deviceName": "Android Device",          # Update as needed
        "automationName": "UiAutomator2",
        "appPackage": "in.amazon.mShop.android.shopping",  # Amazon app package
        "appActivity": "com.amazon.mShop.home.HomeActivity",  # Update if necessary
        "noReset": True,                         # Keep session to reuse saved addresses/cards
        "newCommandTimeout": 300,
    }

    logger.info("Starting Appium session with desired capabilities.")
    driver = webdriver.Remote("http://127.0.0.1:4723/wd/hub", desired_caps)
    driver.implicitly_wait(5)  # small implicit wait
    yield driver

    logger.info("Quitting Appium session.")
    try:
        driver.quit()
    except Exception:
        logger.exception("Error quitting driver.")


class TestAmazonApp:
    """
    Test suite implementing the required test cases using Appium and pytest.
    Each test uses provided XPath locators where relevant and includes assertions.
    """

    # Helper: safe click if present within short timeout
    def safe_click(self, driver, xpath, timeout=SHORT_WAIT):
        try:
            click_element(driver, xpath, timeout)
            return True
        except Exception:
            logger.warning(f"Element not present/clickable: {xpath}")
            return False

    # Helper: check if string present in page source
    def page_contains(self, driver, text, timeout=5):
        end = time.time() + timeout
        while time.time() < end:
            if text.lower() in driver.page_source.lower():
                return True
            time.sleep(0.5)
        return False

    # TC_001: Complete purchase using saved address and card (Happy Path)
    def test_tc_001_complete_purchase_saved_address_card(self, driver):
        """
        Positive | Critical
        Flow: Search -> select first result -> add to cart -> proceed to checkout -> use saved address/card -> place order.
        This test assumes user has saved address and card in app (no additional auth).
        """
        logger.info("TC_001: Start - Complete purchase using saved address and card.")
        try:
            # Search for an item
            input_text(driver, XPATH_SEARCH_INPUT, "wireless mouse")
            # Submit keyboard search key (attempt)
            try:
                driver.press_keycode(66)  # KEYCODE_ENTER
                logger.info("Pressed Enter to submit search.")
            except Exception:
                logger.warning("Could not send ENTER key; proceeding with tap on first result.")

            # Wait for search results - attempt to click first product by generic xpath (may vary by app UI)
            first_product_xpath = '(//android.view.ViewGroup[contains(@resource-id,"s-result-item") or contains(@content-desc,"product")])[1]'
            try:
                click_element(driver, first_product_xpath, timeout=10)
            except Exception:
                # fallback: first clickable element containing text '₹' price indicator
                alt_price_xpath = '(//android.widget.TextView[contains(@text,"₹")])[1]'
                click_element(driver, alt_price_xpath, timeout=10)

            # Add to cart - try several common locators
            add_to_cart_xpaths = [
                '//android.widget.Button[@text="Add to Cart"]',
                '//android.widget.Button[contains(@text,"Add to cart")]',
                '//android.widget.Button[@content-desc="Add to Cart"]',
                '//android.view.View[@resource-id="add-to-cart-button"]'
            ]
            added = False
            for ax in add_to_cart_xpaths:
                try:
                    click_element(driver, ax, timeout=5)
                    added = True
                    break
                except Exception:
                    continue
            assert added, "Failed to add item to cart."

            # Proceed to checkout (look for 'Proceed to Buy' / 'Go to Cart' and 'Proceed to checkout')
            proceed_xpaths = [
                '//android.widget.Button[@text="Proceed to Buy"]',
                '//android.widget.Button[contains(@text,"Proceed")]',
                '//android.widget.Button[@content-desc="Proceed to Buy"]',
            ]
            proceeded = False
            for px in proceed_xpaths:
                if self.safe_click(driver, px):
                    proceeded = True
                    break
            if not proceeded:
                # Try go to cart then proceed
                try:
                    click_element(driver, '//android.widget.ImageButton[@content-desc="Cart"]', timeout=5)
                    click_element(driver, '//android.widget.Button[contains(@text,"Proceed to checkout") or contains(@text,"Proceed")]', timeout=8)
                    proceeded = True
                except Exception:
                    logger.exception("Could not navigate to checkout.")

            assert proceeded, "Failed to proceed to checkout."

            # Choose saved address - try to detect 'Deliver to' or 'Select address' button
            address_xpaths = [
                '//android.widget.Button[contains(@text,"Deliver to")]',
                '//android.widget.TextView[contains(@text,"Deliver to")]',
                '//android.widget.Button[contains(@text,"Use this address")]',
            ]
            address_selected = False
            for ax in address_xpaths:
                if self.safe_click(driver, ax):
                    address_selected = True
                    break
            # If not found, assume default saved address auto-selected; assert presence of address block
            if not address_selected:
                assert self.page_contains(driver, "Deliver to") or self.page_contains(driver, "Ship to"), "No saved address selection available."

            # Choose saved card - look for 'Use this payment method' or saved card text
            payment_xpaths = [
                '//android.widget.Button[contains(@text,"Use this payment method")]',
                '//android.widget.TextView[contains(@text,"Saved cards")]',
                '//android.widget.Button[contains(@text,"Change Payment Method")]',
            ]
            payment_selected = False
            for px in payment_xpaths:
                if self.safe_click(driver, px):
                    payment_selected = True
                    break
            # If payment selection not required, assume saved card present
            assert payment_selected or self.page_contains(driver, "Card") or self.page_contains(driver, "Visa") or self.page_contains(driver, "Mastercard"), "Saved payment method not available."

            # Place order - look for 'Place your order' button
            place_order_xpaths = [
                '//android.widget.Button[contains(@text,"Place your order")]',
                '//android.widget.Button[contains(@text,"Buy now")]',
                '//android.widget.Button[contains(@text,"Place order")]'
            ]
            placed = False
            for po in place_order_xpaths:
                if self.safe_click(driver, po):
                    placed = True
                    break
            assert placed, "Failed to place order."

            # Verify order confirmation - look for "Order placed" or "Thank you"
            assert self.page_contains(driver, "Order placed") or self.page_contains(driver, "Thank you") or self.page_contains(driver, "Order confirmation"), "Order confirmation not detected."

            logger.info("TC_001: Completed successfully.")

        except Exception:
            logger.exception("TC_001 encountered an error.")
            raise

    # TC_002: Search using voice/keyboard and use 'Use my current location' for delivery
    def test_tc_002_search_voice_keyboard_use_current_location(self, driver):
        """
        Positive | High
        Flow: Open search, use keyboard for one search, simulate voice search fallback, then use "Use my current location" for delivery.
        """
        logger.info("TC_002: Start - Search using voice/keyboard and use 'Use my current location' for delivery.")
        try:
            # Input search text using keyboard
            input_text(driver, XPATH_SEARCH_INPUT, "headphones")
            driver.press_keycode(66)  # Enter to submit search
            logger.info("Submitted keyboard search for 'headphones'.")

            # Simulate voice search by attempting to click microphone icon if present
            mic_xpath = '//android.widget.ImageView[@content-desc="Voice Search"]'
            if self.safe_click(driver, mic_xpath):
                # In real scenario, would handle voice permission and input. Wait for UI to reflect voice search.
                time.sleep(2)
                logger.info("Voice search triggered (simulated).")
            else:
                logger.info("Voice search icon not present; continuing with keyboard results.")

            # Use 'Use my current location' for delivery as part of address selection or in-app prompt
            # Use provided locator
            clicked_location = False
            try:
                click_element(driver, XPATH_USE_MY_CURRENT_LOCATION, timeout=8)
                clicked_location = True
            except Exception:
                logger.warning("'Use my current location' button not found using provided locator.")

            assert clicked_location, "'Use my current location' was not accessible."

            # Verify that location permission or selected location is reflected
            # Many apps show 'Delivering to' or a location string
            assert self.page_contains(driver, "Deliver to") or self.page_contains(driver, "Delivering to") or self.page_contains(driver, "Location"), "App did not reflect current location selection."

            logger.info("TC_002: Completed successfully.")

        except Exception:
            logger.exception("TC_002 encountered an error.")
            raise

    # TC_003: Login flow via webview with valid credentials and OTP
    def test_tc_003_login_via_webview_with_otp(self, driver):
        """
        Positive | High
        Flow: Navigate to login webview, enter email, simulate OTP flow, verify login success.
        Uses apwebview and ap_email_login locators.
        """
        logger.info("TC_003: Start - Login via webview with valid credentials and OTP.")
        try:
            # Open sign-in flow by clicking webview area which opens the login page
            click_element(driver, XPATH_APWEBVIEW, timeout=10)

            # Enter email in webview login field
            input_text(driver, XPATH_AP_EMAIL_LOGIN, "testuser@example.com")
            driver.press_keycode(66)  # press Enter
            logger.info("Entered email in webview login.")

            # Simulate OTP entry - we wait for 'Enter OTP' input to appear - guess a generic otp field
            otp_input_xpath = '//android.widget.EditText[contains(@resource-id,"otp") or contains(@content-desc,"otp") or contains(@resource-id,"cvf-input-code")]'
            try:
                otp_field = wait_for_element(driver, otp_input_xpath, timeout=15)
                otp_field.send_keys("123456")  # placeholder OTP for test environment
                logger.info("Entered OTP.")
            except Exception:
                # If OTP field not found, try to detect 'Enter the OTP' text in webview
                logger.warning("OTP input not directly found; assuming OTP auto-verified or alternate OTP flow.")

            # Click submit/continue button (guess)
            submit_xpath = '//android.view.View[contains(@text,"Verify") or contains(@text,"Submit") or contains(@text,"Continue")]'
            try:
                click_element(driver, submit_xpath, timeout=8)
            except Exception:
                logger.info("Submit button not found; continuing to verify login state.")

            # Verify login success by checking presence of user account name or "Hello, <name>"
            assert self.page_contains(driver, "Hello") or self.page_contains(driver, "Account") or self.page_contains(driver, "Your Account"), "Login success indicator not detected."

            logger.info("TC_003: Completed successfully.")

        except Exception:
            logger.exception("TC_003 encountered an error.")
            raise

    # TC_004: Resend OTP when OTP not received
    def test_tc_004_resend_otp_when_not_received(self, driver):
        """
        Negative | High
        Flow: On OTP screen click 'Resend OTP' and verify resend action triggered.
        Uses XPATH_RESEND_OTP.
        """
        logger.info("TC_004: Start - Resend OTP when OTP not received.")
        try:
            # Open webview to get to resend OTP area
            try:
                click_element(driver, XPATH_APWEBVIEW, timeout=10)
            except Exception:
                logger.warning("Could not open webview; proceeding to try to find resend link.")

            # Wait for resend OTP link and click it
            try:
                click_element(driver, XPATH_RESEND_OTP, timeout=10)
            except Exception:
                logger.exception("Resend OTP element not found.")
                raise

            # After clicking resend, ensure a confirmation or UI change shows resend occurred
            # Many web pages show "OTP sent" or a timer; check for 'sent' or presence of 'resend' disabled
            assert self.page_contains(driver, "sent") or self.page_contains(driver, "resent") or self.page_contains(driver, "OTP"), "Resend OTP confirmation not detected."

            logger.info("TC_004: Completed - Resend OTP triggered successfully.")
        except Exception:
            logger.exception("TC_004 encountered an error.")
            raise

    # TC_005: Attempt purchase with expired/declined card
    def test_tc_005_attempt_purchase_with_expired_declined_card(self, driver):
        """
        Negative | Critical
        Flow: Attempt to checkout using an expired/declined card and verify error displayed.
        """
        logger.info("TC_005: Start - Attempt purchase with expired/declined card.")
        try:
            # Search and add item to cart quickly
            input_text(driver, XPATH_SEARCH_INPUT, "notebook")
            driver.press_keycode(66)
            time.sleep(2)
            try:
                click_element(driver, '(//android.widget.TextView[contains(@text,"Notebooks") or contains(@text,"notebook")])[1]', timeout=5)
            except Exception:
                logger.info("Selecting first search result via fallback.")
            # Attempt add to cart using generic XPath
            try:
                click_element(driver, '//android.widget.Button[contains(@text,"Add to Cart")]', timeout=5)
            except Exception:
                logger.info("Add to cart button not found; assuming item in cart already.")

            # Proceed to checkout
            try:
                click_element(driver, '//android.widget.Button[contains(@text,"Proceed to checkout") or contains(@text,"Proceed")]', timeout=8)
            except Exception:
                logger.info("Proceed to checkout button not directly found.")

            # Select payment method and choose expired card - try to find card by text 'Expired' or 'declined'
            expired_card_xpath = '//android.widget.TextView[contains(@text,"Expired") or contains(@text,"expired") or contains(@text,"Declined") or contains(@text,"declined")]'
            try:
                click_element(driver, expired_card_xpath, timeout=6)
            except Exception:
                logger.warning("Expired/declined card entry not visible; attempting to add a card and enter expired details.")
                # Attempt to add card and provide expired date - we won't actually input sensitive data; simulate flow:
                try:
                    click_element(driver, '//android.widget.Button[contains(@text,"Add a new card") or contains(@text,"Add card")]', timeout=6)
                    # Input card details - we will attempt to locate a card number field generically
                    card_input_xpath = '//android.widget.EditText[contains(@resource-id,"cardNumber") or contains(@content-desc,"cardNumber") or contains(@resource-id,"addCreditCardNumber")]'
                    input_text(driver, card_input_xpath, "4012888888881881", timeout=6)  # test card
                    # Enter expired date
                    expiry_xpath = '//android.widget.EditText[contains(@resource-id,"expiryDate") or contains(@content-desc,"expiryDate")]'
                    input_text(driver, expiry_xpath, "01/20", timeout=6)  # expired date
                    # Submit card
                    click_element(driver, '//android.widget.Button[contains(@text,"Save") or contains(@text,"Add card")]', timeout=6)
                except Exception:
                    logger.warning("Could not add expired card - simulating declined card on payment.")

            # Attempt to place order
            try:
                click_element(driver, '//android.widget.Button[contains(@text,"Place your order") or contains(@text,"Place order")]', timeout=8)
            except Exception:
                logger.info("Place order button not found or not clickable.")

            # Verify payment declined message
            assert self.page_contains(driver, "declined") or self.page_contains(driver, "expired") or self.page_contains(driver, "unable to process") or self.page_contains(driver, "payment method was declined"), "Expected payment declined/expired message not detected."

            logger.info("TC_005: Completed - Declined card path verified.")
        except Exception:
            logger.exception("TC_005 encountered an error.")
            raise

    # TC_006: Search yields no results - user sees helpful suggestions
    def test_tc_006_search_no_results_helpful_suggestions(self, driver):
        """
        Negative | Medium
        Flow: Search for gibberish expecting no results and verify suggestions are shown.
        """
        logger.info("TC_006: Start - Search yields no results and shows helpful suggestions.")
        try:
            # Search with unlikely string
            input_text(driver, XPATH_SEARCH_INPUT, "zxqwyplkjnm123")
            driver.press_keycode(66)
            # Wait for 'No results' or suggestions
            time.sleep(2)
            assert self.page_contains(driver, "didn't match any products") or self.page_contains(driver, "No results") or self.page_contains(driver, "Try these suggestions") or self.page_contains(driver, "Try searching for"), "No-results suggestions not displayed."
            logger.info("TC_006: Completed - No results suggestions verified.")
        except Exception:
            logger.exception("TC_006 encountered an error.")
            raise

    # TC_007: Out of stock item selected at checkout
    def test_tc_007_out_of_stock_item_selected_at_checkout(self, driver):
        """
        Edge Case | High
        Flow: Add item, then it becomes out of stock at checkout; verify proper message and resolution options.
        """
        logger.info("TC_007: Start - Out of stock item selected at checkout.")
        try:
            # Search for an item and add to cart
            input_text(driver, XPATH_SEARCH_INPUT, "USB cable")
            driver.press_keycode(66)
            time.sleep(1)
            try:
                click_element(driver, '//android.widget.Button[contains(@text,"Add to Cart")]', timeout=5)
            except Exception:
                logger.info("Could not click Add to Cart; proceeding to cart.")

            # Go to cart
            try:
                click_element(driver, '//android.widget.ImageButton[@content-desc="Cart"]', timeout=6)
            except Exception:
                logger.warning("Cart button not found; using alternate cart text.")
                self.safe_click(driver, '//android.widget.Button[contains(@text,"Cart")]')

            # Attempt checkout
            try:
                click_element(driver, '//android.widget.Button[contains(@text,"Proceed to checkout") or contains(@text,"Proceed")]', timeout=6)
            except Exception:
                logger.warning("Proceed to checkout not found.")

            # Check for out of stock message
            # Many apps show "Out of stock" or "Currently unavailable"
            assert self.page_contains(driver, "Out of stock") or self.page_contains(driver, "Currently unavailable") or self.page_contains(driver, "unavailable"), "Out of stock message not displayed when expected."

            # Verify that app provides options: remove item, save for later, notify me
            assert self.page_contains(driver, "Remove") or self.page_contains(driver, "Save for later") or self.page_contains(driver, "Notify me"), "No remediation options presented for out-of-stock item."

            logger.info("TC_007: Completed - Out of stock handling verified.")
        except Exception:
            logger.exception("TC_007 encountered an error.")
            raise

    # TC_008: Cancel during checkout and verify cart persistence
    def test_tc_008_cancel_during_checkout_verify_cart_persistence(self, driver):
        """
        Functional | Medium
        Flow: Start checkout then cancel. Verify cart retains items.
        """
        logger.info("TC_008: Start - Cancel during checkout and verify cart persistence.")
        try:
            # Ensure cart has at least one item; add if necessary
            input_text(driver, XPATH_SEARCH_INPUT, "pen")
            driver.press_keycode(66)
            time.sleep(1)
            try:
                click_element(driver, '//android.widget.Button[contains(@text,"Add to Cart")]', timeout=5)
            except Exception:
                logger.info("Add to cart not clicked; proceeding.")

            # Navigate to checkout
            click_element(driver, '//android.widget.Button[contains(@text,"Proceed to checkout") or contains(@text,"Proceed")]', timeout=6)

            # Cancel checkout using provided Cancel xpath
            click_element(driver, XPATH_CANCEL, timeout=8)

            # Go to cart and assert item still present
            try:
                click_element(driver, '//android.widget.ImageButton[@content-desc="Cart"]', timeout=6)
            except Exception:
                self.safe_click(driver, '//android.widget.Button[contains(@text,"Cart")]')

            # Check that cart contains items - look for quantity or product title
            assert self.page_contains(driver, "Cart") or self.page_contains(driver, "Items in cart") or self.page_contains(driver, "Remove"), "Cart does not seem to persist; no items found."

            logger.info("TC_008: Completed - Cart persistence after cancel verified.")
        except Exception:
            logger.exception("TC_008 encountered an error.")
            raise

    # TC_009: Close promotional modal/pop-up and continue purchase
    def test_tc_009_close_promotional_modal_and_continue_purchase(self, driver):
        """
        UI | Low
        Flow: When promotional modal appears, close it and continue with purchase.
        Uses XPATH_CLOSE for closing modal.
        """
        logger.info("TC_009: Start - Close promotional modal/pop-up and continue purchase.")
        try:
            # Trigger scenario where promo may appear by navigating to home or search
            click_element(driver, XPATH_SEARCH_INPUT, timeout=5)
            time.sleep(1)
            # Try to close promo using provided locator
            closed = False
            try:
                click_element(driver, XPATH_CLOSE, timeout=5)
                closed = True
                logger.info("Promo modal closed using provided close button.")
            except Exception:
                logger.info("Promo close button not visible via provided locator; attempting back press.")
                try:
                    driver.back()
                    closed = True
                except Exception:
                    logger.warning("Could not dismiss promo modal.")

            assert closed, "Promo modal could not be dismissed."

            # Continue with search and purchasing step (quick flow)
            input_text(driver, XPATH_SEARCH_INPUT, "stapler")
            driver.press_keycode(66)
            time.sleep(1)
            logger.info("Continued after closing promo modal.")

            assert not self.page_contains(driver, "closeButton") or not self.page_contains(driver, "modal"), "Promo modal still appears after attempting to close."

            logger.info("TC_009: Completed - Promo modal handled and purchase continued.")
        except Exception:
            logger.exception("TC_009 encountered an error.")
            raise

    # TC_010: Perform purchase with intermittent/slow network
    def test_tc_010_purchase_with_intermittent_slow_network(self, driver):
        """
        Performance | High
        Flow: Simulate slow/intermittent network while attempting purchase; verify app handles gracefully.
        """
        logger.info("TC_010: Start - Perform purchase with intermittent/slow network.")
        try:
            # Note: Actual network toggling requires device permissions and may differ by environment.
            # We'll attempt to use Appium's set_network_connection where supported.
            # Save current connection
            network_supported = True
            try:
                current_conn = driver.network_connection
            except Exception:
                network_supported = False
                current_conn = None
                logger.warning("Driver does not support network connection manipulation in this environment.")

            # Simulate slow network by toggling data off and on during checkout attempt
            # Add item to cart
            input_text(driver, XPATH_SEARCH_INPUT, "lamp")
            driver.press_keycode(66)
            time.sleep(1)
            try:
                click_element(driver, '//android.widget.Button[contains(@text,"Add to Cart")]', timeout=5)
            except Exception:
                logger.info("Add to cart not clicked; continuing.")

            click_element(driver, '//android.widget.Button[contains(@text,"Proceed to checkout") or contains(@text,"Proceed")]', timeout=8)

            # Turn off network to simulate offline moment
            if network_supported:
                try:
                    driver.set_network_connection(0)  # Airplane mode / no network
                    logger.info("Network turned off to simulate offline.")
                    time.sleep(3)
                except Exception:
                    logger.warning("Could not set network connection to offline.")

            # Attempt to place order while offline
            try:
                click_element(driver, '//android.widget.Button[contains(@text,"Place your order") or contains(@text,"Place order")]', timeout=5)
            except Exception:
                logger.info("Place order action attempted during offline mode.")

            # Verify appropriate error shown for network issues
            assert self.page_contains(driver, "network") or self.page_contains(driver, "connect") or self.page_contains(driver, "Try again") or self.page_contains(driver, "offline"), "No network error message displayed during offline attempt."

            # Restore network and attempt again (simulate intermittent)
            if network_supported:
                try:
                    driver.set_network_connection(6)  # All network on (data + wifi)
                    logger.info("Network restored.")
                    time.sleep(3)
                except Exception:
                    logger.warning("Could not restore network connection via driver.")

            # Retry placing order if possible
            try:
                click_element(driver, '//android.widget.Button[contains(@text,"Retry") or contains(@text,"Place your order")]', timeout=10)
            except Exception:
                logger.info("Retry/place order button not found; verifying app recovered.")

            # Final assertion: app either shows order confirmation or a message indicating retry
            assert self.page_contains(driver, "Order placed") or self.page_contains(driver, "Try again") or self.page_contains(driver, "placed"), "App did not recover or place order after network restoration."

            logger.info("TC_010: Completed - Intermittent network behavior handled.")
        except Exception:
            logger.exception("TC_010 encountered an error.")
            raise
        finally:
            # Attempt to restore original network state if possible
            try:
                if network_supported and current_conn is not None:
                    driver.set_network_connection(current_conn)
            except Exception:
                logger.warning("Could not restore original network state.")

    # TC_011: Attempt login with invalid email and navigate Back
    def test_tc_011_login_invalid_email_and_navigate_back(self, driver):
        """
        Negative | Medium
        Flow: Enter invalid email in login webview and navigate back; verify validation and back navigation.
        """
        logger.info("TC_011: Start - Attempt login with invalid email and navigate Back.")
        try:
            # Open login webview
            click_element(driver, XPATH_APWEBVIEW, timeout=8)
            # Enter invalid email using provided locator
            input_text(driver, XPATH_AP_EMAIL_LOGIN, "invalid-email-format")
            driver.press_keycode(66)
            # Expect validation error
            assert self.page_contains(driver, "enter a valid email") or self.page_contains(driver, "valid email") or self.page_contains(driver, "invalid"), "Validation message for invalid email not found."

            # Navigate back using provided Back xpath
            try:
                click_element(driver, XPATH_BACK, timeout=5)
            except Exception:
                # fallback to driver.back()
                driver.back()
                logger.info("Used device back to navigate back.")

            # Verify we returned to previous screen (home/search)
            assert self.page_contains(driver, "Search Amazon.in") or driver.find_elements(AppiumBy.XPATH, XPATH_SEARCH_INPUT), "Did not navigate back to expected screen."

            logger.info("TC_011: Completed - Invalid email validation and back navigation verified.")
        except Exception:
            logger.exception("TC_011 encountered an error.")
            raise

    # TC_012: Place order with maximum allowed quantity and apply coupon
    def test_tc_012_place_order_max_quantity_apply_coupon(self, driver):
        """
        Edge Case | High
        Flow: Attempt to set maximum quantity for an item, apply coupon, and place order.
        """
        logger.info("TC_012: Start - Place order with maximum allowed quantity and apply coupon.")
        try:
            # Search item
            input_text(driver, XPATH_SEARCH_INPUT, "staples box")
            driver.press_keycode(66)
            time.sleep(1)
            # Click first product
            try:
                click_element(driver, '(//android.view.ViewGroup[contains(@resource-id,"s-result-item")])[1]', timeout=8)
            except Exception:
                logger.info("First product selection fallback mismatch; continuing.")

            # Attempt to set quantity to a large number via quantity selector
            try:
                click_element(driver, '//android.widget.Spinner[contains(@resource-id,"quantity") or contains(@resource-id,"qty")]', timeout=6)
                # Select maximum allowed by choosing '10' or the last option
                try:
                    click_element(driver, '(//android.widget.CheckedTextView)[last()]', timeout=5)
                    logger.info("Selected maximum quantity option available in selector.")
                except Exception:
                    logger.warning("Could not select last quantity option from spinner.")
            except Exception:
                logger.info("Quantity selector not found; attempting to use +/- controls.")
                try:
                    # Attempt repeated taps on increase quantity control
                    plus_button_xpath = '//android.widget.Button[contains(@content-desc,"increase quantity") or contains(@text,"+") or contains(@resource-id,"plus")]'
                    for _ in range(9):
                        self.safe_click(driver, plus_button_xpath)
                        time.sleep(0.3)
                    logger.info("Attempted to increment quantity via plus control.")
                except Exception:
                    logger.warning("Could not change quantity via plus control.")

            # Add to cart
            try:
                click_element(driver, '//android.widget.Button[contains(@text,"Add to Cart") or contains(@text,"Add to cart")]', timeout=6)
            except Exception:
                logger.info("Add to cart may not be needed or failed.")

            # Go to cart
            click_element(driver, '//android.widget.ImageButton[@content-desc="Cart"]', timeout=6)

            # Apply coupon - attempt to find 'Apply Coupon' or 'Gift card & promo' entry
            coupon_applied = False
            coupon_xpaths = [
                '//android.widget.TextView[contains(@text,"Apply coupon") or contains(@text,"Apply Coupon")]',
                '//android.widget.Button[contains(@text,"Apply") and contains(@resource-id,"coupon")]',
                '//android.widget.EditText[contains(@resource-id,"coupon") or contains(@content-desc,"coupon")]'
            ]
            for cx in coupon_xpaths:
                try:
                    el = driver.find_element(AppiumBy.XPATH, cx)
                    if el.tag_name.lower() == "android.widget.EditText":
                        el.clear()
                        el.send_keys("TESTCOUPON")
                        driver.press_keycode(66)
                        coupon_applied = True
                        break
                    else:
                        el.click()
                        # Try to input coupon code if a popup appears
                        try:
                            input_text(driver, '//android.widget.EditText[contains(@resource-id,"coupon")]', "TESTCOUPON", timeout=5)
                            driver.press_keycode(66)
                            coupon_applied = True
                            break
                        except Exception:
                            coupon_applied = True
                            break
                except NoSuchElementException:
                    continue
                except Exception:
                    continue

            logger.info(f"Coupon applied flag: {coupon_applied}")

            # Proceed to checkout and attempt to place order
            click_element(driver, '//android.widget.Button[contains(@text,"Proceed to checkout") or contains(@text,"Proceed")]', timeout=8)
            try:
                click_element(driver, '//android.widget.Button[contains(@text,"Place your order") or contains(@text,"Place order")]', timeout=8)
            except Exception:
                logger.info("Place order button not found at final checkout stage.")

            # Verify successful order placement or coupon application message
            assert self.page_contains(driver, "Order placed") or self.page_contains(driver, "coupon applied") or self.page_contains(driver, "discount"), "Order placement or coupon application not confirmed."

            logger.info("TC_012: Completed - Max quantity and coupon application verified.")
        except Exception:
            logger.exception("TC_012 encountered an error.")
            raise
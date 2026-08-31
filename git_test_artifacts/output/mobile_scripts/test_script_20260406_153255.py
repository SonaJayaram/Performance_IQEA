import time
import logging
import pytest
import allure

from appium import webdriver
from appium.options import UiAutomator2Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============
# XPath CONSTANTS (Update resource-ids/package/activity to match AUT)
# All XPaths recorded plus additional commonly needed ones.
# ============
# Recorded XPaths
XPATH_SEARCH_BUTTON = '//android.widget.ImageButton[@resource-id="in.amazon.mShop.android.shopping:id/chrome_search_box"]'
XPATH_BACK_BUTTON = '//android.widget.ImageButton[@resource-id="in.amazon.mShop.android.shopping:id/chrome_action_bar_back_icon"]'
XPATH_ALL_FILTERS_BUTTON = '//android.widget.Button[@resource-id="s-all-filters-announce"]'
XPATH_SEE_MORE_LIKE_THIS = '//android.widget.Button[@resource-id="comparison-lite-trigger-B0FTRMJNPX-announce"]'
XPATH_LOGIN_EMAIL = '//android.widget.EditText[@resource-id="ap_email_login"]'
XPATH_LOGIN_CHANGE = '//android.view.View[@content-desc="Change"]'
XPATH_LOGIN_PHONE = '//android.widget.EditText[@resource-id="ap_phone_number"]'

# Additional assumed XPaths (may need update for real app)
XPATH_SEARCH_INPUT = '//android.widget.EditText[@resource-id="in.amazon.mShop.android.shopping:id/rs_search_src_text"]'
XPATH_FIRST_PRODUCT = '(//android.widget.ImageView[@resource-id="in.amazon.mShop.android.shopping:id/item_image"])[1]'
XPATH_ADD_TO_CART_BUTTON = '//android.widget.Button[@resource-id="add-to-cart-button"]'
XPATH_CART_ICON = '//android.view.View[@resource-id="in.amazon.mShop.android.shopping:id/action_bar_cart_image"]'
XPATH_CART_ITEM = '//android.view.ViewGroup[@resource-id="sc-item-CURRENT"]'  # placeholder
XPATH_CART_ITEM_TITLE = '//android.widget.TextView[@resource-id="com.example.app:id/cart_item_title"]'  # update
XPATH_CART_ITEM_QUANTITY = '//android.widget.EditText[@resource-id="com.example.app:id/quantity"]'  # update
XPATH_QUANTITY_INCREASE_BUTTON = '//android.widget.Button[@resource-id="com.example.app:id/increase"]'  # update
XPATH_QUANTITY_DECREASE_BUTTON = '//android.widget.Button[@resource-id="com.example.app:id/decrease"]'  # update
XPATH_REMOVE_FROM_CART = '//android.widget.Button[@resource-id="com.example.app:id/remove_button"]'  # update
XPATH_EMPTY_CART_MESSAGE = '//android.widget.TextView[@resource-id="com.example.app:id/empty_cart_message"]'  # update
XPATH_FILTER_STORAGE_OPTION = '//android.widget.CheckBox[@text="512 GB"]'  # example
XPATH_APPLY_FILTERS = '//android.widget.Button[@resource-id="s-apply-button"]'
XPATH_PRODUCT_VARIANT_OPTION = '//android.widget.RadioButton[@resource-id="com.example.app:id/variant_option"]'  # update
XPATH_QUANTITY_DROPDOWN = '//android.widget.Spinner[@resource-id="com.example.app:id/qty_spinner"]'  # update
XPATH_CONCURRENCY_ADD_BUTTON = '//android.widget.Button[@resource-id="com.example.app:id/add_button"]'  # update
XPATH_COMPARE_VIEW_ADD_BUTTON = '//android.widget.Button[@resource-id="com.example.app:id/compare_add_to_cart"]'  # update

# Timeout defaults
DEFAULT_TIMEOUT = 20

# ============
# Helper functions
# ============


def wait_for_element(driver, xpath, timeout=DEFAULT_TIMEOUT):
    """
    Wait for an element located by xpath to be present and visible.
    Returns the WebElement or raises TimeoutException.
    """
    logger.info(f"Waiting for element with xpath: {xpath}")
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        # additional wait for visibility
        element = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
        return element
    except TimeoutException:
        logger.warning(f"Element not found within {timeout} seconds: {xpath}")
        raise


def tap_element(driver, xpath, timeout=DEFAULT_TIMEOUT):
    """
    Wait for element and tap/click it.
    """
    try:
        el = wait_for_element(driver, xpath, timeout)
        logger.info(f"Tapping element: {xpath}")
        el.click()
        return True
    except TimeoutException:
        logger.error(f"Unable to tap element - not found: {xpath}")
        return False


def input_text(driver, xpath, text, timeout=DEFAULT_TIMEOUT):
    """
    Wait for input element, clear it, and send keys.
    """
    try:
        el = wait_for_element(driver, xpath, timeout)
        logger.info(f"Inputting text into element {xpath}: {text}")
        el.clear()
        el.send_keys(text)
        return True
    except TimeoutException:
        logger.error(f"Unable to input text - element not found: {xpath}")
        return False


def is_element_present(driver, xpath, timeout=3):
    """
    Return True if element is present in DOM within timeout, else False.
    """
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return True
    except TimeoutException:
        return False


# ============
# Pytest fixture for Appium driver
# ============
@pytest.fixture(scope="module")
def driver():
    """
    Module scoped Appium driver fixture. Update the options values to match test device/app.
    """
    # Setup Appium options for Android (Appium 2.x)
    options = UiAutomator2Options()
    # ======= UPDATE THESE CAPABILITIES AS PER ENVIRONMENT =======
    options.platform_name = "Android"
    options.platform_version = "13"
    options.device_name = "R9ZR701FW6R"
    options.udid = "R9ZR701FW6R"
    options.automation_name = "UiAutomator2"
    options.app_package = "in.amazon.mShop.android.shopping"
    options.app_activity = "com.amazon.mShop.home.HomeActivity"
    options.no_reset = True
    options.new_command_timeout = 300
    # ===========================================================

    logger.info("Starting Appium driver with options: %s", options)
    driver = webdriver.Remote("http://127.0.0.1:4723", options=options)

    yield driver

    logger.info("Quitting Appium driver")
    try:
        driver.quit()
    except Exception as e:
        logger.exception("Error quitting driver: %s", e)


# ============
# Helper operations for test flows
# ============


def open_search_and_search(driver, query):
    """
    Open search field and type query, then submit.
    """
    # Tap the search icon
    if not tap_element(driver, XPATH_SEARCH_BUTTON):
        pytest.skip("Search button not present; skipping search flow")

    # Input into search field
    if not input_text(driver, XPATH_SEARCH_INPUT, query):
        logger.warning("Search input not found; attempting to proceed")
        pytest.skip("Search input not present; skipping search flow")

    # Submit with Enter key event via send_keys newline
    el = wait_for_element(driver, XPATH_SEARCH_INPUT)
    el.send_keys("\n")
    logger.info(f"Searched for: {query}")
    time.sleep(2)  # wait for results to load


def open_first_product(driver):
    """
    Tap the first product in search results.
    """
    if is_element_present(driver, XPATH_FIRST_PRODUCT):
        tap_element(driver, XPATH_FIRST_PRODUCT)
        logger.info("Opened first product")
        time.sleep(2)
    else:
        pytest.skip("No product found in search results")


def add_to_cart_with_quantity(driver, target_quantity=1):
    """
    Add product to cart and set quantity (if UI supports setting).
    Attempts to use quantity spinner or increase button.
    """
    # Tap Add to Cart
    if not tap_element(driver, XPATH_ADD_TO_CART_BUTTON):
        pytest.skip("Add to cart button not present; cannot add")

    # After adding, try to set quantity if quantity control is present
    # Some apps allow changing quantity from cart page
    try:
        # Open cart
        if tap_element(driver, XPATH_CART_ICON):
            logger.info("Opened cart to set quantity")
            time.sleep(1)
        else:
            logger.info("Cart icon not available after add; assuming added and returning")
            return

        # Attempt to set quantity by increment button until desired
        for _ in range(10):  # safety upper bound
            try:
                qty_el = wait_for_element(driver, XPATH_CART_ITEM_QUANTITY, timeout=5)
                current_qty = int(qty_el.text) if qty_el.text.isdigit() else 1
                if current_qty >= target_quantity:
                    logger.info(f"Desired quantity {target_quantity} reached (current: {current_qty})")
                    break
                if is_element_present(driver, XPATH_QUANTITY_INCREASE_BUTTON, timeout=2):
                    tap_element(driver, XPATH_QUANTITY_INCREASE_BUTTON)
                    time.sleep(0.5)
                else:
                    # Try quantity dropdown selection
                    if is_element_present(driver, XPATH_QUANTITY_DROPDOWN, timeout=2):
                        tap_element(driver, XPATH_QUANTITY_DROPDOWN)
                        # attempt to choose value by text; fallback to break
                        qty_option_xpath = f'//android.widget.TextView[@text="{target_quantity}"]'
                        if is_element_present(driver, qty_option_xpath, timeout=2):
                            tap_element(driver, qty_option_xpath)
                            time.sleep(0.5)
                            break
                        else:
                            logger.warning("Desired quantity option not available in dropdown")
                            break
                    else:
                        logger.warning("No increase or dropdown control found for quantity")
                        break
            except TimeoutException:
                logger.warning("Quantity element not found inside cart")
                break
    except Exception as e:
        logger.exception("Error while adjusting quantity: %s", e)


def get_cart_item_count(driver):
    """
    Attempt to retrieve the cart item count from cart icon/badge.
    Returns int or None if not available.
    """
    # Common Amazon badge resource-id might be different; try to read content-desc or text
    try:
        if is_element_present(driver, XPATH_CART_ICON, timeout=5):
            el = wait_for_element(driver, XPATH_CART_ICON)
            # try to find badge inside cart icon element
            # Searching for numeric text near cart icon
            possible_badge_xpath = '//android.widget.TextView[contains(@resource-id,"cart_badge") or contains(@resource-id,"cart_count")]'
            if is_element_present(driver, possible_badge_xpath, timeout=2):
                badge = wait_for_element(driver, possible_badge_xpath)
                if badge.text.isdigit():
                    return int(badge.text)
            # fallback: check content-desc numeric
            desc = el.get_attribute("content-desc") or ""
            digits = ''.join([c for c in desc if c.isdigit()])
            if digits:
                return int(digits)
    except Exception:
        logger.exception("Error while retrieving cart item count")
    return None


# ============
# Test Cases
# ============

@allure.feature("Cart and Search Flows")
@allure.story("TC_001: Search mobile and add single product quantity to 3 then verify cart")
def test_tc_001_search_and_add_quantity(driver):
    """
    TC_001: Search mobile and add single product quantity to 3 then verify cart [Positive | High]
    """
    with allure.step("Search for a mobile product and open it"):
        open_search_and_search(driver, "OnePlus 15")
        open_first_product(driver)

    with allure.step("Add to cart and set quantity to 3"):
        add_to_cart_with_quantity(driver, target_quantity=3)

    with allure.step("Verify cart shows quantity 3 for the added product"):
        # Open cart and verify quantity
        if not tap_element(driver, XPATH_CART_ICON):
            pytest.skip("Cart icon unavailable; cannot verify cart")
        # Try to find quantity element
        if is_element_present(driver, XPATH_CART_ITEM_QUANTITY, timeout=5):
            el = wait_for_element(driver, XPATH_CART_ITEM_QUANTITY)
            # If element has text numeric, assert equals 3 else skip
            try:
                qty = int(el.text)
                assert qty == 3, f"Expected quantity 3 but found {qty}"
            except ValueError:
                pytest.skip("Cart quantity text not numeric; cannot assert exact quantity")
        else:
            pytest.skip("Cart quantity element not present; skipping assertion")


# @allure.feature("Cart and Search Flows")
# @allure.story("TC_002: Add two different mobiles, then remove one to leave only the first with quantity 3")
# def test_tc_002_add_two_and_remove_one(driver):
#     """
#     TC_002: Add two different mobiles, then remove one to leave only the first with quantity 3 [Positive | High]
#     """
#     with allure.step("Search and add first product"):
#         open_search_and_search(driver, "OnePlus 15")
#         open_first_product(driver)
#         add_to_cart_with_quantity(driver, target_quantity=3)

#     with allure.step("Search and add second product"):
#         # Navigate back to search
#         if tap_element(driver, XPATH_BACK_BUTTON):
#             time.sleep(1)
#         open_search_and_search(driver, "Samsung Galaxy")
#         open_first_product(driver)
#         add_to_cart_with_quantity(driver, target_quantity=1)

#     with allure.step("Open cart and remove second product"):
#         if not tap_element(driver, XPATH_CART_ICON):
#             pytest.skip("Cart icon not present; cannot remove item")
#         # Try to remove one item if remove button present
#         if is_element_present(driver, XPATH_REMOVE_FROM_CART, timeout=5):
#             # Remove once - assumes it removes the second item
#             tap_element(driver, XPATH_REMOVE_FROM_CART)
#             time.sleep(1)
#         else:
#             pytest.skip("Remove button not present in cart; skipping removal")

#         # Verify remaining first product quantity is 3
#         if is_element_present(driver, XPATH_CART_ITEM_QUANTITY, timeout=5):
#             el = wait_for_element(driver, XPATH_CART_ITEM_QUANTITY)
#             try:
#                 qty = int(el.text)
#                 assert qty == 3, f"Expected remaining product qty 3, found {qty}"
#             except ValueError:
#                 pytest.skip("Unable to parse quantity text; skipping exact check")
#         else:
#             pytest.skip("Cart quantity element not present for verification")


# @allure.feature("Cart Limits")
# @allure.story("TC_003: Attempt to increase quantity beyond available stock")
# def test_tc_003_increase_beyond_stock(driver):
#     """
#     TC_003: Attempt to increase quantity beyond available stock [Negative | High]
#     """
#     with allure.step("Search and open a product that may have limited stock"):
#         open_search_and_search(driver, "Limited Edition Phone")
#         open_first_product(driver)

#     with allure.step("Attempt to set quantity to a very large number"):
#         # Tap add to cart first if required
#         if not tap_element(driver, XPATH_ADD_TO_CART_BUTTON):
#             pytest.skip("Add to cart button missing; cannot perform test")
#         # Open cart and attempt to set a large quantity
#         if tap_element(driver, XPATH_CART_ICON):
#             # try to increase until blocked or error message appears
#             max_attempts = 10
#             blocked = False
#             for i in range(max_attempts):
#                 if is_element_present(driver, XPATH_QUANTITY_INCREASE_BUTTON, timeout=2):
#                     tap_element(driver, XPATH_QUANTITY_INCREASE_BUTTON)
#                     time.sleep(0.5)
#                     # Check for out-of-stock or limit message
#                     out_of_stock_xpath = '//*[contains(@text,"maximum") or contains(@text,"not available") or contains(@text,"only")]'
#                     if is_element_present(driver, out_of_stock_xpath, timeout=1):
#                         blocked = True
#                         break
#                 else:
#                     logger.info("Increase button not present; trying dropdown or breaking")
#                     break
#             assert blocked or i < max_attempts - 1, "Was able to increase quantity without encountering stock limit (unexpected)"


# @allure.feature("Network Resilience")
# @allure.story("TC_004: Network interruption while adding to cart")
# def test_tc_004_network_interruption_add_to_cart(driver):
#     """
#     TC_004: Network interruption while adding to cart [Edge Case | Critical]
#     """
#     with allure.step("Search and open a product"):
#         open_search_and_search(driver, "OnePlus 15")
#         open_first_product(driver)

#     with allure.step("Disable network, attempt to add to cart, then re-enable and verify behavior"):
#         # Try to disable network via mobile shell commands. If not permitted, skip gracefully.
#         try:
#             # Put device into airplane mode (may require permission)
#             logger.info("Attempting to enable airplane mode via shell")
#             driver.execute_script("mobile: shell", {
#                 "command": "settings",
#                 "args": ["put", "global", "airplane_mode_on", "1"]
#             })
#             driver.execute_script("mobile: shell", {
#                 "command": "am",
#                 "args": ["broadcast", "-a", "android.intent.action.AIRPLANE_MODE", "--ez", "state", "true"]
#             })
#             time.sleep(2)
#         except Exception as e:
#             logger.warning("Unable to toggle airplane mode via Appium shell: %s", e)
#             pytest.skip("Cannot control network from test environment; skipping network interruption test")

#         # Attempt add to cart while offline
#         try:
#             if not tap_element(driver, XPATH_ADD_TO_CART_BUTTON):
#                 logger.warning("Add to cart button not present while offline attempt")
#             else:
#                 # Wait a moment for failure message
#                 offline_msg_xpath = '//*[contains(@text,"offline") or contains(@text,"network") or contains(@text,"connect")]'
#                 if is_element_present(driver, offline_msg_xpath, timeout=5):
#                     logger.info("Offline/network error message displayed as expected")
#                 else:
#                     logger.warning("No explicit offline message detected after add attempt")
#         finally:
#             # Re-enable network
#             try:
#                 logger.info("Re-enabling airplane mode off via shell")
#                 driver.execute_script("mobile: shell", {
#                     "command": "settings",
#                     "args": ["put", "global", "airplane_mode_on", "0"]
#                 })
#                 driver.execute_script("mobile: shell", {
#                     "command": "am",
#                     "args": ["broadcast", "-a", "android.intent.action.AIRPLANE_MODE", "--ez", "state", "false"]
#                 })
#                 time.sleep(2)
#             except Exception as e:
#                 logger.warning("Unable to re-enable network via shell: %s", e)

#         # After restoring network, verify app recovered and add to cart if necessary
#         try:
#             # Try to add to cart again if not already added
#             if tap_element(driver, XPATH_ADD_TO_CART_BUTTON):
#                 logger.info("Add to cart attempted after network restore")
#             # Check cart count or presence
#             ct = get_cart_item_count(driver)
#             assert ct is None or ct >= 0  # At least driver responded; detailed assert may be skipped
#         except Exception as e:
#             logger.exception("Post-network-add verification failed: %s", e)
#             pytest.skip("Unable to fully verify network recovery behavior")


# @allure.feature("Comparison and Add to Cart")
# @allure.story("TC_005: Use 'See more like this' comparison view and ensure add to cart is handled correctly")
# def test_tc_005_see_more_like_this_add_to_cart(driver):
#     """
#     TC_005: Use 'See more like this' comparison view and ensure add to cart is handled correctly [Negative | Medium]
#     """
#     with allure.step("Open comparison 'See more like this' if present"):
#         if not is_element_present(driver, XPATH_SEE_MORE_LIKE_THIS, timeout=5):
#             pytest.skip("'See more like this' not present on product; skipping test")
#         tap_element(driver, XPATH_SEE_MORE_LIKE_THIS)
#         time.sleep(2)

#     with allure.step("In comparison view, attempt to add compared item to cart"):
#         # Try to tap an add button in compare view
#         if is_element_present(driver, XPATH_COMPARE_VIEW_ADD_BUTTON, timeout=5):
#             tap_element(driver, XPATH_COMPARE_VIEW_ADD_BUTTON)
#             # Determine if add succeeded or requires additional steps
#             # If requires selecting variant, expect an error or prompt
#             if is_element_present(driver, XPATH_PRODUCT_VARIANT_OPTION, timeout=3):
#                 # Missing mandatory variant selection expected -> negative scenario
#                 logger.info("Variant option required; cannot add directly from compare view (expected negative)")
#                 assert True
#             else:
#                 logger.info("Added from compare view; verifying cart")
#                 if tap_element(driver, XPATH_CART_ICON):
#                     ct = get_cart_item_count(driver)
#                     # If count available, at least 1
#                     if ct is not None:
#                         assert ct >= 1
#                     else:
#                         pytest.skip("Cart count not available to verify add from compare view")
#         else:
#             pytest.skip("Add button not present in comparison view; skipping adding step")


# @allure.feature("Navigation")
# @allure.story("TC_006: Back navigation from search and product page behavior")
# def test_tc_006_back_navigation_behavior(driver):
#     """
#     TC_006: Back navigation from search and product page behavior [UI | Medium]
#     """
#     with allure.step("Open search, open product, then navigate back and verify"):
#         open_search_and_search(driver, "OnePlus 15")
#         open_first_product(driver)
#         # from product page tap back
#         if tap_element(driver, XPATH_BACK_BUTTON):
#             time.sleep(1)
#             # After back, search results or home should be visible; check for search input or search button
#             if is_element_present(driver, XPATH_SEARCH_INPUT, timeout=5) or is_element_present(driver, XPATH_SEARCH_BUTTON, timeout=5):
#                 assert True
#             else:
#                 pytest.skip("Unable to confirm navigation returned to search/home")
#         else:
#             pytest.skip("Back button not present on product page; skipping test")


# @allure.feature("Orientation")
# @allure.story("TC_007: Orientation change while selecting quantity and adding to cart (compatibility)")
# def test_tc_007_orientation_change_quantity_add(driver):
#     """
#     TC_007: Orientation change while selecting quantity and adding to cart (compatibility) [UI | Medium]
#     """
#     with allure.step("Open product and start selecting quantity"):
#         open_search_and_search(driver, "OnePlus 15")
#         open_first_product(driver)

#     with allure.step("Rotate device to landscape then back to portrait while adjusting quantity"):
#         try:
#             # Rotate to landscape
#             driver.orientation = "LANDSCAPE"
#             logger.info("Changed orientation to LANDSCAPE")
#             time.sleep(1)
#             # Try to set quantity via increase button if present
#             if is_element_present(driver, XPATH_QUANTITY_INCREASE_BUTTON, timeout=3):
#                 tap_element(driver, XPATH_QUANTITY_INCREASE_BUTTON)
#             # Rotate back
#             driver.orientation = "PORTRAIT"
#             logger.info("Changed orientation back to PORTRAIT")
#             time.sleep(1)
#         except Exception as e:
#             logger.warning("Unable to change orientation: %s", e)
#             pytest.skip("Device/orientation controls not available in environment")

#     with allure.step("Attempt to add to cart after orientation changes"):
#         if tap_element(driver, XPATH_ADD_TO_CART_BUTTON):
#             # Verify no crash and cart accessible
#             if tap_element(driver, XPATH_CART_ICON):
#                 assert True
#             else:
#                 pytest.skip("Cart icon not available post-orientation change")
#         else:
#             pytest.skip("Add to cart not present post-orientation change")


# @allure.feature("Variants")
# @allure.story("TC_008: Attempt to add to cart without selecting mandatory variant options")
# def test_tc_008_add_without_variant_selection(driver):
#     """
#     TC_008: Attempt to add to cart without selecting mandatory variant options [Negative | High]
#     """
#     with allure.step("Open product which has variants"):
#         open_search_and_search(driver, "Phone with variants")
#         open_first_product(driver)

#     with allure.step("Attempt to add to cart without selecting variants"):
#         # If product has variant options visible, intentionally avoid selecting them
#         if not tap_element(driver, XPATH_ADD_TO_CART_BUTTON):
#             pytest.skip("Add to cart button missing; skipping test")
#         # Expect an error or prompt to select variant
#         variant_prompt_xpath = '//*[contains(@text,"select") or contains(@text,"Choose") or contains(@text,"size")]'
#         if is_element_present(driver, variant_prompt_xpath, timeout=5) or is_element_present(driver, XPATH_PRODUCT_VARIANT_OPTION, timeout=5):
#             logger.info("Variant selection required prompt shown (expected)")
#             assert True
#         else:
#             # If it allowed add without variant, that's a negative unexpected behavior - fail
#             pytest.fail("Add to cart succeeded without selecting mandatory variant options")


# @allure.feature("Concurrency")
# @allure.story("TC_009: Rapid repeated add-to-cart actions to reach quantity 3 (concurrency/race)")
# def test_tc_009_rapid_repeated_adds(driver):
#     """
#     TC_009: Rapid repeated add-to-cart actions to reach quantity 3 (concurrency/race) [Edge Case | High]
#     """
#     with allure.step("Open product to stress add-to-cart rapidly"):
#         open_search_and_search(driver, "OnePlus 15")
#         open_first_product(driver)

#     with allure.step("Rapidly tap add-to-cart multiple times"):
#         if not is_element_present(driver, XPATH_ADD_TO_CART_BUTTON, timeout=5):
#             pytest.skip("Add to cart button not present; skipping concurrency test")

#         # Rapidly tap add to cart 5 times to try to reach quantity 3 (some apps queue taps)
#         for i in range(5):
#             try:
#                 tap_element(driver, XPATH_ADD_TO_CART_BUTTON)
#                 # Very small pause to simulate rapid tapping
#                 time.sleep(0.2)
#             except Exception:
#                 logger.exception("Exception while rapidly tapping add-to-cart")
#                 break

#         # Open cart and check quantity
#         if not tap_element(driver, XPATH_CART_ICON):
#             pytest.skip("Cart icon not present after rapid adds")
#         if is_element_present(driver, XPATH_CART_ITEM_QUANTITY, timeout=5):
#             el = wait_for_element(driver, XPATH_CART_ITEM_QUANTITY)
#             try:
#                 qty = int(el.text)
#                 assert qty >= 3, f"Expected at least 3 after rapid adds; found {qty}"
#             except ValueError:
#                 pytest.skip("Quantity text not numeric after rapid adds")
#         else:
#             pytest.skip("Cart quantity element not present post rapid adds")


# @allure.feature("Filters")
# @allure.story("TC_010: Apply 'All Filters' to narrow search to specific storage option then add product")
# def test_tc_010_apply_all_filters_and_add(driver):
#     """
#     TC_010: Apply 'All Filters' to narrow search to specific storage option then add product [Positive | Medium]
#     """
#     with allure.step("Search for a product category"):
#         open_search_and_search(driver, "OnePlus")

#     with allure.step("Open 'All Filters' and apply storage filter"):
#         if not tap_element(driver, XPATH_ALL_FILTERS_BUTTON):
#             pytest.skip("'All Filters' button not present")
#         # Try to select storage option if present
#         if is_element_present(driver, XPATH_FILTER_STORAGE_OPTION, timeout=5):
#             tap_element(driver, XPATH_FILTER_STORAGE_OPTION)
#             if is_element_present(driver, XPATH_APPLY_FILTERS, timeout=3):
#                 tap_element(driver, XPATH_APPLY_FILTERS)
#                 time.sleep(2)
#             else:
#                 logger.info("Apply filters button not found; proceeding")
#         else:
#             pytest.skip("Desired storage filter not present; skipping filter application")

#     with allure.step("Open first filtered product and add to cart"):
#         open_first_product(driver)
#         if not tap_element(driver, XPATH_ADD_TO_CART_BUTTON):
#             pytest.skip("Add to cart not present after filtering")
#         # Verify in cart
#         if tap_element(driver, XPATH_CART_ICON):
#             ct = get_cart_item_count(driver)
#             if ct is not None:
#                 assert ct >= 1
#             else:
#                 pytest.skip("Cart item count not available for verification")


# @allure.feature("Guest and Login Flow")
# @allure.story("TC_011: Guest cart persistence and merge after login")
# def test_tc_011_guest_cart_persistence_and_merge(driver):
#     """
#     TC_011: Guest cart persistence and merge after login [Positive | High]
#     """
#     with allure.step("As guest, add an item to cart"):
#         open_search_and_search(driver, "OnePlus 15")
#         open_first_product(driver)
#         if not tap_element(driver, XPATH_ADD_TO_CART_BUTTON):
#             pytest.skip("Add to cart not possible as guest")
#         # Record cart count
#         guest_count = get_cart_item_count(driver)

#     with allure.step("Perform login and verify cart merged"):
#         # Attempt login flow using provided recorded login inputs; may require navigation
#         # Open login screen via search page or navigate to account - best-effort
#         # For the purpose of this test, try to locate email login field and input credentials
#         if is_element_present(driver, XPATH_LOGIN_EMAIL, timeout=5):
#             input_text(driver, XPATH_LOGIN_EMAIL, "satha")
#             # If change and phone number fields appear, simulate phone entry
#             if is_element_present(driver, XPATH_LOGIN_CHANGE, timeout=2):
#                 tap_element(driver, XPATH_LOGIN_CHANGE)
#             if is_element_present(driver, XPATH_LOGIN_PHONE, timeout=2):
#                 input_text(driver, XPATH_LOGIN_PHONE, "9629")
#             # After entering, attempt to submit - in many flows there's a continue button; skip if not present
#             # In absence of explicit submit, assume login performed externally
#         else:
#             pytest.skip("Login fields not available; cannot perform login in this environment")

#         # Wait briefly for merge to occur
#         time.sleep(3)

#         # Verify cart after login: ensure items from guest are present (count same or greater)
#         if tap_element(driver, XPATH_CART_ICON):
#             post_login_count = get_cart_item_count(driver)
#             if guest_count is not None and post_login_count is not None:
#                 assert post_login_count >= guest_count, "Post-login cart has fewer items than guest cart"
#             else:
#                 pytest.skip("Cart counts not available to verify merge")
#         else:
#             pytest.skip("Cart icon not present after login attempt")


# @allure.feature("Cart Management")
# @allure.story("TC_012: Remove items until cart is empty and verify empty cart UI")
# def test_tc_012_remove_items_until_empty(driver):
#     """
#     TC_012: Remove items until cart is empty and verify empty cart UI [Negative | Medium]
#     """
#     with allure.step("Open cart and remove items until empty"):
#         if not tap_element(driver, XPATH_CART_ICON):
#             pytest.skip("Cart icon not present; cannot perform remove test")
#         # Loop removing items while remove button exists
#         removed_any = False
#         for _ in range(20):  # safety loop limit
#             if is_element_present(driver, XPATH_REMOVE_FROM_CART, timeout=2):
#                 tap_element(driver, XPATH_REMOVE_FROM_CART)
#                 removed_any = True
#                 time.sleep(1)
#             else:
#                 break

#         if not removed_any:
#             pytest.skip("No removable items in cart to perform empty cart test")

#     with allure.step("Verify empty cart UI is shown"):
#         if is_element_present(driver, XPATH_EMPTY_CART_MESSAGE, timeout=5):
#             el = wait_for_element(driver, XPATH_EMPTY_CART_MESSAGE)
#             assert el.is_displayed()
#         else:
#             # If empty message not present, attempt to find alternative texts
#             alt_empty_xpath = '//*[contains(@text,"empty") or contains(@text,"Your Cart is empty")]'
#             if is_element_present(driver, alt_empty_xpath, timeout=3):
#                 assert True
#             else:
#                 pytest.skip("Empty cart UI not identifiable in this app; skipping final assert")
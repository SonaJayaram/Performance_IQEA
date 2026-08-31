import pytest
import allure
import time
import os
from allure_commons.types import AttachmentType
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://www.saucedemo.com/"
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def attach_screenshot(driver, name: str):
    try:
        allure.attach(
            driver.get_screenshot_as_png(),
            name=name,
            attachment_type=AttachmentType.PNG
        )
    except Exception:
        pass


def safe_click(driver, wait, locator, step_label):
    attempt = 0
    last_err = None
    while attempt < 2:
        try:
            el = wait.until(EC.element_to_be_clickable(locator))
            el.click()
            break
        except Exception as e:
            last_err = e
            attach_screenshot(driver, f"retry_{step_label}_attempt_{attempt}")
            time.sleep(0.5)
            attempt += 1
    if attempt == 2:
        attach_screenshot(driver, f"failed_{step_label}")
        raise RuntimeError(f"{step_label} failed after 2 attempts: {last_err}")


def safe_type(driver, wait, locator, value, step_label):
    attempt = 0
    last_err = None
    while attempt < 2:
        try:
            el = wait.until(EC.presence_of_element_located(locator))
            el.clear()
            el.send_keys(value)
            break
        except Exception as e:
            last_err = e
            attach_screenshot(driver, f"retry_{step_label}_attempt_{attempt}")
            time.sleep(0.5)
            attempt += 1
    if attempt == 2:
        attach_screenshot(driver, f"failed_{step_label}")
        raise RuntimeError(f"{step_label} failed after 2 attempts: {last_err}")


@pytest.fixture
def setup():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(0)
    yield driver
    driver.quit()


def test_recorded_flow(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)

    driver.get(BASE_URL)
    attach_screenshot(driver, "page_loaded")

    with allure.step("Step 1: CLICK username field"):
        safe_click(driver, wait, (By.ID, "user-name"), "step_1_click_username")
        attach_screenshot(driver, "step_1_done")

    with allure.step("Step 2: TYPE 'standard_user' into username"):
        safe_type(driver, wait, (By.ID, "user-name"), "standard_user", "step_2_type_username")
        attach_screenshot(driver, "step_2_done")

    with allure.step("Step 3: TYPE 'secret_sauce' into password"):
        safe_type(driver, wait, (By.ID, "password"), "secret_sauce", "step_3_type_password")
        attach_screenshot(driver, "step_3_done")

    with allure.step("Step 4: CLICK Login button"):
        safe_click(driver, wait, (By.ID, "login-button"), "step_4_click_login")
        wait.until(EC.url_contains("/inventory.html"))
        attach_screenshot(driver, "step_4_logged_in")

    with allure.step("Step 5: ADD Sauce Labs Backpack to cart"):
        safe_click(driver, wait, (By.ID, "add-to-cart-sauce-labs-backpack"), "step_5_add_backpack")
        attach_screenshot(driver, "step_5_done")

    with allure.step("Step 6: ADD Sauce Labs Bike Light to cart"):
        safe_click(driver, wait, (By.ID, "add-to-cart-sauce-labs-bike-light"), "step_6_add_bikelight")
        attach_screenshot(driver, "step_6_done")

    with allure.step("Step 7: CLICK shopping cart"):
        safe_click(driver, wait, (By.CLASS_NAME, "shopping_cart_link"), "step_7_open_cart")
        wait.until(EC.url_contains("/cart.html"))
        attach_screenshot(driver, "step_7_cart_open")

    with allure.step("Step 8: REMOVE Sauce Labs Backpack from cart"):
        safe_click(driver, wait, (By.ID, "remove-sauce-labs-backpack"), "step_8_remove_backpack")
        attach_screenshot(driver, "step_8_done")

    with allure.step("Step 9: CLICK Checkout"):
        safe_click(driver, wait, (By.ID, "checkout"), "step_9_checkout")
        wait.until(EC.url_contains("/checkout-step-one.html"))
        attach_screenshot(driver, "step_9_checkout_step1")

    with allure.step("Step 10: TYPE 'test' into First Name"):
        safe_type(driver, wait, (By.ID, "first-name"), "test", "step_10_firstname")
        attach_screenshot(driver, "step_10_done")

    with allure.step("Step 11: TYPE 'test' into Last Name"):
        safe_type(driver, wait, (By.ID, "last-name"), "test", "step_11_lastname")
        attach_screenshot(driver, "step_11_done")

    with allure.step("Step 12: TYPE '8765' into Postal Code"):
        safe_type(driver, wait, (By.ID, "postal-code"), "8765", "step_12_postalcode")
        attach_screenshot(driver, "step_12_done")

    with allure.step("Step 13: CLICK Continue"):
        safe_click(driver, wait, (By.ID, "continue"), "step_13_continue")
        wait.until(EC.url_contains("/checkout-step-two.html"))
        attach_screenshot(driver, "step_13_checkout_step2")

    with allure.step("Step 14: CLICK Finish"):
        safe_click(driver, wait, (By.ID, "finish"), "step_14_finish")
        wait.until(EC.url_contains("/checkout-complete.html"))
        attach_screenshot(driver, "step_14_order_complete")

    with allure.step("Step 15: CLICK Back to Products"):
        safe_click(driver, wait, (By.ID, "back-to-products"), "step_15_back_to_products")
        wait.until(EC.url_contains("/inventory.html"))
        attach_screenshot(driver, "step_15_back_inventory")

    with allure.step("Step 16: CLICK Burger Menu"):
        safe_click(driver, wait, (By.ID, "react-burger-menu-btn"), "step_16_burger_menu")
        attach_screenshot(driver, "step_16_menu_open")

    with allure.step("Step 17: CLICK All Items sidebar link"):
        safe_click(driver, wait, (By.ID, "inventory_sidebar_link"), "step_17_all_items")
        wait.until(EC.url_contains("/inventory.html"))
        attach_screenshot(driver, "step_17_all_items")

    with allure.step("Step 18: CLICK Logout sidebar link"):
        safe_click(driver, wait, (By.ID, "react-burger-menu-btn"), "step_18_reopen_menu")
        safe_click(driver, wait, (By.ID, "logout_sidebar_link"), "step_18_logout")
        wait.until(EC.url_contains(BASE_URL))
        attach_screenshot(driver, "step_18_logged_out")

    el = wait.until(EC.visibility_of_element_located((By.ID, "login-button")))
    assert el.is_displayed(), "Expected: login button visible after logout"
    attach_screenshot(driver, "assertion_passed")


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))

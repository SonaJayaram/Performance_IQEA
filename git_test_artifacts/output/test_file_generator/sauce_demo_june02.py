import pytest
import allure
import time
import os
from allure_commons.types import AttachmentType
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
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

@pytest.fixture(scope="function")
def setup():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(0)
    yield driver
    driver.quit()

@allure.title("Full purchase flow: login, add items, checkout, logout")
@pytest.mark.regression
def test_full_purchase_flow(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)

    driver.get(BASE_URL)
    attach_screenshot(driver, "start")

    with allure.step("Login with valid credentials"):
        el = wait.until(EC.presence_of_element_located((By.ID, "user-name")))
        el.clear()
        el.send_keys("standard_user")
        el = wait.until(EC.presence_of_element_located((By.ID, "password")))
        el.clear()
        el.send_keys("secret_sauce")
        el = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        el.click()
        wait.until(EC.url_contains("/inventory.html"))
        attach_screenshot(driver, "logged_in")

    with allure.step("Add items to cart (first interaction on inventory page with retry)"):
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-backpack")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_add_backpack_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_add_backpack")
            raise RuntimeError(f"add-to-cart-sauce-labs-backpack failed: {last_err}")
        # second add (stable same page)
        el = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-bike-light")))
        el.click()
        attach_screenshot(driver, "items_added")

    with allure.step("Open cart and navigate to cart page"):
        el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.shopping_cart_link")))
        el.click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cart_list")))
        attach_screenshot(driver, "cart_open")

    with allure.step("Remove one item from cart (first interaction on cart page with retry)"):
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "remove-sauce-labs-bike-light")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_remove_bike_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_remove_bike")
            raise RuntimeError(f"remove-sauce-labs-bike-light failed: {last_err}")
        attach_screenshot(driver, "item_removed")

    with allure.step("Proceed to checkout - fill info and continue"):
        el = wait.until(EC.element_to_be_clickable((By.ID, "checkout")))
        el.click()
        wait.until(EC.url_contains("/checkout-step-one.html"))
        attach_screenshot(driver, "checkout_info_page")

        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el = wait.until(EC.presence_of_element_located((By.ID, "first-name")))
                el.clear()
                el.send_keys("test")
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_firstname_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_firstname")
            raise RuntimeError(f"first-name input failed: {last_err}")

        el = wait.until(EC.presence_of_element_located((By.ID, "last-name")))
        el.clear()
        el.send_keys("test")
        el = wait.until(EC.presence_of_element_located((By.ID, "postal-code")))
        el.clear()
        el.send_keys("67686")
        el = wait.until(EC.element_to_be_clickable((By.ID, "continue")))
        el.click()
        wait.until(EC.url_contains("/checkout-step-two.html"))
        attach_screenshot(driver, "checkout_overview")

    with allure.step("Finish checkout and return to products"):
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "finish")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_finish_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_finish")
            raise RuntimeError(f"finish failed: {last_err}")
        wait.until(EC.url_contains("/checkout-complete.html"))
        attach_screenshot(driver, "checkout_complete")

        el = wait.until(EC.element_to_be_clickable((By.ID, "back-to-products")))
        el.click()
        wait.until(EC.url_contains("/inventory.html"))
        attach_screenshot(driver, "back_to_products")

    with allure.step("Logout via burger menu"):
        el = wait.until(EC.element_to_be_clickable((By.ID, "react-burger-menu-btn")))
        el.click()
        wait.until(EC.visibility_of_element_located((By.ID, "logout_sidebar_link")))
        el = wait.until(EC.element_to_be_clickable((By.ID, "logout_sidebar_link")))
        el.click()
        wait.until(EC.visibility_of_element_located((By.ID, "login-button")))
        attach_screenshot(driver, "logged_out")

    el = wait.until(EC.visibility_of_element_located((By.ID, "login-button")))
    assert el.is_displayed(), "Expected: login button visible after logout"
    attach_screenshot(driver, "assertion_passed")

@allure.title("Login negative: invalid credentials should not allow access")
@pytest.mark.negative
def test_login_negative_invalid_credentials(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)

    driver.get(BASE_URL)
    attach_screenshot(driver, "start")

    with allure.step("Attempt login with invalid credentials"):
        el = wait.until(EC.presence_of_element_located((By.ID, "user-name")))
        el.clear()
        el.send_keys("invalid_user")
        el = wait.until(EC.presence_of_element_located((By.ID, "password")))
        el.clear()
        el.send_keys("bad_pass")
        el = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        el.click()
        time.sleep(1)  # allow potential client-side validation to show
        attach_screenshot(driver, "after_invalid_login")

    assert "/inventory.html" not in driver.current_url
    attach_screenshot(driver, "assertion_passed")

@allure.title("Checkout form boundary: submitting checkout with empty fields should stay on page")
@pytest.mark.boundary
def test_checkout_form_boundary_empty_fields(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)

    driver.get(BASE_URL)
    attach_screenshot(driver, "start")

    with allure.step("Login with valid credentials"):
        el = wait.until(EC.presence_of_element_located((By.ID, "user-name")))
        el.clear()
        el.send_keys("standard_user")
        el = wait.until(EC.presence_of_element_located((By.ID, "password")))
        el.clear()
        el.send_keys("secret_sauce")
        el = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        el.click()
        wait.until(EC.url_contains("/inventory.html"))
        attach_screenshot(driver, "logged_in")

    with allure.step("Navigate to cart with an item added (first interaction on inventory page with retry)"):
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-backpack")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_add_backpack_boundary_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_add_backpack_boundary")
            raise RuntimeError(f"add-to-cart-sauce-labs-backpack failed: {last_err}")

        el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.shopping_cart_link")))
        el.click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cart_list")))
        attach_screenshot(driver, "cart_open")

    with allure.step("Proceed to checkout and attempt to continue with empty form (first interaction on cart page with retry for checkout click)"):
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "checkout")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_checkout_click_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_checkout_click")
            raise RuntimeError(f"checkout click failed: {last_err}")

        wait.until(EC.url_contains("/checkout-step-one.html"))
        attach_screenshot(driver, "checkout_info_page")

        with allure.step("Click continue without filling required fields"):
            el = wait.until(EC.element_to_be_clickable((By.ID, "continue")))
            el.click()
            time.sleep(1)
            attach_screenshot(driver, "continue_clicked_empty")

    assert "/checkout-step-one.html" in driver.current_url
    attach_screenshot(driver, "assertion_passed")

@allure.title("Add and remove items in cart: add two, remove one, verify remaining count")
@pytest.mark.smoke
def test_add_and_remove_items_cart(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)

    driver.get(BASE_URL)
    attach_screenshot(driver, "start")

    with allure.step("Login"):
        el = wait.until(EC.presence_of_element_located((By.ID, "user-name")))
        el.clear()
        el.send_keys("standard_user")
        el = wait.until(EC.presence_of_element_located((By.ID, "password")))
        el.clear()
        el.send_keys("secret_sauce")
        el = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        el.click()
        wait.until(EC.url_contains("/inventory.html"))
        attach_screenshot(driver, "logged_in")

    with allure.step("Add two items (first interaction on inventory page with retry)"):
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-backpack")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_add_backpack_cart_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_add_backpack_cart")
            raise RuntimeError(f"add-to-cart-sauce-labs-backpack failed: {last_err}")

        el = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-bike-light")))
        el.click()
        attach_screenshot(driver, "two_items_added")

    with allure.step("Open cart and remove one item (first interaction on cart page with retry)"):
        el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.shopping_cart_link")))
        el.click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cart_list")))
        attach_screenshot(driver, "cart_open")

        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "remove-sauce-labs-bike-light")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_remove_bike_cart_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_remove_bike_cart")
            raise RuntimeError(f"remove-sauce-labs-bike-light failed: {last_err}")

        attach_screenshot(driver, "one_item_removed")

    with allure.step("Verify only one item remains in cart"):
        items = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "cart_item")))
        attach_screenshot(driver, "cart_items_counted")
    assert len(items) == 1
    attach_screenshot(driver, "assertion_passed")

@allure.title("Logout flow: login then logout via sidebar menu")
@pytest.mark.regression
def test_logout_flow(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)

    driver.get(BASE_URL)
    attach_screenshot(driver, "start")

    with allure.step("Login"):
        el = wait.until(EC.presence_of_element_located((By.ID, "user-name")))
        el.clear()
        el.send_keys("standard_user")
        el = wait.until(EC.presence_of_element_located((By.ID, "password")))
        el.clear()
        el.send_keys("secret_sauce")
        el = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        el.click()
        wait.until(EC.url_contains("/inventory.html"))
        attach_screenshot(driver, "logged_in")

    with allure.step("Open sidebar and click logout"):
        el = wait.until(EC.element_to_be_clickable((By.ID, "react-burger-menu-btn")))
        el.click()
        wait.until(EC.visibility_of_element_located((By.ID, "logout_sidebar_link")))
        el = wait.until(EC.element_to_be_clickable((By.ID, "logout_sidebar_link")))
        el.click()
        wait.until(EC.visibility_of_element_located((By.ID, "login-button")))
        attach_screenshot(driver, "logged_out")

    el = wait.until(EC.visibility_of_element_located((By.ID, "login-button")))
    assert el.is_displayed(), "Expected: login button visible after logout"
    attach_screenshot(driver, "assertion_passed")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
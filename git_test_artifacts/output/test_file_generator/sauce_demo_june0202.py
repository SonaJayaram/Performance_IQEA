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

@allure.title("Happy path: login, add items, checkout and logout")
@pytest.mark.smoke
def test_happy_path_checkout(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)
    attach_screenshot(driver, "start")

    with allure.step("Login with standard_user"):
        el_user = wait.until(EC.presence_of_element_located((By.ID, "user-name")))
        el_user.clear()
        el_user.send_keys("standard_user")
        el_pw = wait.until(EC.presence_of_element_located((By.ID, "password")))
        el_pw.clear()
        el_pw.send_keys("secret_sauce")
        btn_login = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        btn_login.click()
        # wait for inventory page to load
        wait.until(EC.presence_of_element_located((By.ID, "inventory_container")))
        attach_screenshot(driver, "logged_in")

    with allure.step("Add three items to cart (apply retry to first add after login)"):
        # Retry wrapper for first interaction after page change
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el_add_backpack = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-backpack")))
                el_add_backpack.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_add_backpack_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_add_backpack")
            raise RuntimeError(f"add_backpack failed: {last_err}")

        # other adds (no retry)
        el_add_bikelight = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-bike-light")))
        el_add_bikelight.click()
        el_add_bolt = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-bolt-t-shirt")))
        el_add_bolt.click()
        attach_screenshot(driver, "items_added")

    with allure.step("Open cart"):
        el_cart = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.shopping_cart_link")))
        el_cart.click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cart_list")))
        attach_screenshot(driver, "cart_open")

    with allure.step("Remove bike light from cart (retry on first interaction after nav)"):
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el_remove = wait.until(EC.element_to_be_clickable((By.ID, "remove-sauce-labs-bike-light")))
                el_remove.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_remove_bikelight_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_remove_bikelight")
            raise RuntimeError(f"remove_bikelight failed: {last_err}")
        attach_screenshot(driver, "item_removed")

    with allure.step("Continue shopping and re-add bike light (retry on first interaction after nav)"):
        el_continue = wait.until(EC.element_to_be_clickable((By.ID, "continue-shopping")))
        el_continue.click()
        wait.until(EC.presence_of_element_located((By.ID, "inventory_container")))
        attach_screenshot(driver, "inventory_returned")

        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el_add_bikelight_again = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-bike-light")))
                el_add_bikelight_again.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_add_bikelight_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_add_bikelight")
            raise RuntimeError(f"add_bikelight failed: {last_err}")
        attach_screenshot(driver, "bikelight_readded")

    with allure.step("Go to cart and proceed to checkout (retry on first interaction after nav)"):
        el_cart_2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.shopping_cart_link")))
        el_cart_2.click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cart_list")))
        attach_screenshot(driver, "cart_open_again")

        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el_checkout = wait.until(EC.element_to_be_clickable((By.ID, "checkout")))
                el_checkout.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_checkout_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_checkout")
            raise RuntimeError(f"checkout failed: {last_err}")
        wait.until(EC.presence_of_element_located((By.ID, "checkout_info_container")))
        attach_screenshot(driver, "checkout_step_one")

    with allure.step("Fill checkout info and finish (apply retry to first interaction after nav)"):
        # First interaction after nav: ensure first name field present (retry wrapper)
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el_first = wait.until(EC.presence_of_element_located((By.ID, "first-name")))
                el_first.clear()
                el_first.send_keys("test")
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_firstname_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_firstname")
            raise RuntimeError(f"first-name interaction failed: {last_err}")

        el_last = wait.until(EC.presence_of_element_located((By.ID, "last-name")))
        el_last.clear()
        el_last.send_keys("test")
        el_postal = wait.until(EC.presence_of_element_located((By.ID, "postal-code")))
        el_postal.clear()
        el_postal.send_keys("7865756")
        btn_continue = wait.until(EC.element_to_be_clickable((By.ID, "continue")))
        btn_continue.click()
        wait.until(EC.presence_of_element_located((By.ID, "finish")))
        attach_screenshot(driver, "checkout_step_two")

        # Finish (retry as first interaction after nav to checkout-step-two)
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el_finish = wait.until(EC.element_to_be_clickable((By.ID, "finish")))
                el_finish.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_finish_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_finish")
            raise RuntimeError(f"finish failed: {last_err}")
        wait.until(EC.presence_of_element_located((By.ID, "checkout_complete_container")))
        attach_screenshot(driver, "checkout_complete")

    with allure.step("Back to products and logout (apply retry on first interaction after nav)"):
        el_back = wait.until(EC.element_to_be_clickable((By.ID, "back-to-products")))
        el_back.click()
        wait.until(EC.presence_of_element_located((By.ID, "inventory_container")))
        attach_screenshot(driver, "back_to_products")

        # First interaction after page change: open burger menu (retry)
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                btn_menu = wait.until(EC.presence_of_element_located((By.ID, "react-burger-menu-btn")))
                driver.execute_script("arguments[0].click();", btn_menu)
                time.sleep(0.5)
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_menu_open_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_menu_open")
            raise RuntimeError(f"menu open failed: {last_err}")

        el_logout = wait.until(EC.element_to_be_clickable((By.ID, "logout_sidebar_link")))
        el_logout.click()
        wait.until(EC.visibility_of_element_located((By.ID, "login-button")))
        attach_screenshot(driver, "logged_out")

    # Final assertion: ensure we are back on login page (single assertion)
    login_btn = wait.until(EC.visibility_of_element_located((By.ID, "login-button")))
    assert login_btn.is_displayed()
    attach_screenshot(driver, "assertion_passed")

@allure.title("Negative: invalid login should not allow access")
@pytest.mark.negative
def test_invalid_login(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)
    attach_screenshot(driver, "start")

    with allure.step("Attempt login with invalid credentials"):
        el_user = wait.until(EC.presence_of_element_located((By.ID, "user-name")))
        el_user.clear()
        el_user.send_keys("invalid_user")
        el_pw = wait.until(EC.presence_of_element_located((By.ID, "password")))
        el_pw.clear()
        el_pw.send_keys("wrong_password")
        btn_login = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        btn_login.click()
        # Stay on login page; wait for login button to remain visible
        wait.until(EC.visibility_of_element_located((By.ID, "login-button")))
        attach_screenshot(driver, "login_failed_visible")

    # Single assertion: login button still visible
    login_btn = wait.until(EC.visibility_of_element_located((By.ID, "login-button")))
    assert login_btn.is_displayed()
    attach_screenshot(driver, "assertion_passed")

@allure.title("Boundary: checkout with empty information should not proceed")
@pytest.mark.boundary
def test_checkout_empty_info(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)
    attach_screenshot(driver, "start")

    with allure.step("Login with standard_user"):
        el_user = wait.until(EC.presence_of_element_located((By.ID, "user-name")))
        el_user.clear()
        el_user.send_keys("standard_user")
        el_pw = wait.until(EC.presence_of_element_located((By.ID, "password")))
        el_pw.clear()
        el_pw.send_keys("secret_sauce")
        btn_login = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        btn_login.click()
        wait.until(EC.presence_of_element_located((By.ID, "inventory_container")))
        attach_screenshot(driver, "logged_in")

    with allure.step("Add one item to cart (retry on first post-login interaction)"):
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el_add = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-backpack")))
                el_add.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_add_item_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_add_item")
            raise RuntimeError(f"add item failed: {last_err}")
        attach_screenshot(driver, "item_added")

    with allure.step("Go to cart and proceed to checkout"):
        el_cart = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.shopping_cart_link")))
        el_cart.click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cart_list")))
        attach_screenshot(driver, "cart_open")
        el_checkout = wait.until(EC.element_to_be_clickable((By.ID, "checkout")))
        el_checkout.click()
        # now on checkout-step-one
        wait.until(EC.presence_of_element_located((By.ID, "checkout_info_container")))
        attach_screenshot(driver, "checkout_step_one")

    with allure.step("Try to continue without filling any info (apply retry to first interaction after nav)"):
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                # ensure first name field is present
                wait.until(EC.presence_of_element_located((By.ID, "first-name")))
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_wait_firstname_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_wait_firstname")
            raise RuntimeError(f"wait for first-name failed: {last_err}")

        btn_continue = wait.until(EC.element_to_be_clickable((By.ID, "continue")))
        btn_continue.click()
        # Expect to remain on checkout-step-one (URL contains checkout-step-one)
        wait.until(EC.url_contains("checkout-step-one"))
        attach_screenshot(driver, "still_on_checkout_step_one")

    # Single assertion: still on checkout-step-one
    assert "checkout-step-one" in driver.current_url
    attach_screenshot(driver, "assertion_passed")

@allure.title("Regression: cart operations - add multiple items and remove one")
@pytest.mark.regression
def test_cart_operations(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)
    attach_screenshot(driver, "start")

    with allure.step("Login with standard_user"):
        el_user = wait.until(EC.presence_of_element_located((By.ID, "user-name")))
        el_user.clear()
        el_user.send_keys("standard_user")
        el_pw = wait.until(EC.presence_of_element_located((By.ID, "password")))
        el_pw.clear()
        el_pw.send_keys("secret_sauce")
        btn_login = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        btn_login.click()
        wait.until(EC.presence_of_element_located((By.ID, "inventory_container")))
        attach_screenshot(driver, "logged_in")

    with allure.step("Add three items to cart (retry on first post-login interaction)"):
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el_add1 = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-backpack")))
                el_add1.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_add1_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_add1")
            raise RuntimeError(f"add1 failed: {last_err}")

        el_add2 = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-bike-light")))
        el_add2.click()
        el_add3 = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-bolt-t-shirt")))
        el_add3.click()
        attach_screenshot(driver, "items_added")

    with allure.step("Open cart and remove one item (retry on first interaction after nav)"):
        el_cart = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.shopping_cart_link")))
        el_cart.click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cart_list")))
        attach_screenshot(driver, "cart_open")

        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el_remove = wait.until(EC.element_to_be_clickable((By.ID, "remove-sauce-labs-bike-light")))
                el_remove.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_remove_cart_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_remove_cart")
            raise RuntimeError(f"remove in cart failed: {last_err}")
        attach_screenshot(driver, "item_removed")

    with allure.step("Verify cart has two items"):
        items = driver.find_elements(By.CLASS_NAME, "cart_item")
        # Single assertion: two items remain
        assert len(items) == 2
        attach_screenshot(driver, "assertion_passed")

@allure.title("Regression: logout from inventory via sidebar menu")
@pytest.mark.regression
def test_logout_flow(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)
    attach_screenshot(driver, "start")

    with allure.step("Login with standard_user"):
        el_user = wait.until(EC.presence_of_element_located((By.ID, "user-name")))
        el_user.clear()
        el_user.send_keys("standard_user")
        el_pw = wait.until(EC.presence_of_element_located((By.ID, "password")))
        el_pw.clear()
        el_pw.send_keys("secret_sauce")
        btn_login = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        btn_login.click()
        wait.until(EC.presence_of_element_located((By.ID, "inventory_container")))
        attach_screenshot(driver, "logged_in")

    with allure.step("Open sidebar menu (retry on first interaction after nav)"):
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                btn_menu = wait.until(EC.presence_of_element_located((By.ID, "react-burger-menu-btn")))
                driver.execute_script("arguments[0].click();", btn_menu)
                time.sleep(0.5)
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_menu_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_menu")
            raise RuntimeError(f"menu open failed: {last_err}")

        el_logout = wait.until(EC.element_to_be_clickable((By.ID, "logout_sidebar_link")))
        el_logout.click()
        wait.until(EC.visibility_of_element_located((By.ID, "login-button")))
        attach_screenshot(driver, "logged_out")

    # Single assertion: login button visible
    login_btn = wait.until(EC.visibility_of_element_located((By.ID, "login-button")))
    assert login_btn.is_displayed()
    attach_screenshot(driver, "assertion_passed")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
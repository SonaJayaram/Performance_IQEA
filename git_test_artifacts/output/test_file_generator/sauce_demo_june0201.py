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

def _retry_interaction(driver, action_fn, label: str):
    attempt, last_err = 0, None
    while attempt < 2:
        try:
            action_fn()
            break
        except Exception as e:
            last_err = e
            attach_screenshot(driver, f"retry_{label}_{attempt}")
            time.sleep(0.5)
            attempt += 1
    if attempt == 2:
        attach_screenshot(driver, f"failed_{label}")
        raise RuntimeError(f"{label} failed: {last_err}")

@pytest.fixture(scope="function")
def setup():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(0)
    yield driver
    driver.quit()

@allure.title("Complete purchase flow: login, add/remove items, checkout and logout")
@pytest.mark.smoke
def test_complete_purchase_flow(setup):
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
        btn = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        btn.click()
        # wait for inventory page to load
        wait.until(EC.url_contains("/inventory.html"))
        attach_screenshot(driver, "logged_in")

    with allure.step("Add first item to cart (first interaction after page change - retry applied)"):
        # retry wrapper applied as this is first interaction after navigation
        def action():
            el = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-backpack")))
            el.click()
        _retry_interaction(driver, action, "add_backpack")
        attach_screenshot(driver, "added_backpack")

    with allure.step("Add second item to cart"):
        el = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-bike-light")))
        el.click()
        attach_screenshot(driver, "added_bike_light")

    with allure.step("Open cart"):
        el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.shopping_cart_link")))
        el.click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cart_list")))
        attach_screenshot(driver, "cart_open")

    with allure.step("Remove one item from cart (first interaction after page change - retry applied)"):
        def action():
            el = wait.until(EC.element_to_be_clickable((By.ID, "remove-sauce-labs-bike-light")))
            el.click()
        _retry_interaction(driver, action, "remove_bike_light")
        attach_screenshot(driver, "removed_bike_light")

    with allure.step("Continue shopping to inventory"):
        el = wait.until(EC.element_to_be_clickable((By.ID, "continue-shopping")))
        el.click()
        wait.until(EC.url_contains("/inventory.html"))
        attach_screenshot(driver, "back_to_inventory")

    with allure.step("Add another item (first interaction after page change - retry applied)"):
        def action():
            el = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-bolt-t-shirt")))
            el.click()
        _retry_interaction(driver, action, "add_tshirt")
        attach_screenshot(driver, "added_tshirt")

    with allure.step("Open cart to checkout"):
        el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.shopping_cart_link")))
        el.click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cart_list")))
        attach_screenshot(driver, "cart_open_2")

    with allure.step("Checkout (first interaction after page change - retry applied)"):
        def action():
            el = wait.until(EC.element_to_be_clickable((By.ID, "checkout")))
            el.click()
        _retry_interaction(driver, action, "checkout_click")
        wait.until(EC.url_contains("/checkout-step-one.html"))
        attach_screenshot(driver, "checkout_step_one")

    with allure.step("Fill checkout information and continue"):
        el = wait.until(EC.presence_of_element_located((By.ID, "first-name")))
        el.clear()
        el.send_keys("test")
        el = wait.until(EC.presence_of_element_located((By.ID, "last-name")))
        el.clear()
        el.send_keys("test")
        el = wait.until(EC.presence_of_element_located((By.ID, "postal-code")))
        el.clear()
        el.send_keys("234567")
        btn = wait.until(EC.element_to_be_clickable((By.ID, "continue")))
        btn.click()
        wait.until(EC.url_contains("/checkout-step-two.html"))
        attach_screenshot(driver, "checkout_step_two")

    with allure.step("Finish purchase (first interaction after page change - retry applied)"):
        def action():
            el = wait.until(EC.element_to_be_clickable((By.ID, "finish")))
            el.click()
        _retry_interaction(driver, action, "finish_click")
        wait.until(EC.url_contains("/checkout-complete.html"))
        attach_screenshot(driver, "checkout_complete")

    with allure.step("Return to products and logout via menu"):
        def action():
            el = wait.until(EC.element_to_be_clickable((By.ID, "back-to-products")))
            el.click()
        _retry_interaction(driver, action, "back_to_products")
        wait.until(EC.url_contains("/inventory.html"))
        attach_screenshot(driver, "inventory_after_return")

        # open menu and logout
        btn = wait.until(EC.presence_of_element_located((By.ID, "react-burger-menu-btn")))
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.5)
        el = wait.until(EC.element_to_be_clickable((By.ID, "logout_sidebar_link")))
        el.click()
        # verify returned to login page
        wait.until(EC.visibility_of_element_located((By.ID, "login-button")))
        attach_screenshot(driver, "logged_out")

    # Final assertion: user is logged out and login button visible
    assert wait.until(EC.visibility_of_element_located((By.ID, "login-button"))).is_displayed()
    attach_screenshot(driver, "assertion_passed")

@allure.title("Invalid login should not navigate away from login page")
@pytest.mark.negative
@pytest.mark.parametrize("username,password", [
    ("invalid_user", "wrong_password"),
    ("", "secret_sauce"),
    ("standard_user", "")
])
def test_invalid_login(setup, username, password):
    driver = setup
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)
    attach_screenshot(driver, "start")

    with allure.step("Attempt login with invalid credentials"):
        el = wait.until(EC.presence_of_element_located((By.ID, "user-name")))
        el.clear()
        el.send_keys(username)
        el = wait.until(EC.presence_of_element_located((By.ID, "password")))
        el.clear()
        el.send_keys(password)
        btn = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        btn.click()
        # Expect to remain on login page; verify login-button still visible
        wait.until(EC.visibility_of_element_located((By.ID, "login-button")))
        attach_screenshot(driver, "login_attempted_invalid")

    assert wait.until(EC.visibility_of_element_located((By.ID, "login-button"))).is_displayed()
    attach_screenshot(driver, "assertion_passed")

@allure.title("Checkout validation: missing first name should prevent progression")
@pytest.mark.boundary
def test_checkout_missing_firstname(setup):
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
        btn = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        btn.click()
        wait.until(EC.url_contains("/inventory.html"))
        attach_screenshot(driver, "logged_in")

    with allure.step("Add an item to cart (first interaction after page change - retry applied)"):
        def action():
            el = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-backpack")))
            el.click()
        _retry_interaction(driver, action, "add_backpack_boundary")
        attach_screenshot(driver, "added_backpack")

    with allure.step("Open cart and proceed to checkout"):
        el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.shopping_cart_link")))
        el.click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cart_list")))
        attach_screenshot(driver, "cart_open")
        def action_checkout():
            el = wait.until(EC.element_to_be_clickable((By.ID, "checkout")))
            el.click()
        _retry_interaction(driver, action_checkout, "checkout_click_boundary")
        wait.until(EC.url_contains("/checkout-step-one.html"))
        attach_screenshot(driver, "checkout_step_one")

    with allure.step("Leave first name empty, fill other fields and continue"):
        # Intentionally do NOT fill first-name
        el = wait.until(EC.presence_of_element_located((By.ID, "last-name")))
        el.clear()
        el.send_keys("test")
        el = wait.until(EC.presence_of_element_located((By.ID, "postal-code")))
        el.clear()
        el.send_keys("234567")
        btn = wait.until(EC.element_to_be_clickable((By.ID, "continue")))
        btn.click()
        # Expect to remain on checkout-step-one due to missing required field
        wait.until(EC.url_contains("/checkout-step-one.html"))
        attach_screenshot(driver, "checkout_still_step_one")

    assert "/checkout-step-one.html" in driver.current_url
    attach_screenshot(driver, "assertion_passed")

@allure.title("Cart add and remove flow: remove one of two items")
@pytest.mark.regression
def test_cart_add_remove_flow(setup):
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
        btn = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        btn.click()
        wait.until(EC.url_contains("/inventory.html"))
        attach_screenshot(driver, "logged_in")

    with allure.step("Add two items to cart (first interaction after page change - retry applied)"):
        def action():
            el = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-backpack")))
            el.click()
        _retry_interaction(driver, action, "add_backpack_cartflow")
        el = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-bike-light")))
        el.click()
        attach_screenshot(driver, "added_two_items")

    with allure.step("Open cart and remove one item (first interaction after page change - retry applied)"):
        el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.shopping_cart_link")))
        el.click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cart_list")))
        attach_screenshot(driver, "cart_open")
        def action_remove():
            el = wait.until(EC.element_to_be_clickable((By.ID, "remove-sauce-labs-bike-light")))
            el.click()
        _retry_interaction(driver, action_remove, "remove_bike_light_cartflow")
        attach_screenshot(driver, "removed_one_item")

    # Assert the removed item's button is no longer visible/in DOM
    assert wait.until(EC.invisibility_of_element_located((By.ID, "remove-sauce-labs-bike-light")))
    attach_screenshot(driver, "assertion_passed")

@allure.title("Logout via sidebar menu returns to login page")
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
        btn = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        btn.click()
        wait.until(EC.url_contains("/inventory.html"))
        attach_screenshot(driver, "logged_in")

    with allure.step("Open menu and logout"):
        btn = wait.until(EC.presence_of_element_located((By.ID, "react-burger-menu-btn")))
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.5)
        el = wait.until(EC.element_to_be_clickable((By.ID, "logout_sidebar_link")))
        el.click()
        wait.until(EC.visibility_of_element_located((By.ID, "login-button")))
        attach_screenshot(driver, "logged_out")

    assert wait.until(EC.visibility_of_element_located((By.ID, "login-button"))).is_displayed()
    attach_screenshot(driver, "assertion_passed")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
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
        allure.attach(driver.get_screenshot_as_png(),
                      name=name, attachment_type=AttachmentType.PNG)
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

@allure.title("Happy path purchase flow")
@pytest.mark.regression
def test_happy_path_purchase(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)
    attach_screenshot(driver, "start")

    with allure.step("Enter username"):
        el = wait.until(EC.presence_of_element_located((By.ID, "user-name")))
        el.clear()
        el.send_keys("standard_user")

    with allure.step("Enter password"):
        el = wait.until(EC.presence_of_element_located((By.ID, "password")))
        el.clear()
        el.send_keys("secret_sauce")

    with allure.step("Click login"):
        btn = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        btn.click()

    # PAGE_CHANGE: navigated to /inventory.html
    with allure.step("Wait for inventory page and attach screenshot"):
        wait.until(EC.url_contains("/inventory.html"))
        attach_screenshot(driver, "navigated_to_inventory")

    # First interaction after page change: add to cart (apply retry rule)
    with allure.step("Add Sauce Labs Backpack to cart (with retry)"):
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-backpack")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_add_to_cart_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_add_to_cart")
            raise RuntimeError(f"add_to_cart failed: {last_err}")

    with allure.step("Open cart (nav link)"):
        # NAV_LINK click - use JavaScript click as it's a nav link
        cart_link = (By.CSS_SELECTOR, "a.shopping_cart_link")
        el = wait.until(EC.presence_of_element_located(cart_link))
        driver.execute_script("arguments[0].click();", el)
        wait.until(EC.url_contains("/cart.html"))
        attach_screenshot(driver, "navigated_to_cart")

    with allure.step("Click checkout"):
        driver.implicitly_wait(10)
        checkout = (By.ID, "checkout")
        el = wait.until(EC.presence_of_element_located(cart_link))
        driver.execute_script("arguments[0].click();", el)

    # PAGE_CHANGE: navigated to /checkout-step-one.html
    with allure.step("Wait for checkout-step-one page and attach screenshot"):
        wait.until(EC.url_contains("/checkout-step-one.html"))
        attach_screenshot(driver, "navigated_to_checkout_step_one")

    # First interaction after page change: fill first name (apply retry rule)
    with allure.step("Fill checkout information (with retry for first interaction)"):
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el = wait.until(EC.presence_of_element_located((By.ID, "firstName")))
                el.clear()
                el.send_keys("John")
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_fill_firstname_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_fill_firstname")
            raise RuntimeError(f"fill_firstname failed: {last_err}")

        el = wait.until(EC.presence_of_element_located((By.ID, "lastName")))
        el.clear()
        el.send_keys("Doe")

        el = wait.until(EC.presence_of_element_located((By.ID, "postalCode")))
        el.clear()
        el.send_keys("12345")

    with allure.step("Click continue"):
        btn = driver.find_element(By.XPATH, "//button[@id='continue']")
        btn.click()

    # PAGE_CHANGE: navigated to /checkout-step-two.html
    with allure.step("Wait for checkout-step-two page and attach screenshot"):
        wait.until(EC.url_contains("/checkout-step-two.html"))
        attach_screenshot(driver, "navigated_to_checkout_step_two")

    # First interaction after page change: (we will click finish) apply retry
    with allure.step("Finish checkout (with retry on first interaction)"):
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                btn = wait.until(EC.element_to_be_clickable((By.ID, "finish")))
                btn.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_finish_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_finish")
            raise RuntimeError(f"finish failed: {last_err}")

    # PAGE_CHANGE: navigated to /checkout-complete.html
    with allure.step("Wait for checkout complete and attach screenshot"):
        wait.until(EC.url_contains("/checkout-complete.html"))
        attach_screenshot(driver, "navigated_to_checkout_complete")

    with allure.step("Click back to products"):
        btn = wait.until(EC.element_to_be_clickable((By.ID, "back-to-products")))
        btn.click()

    # PAGE_CHANGE: back to /inventory.html
    with allure.step("Wait for inventory page after returning and attach screenshot"):
        wait.until(EC.url_contains("/inventory.html"))
        attach_screenshot(driver, "returned_to_inventory")

    # Final assertion: ensure we're back on inventory
    assert "/inventory.html" in driver.current_url
    attach_screenshot(driver, "assertion_passed")

@allure.title("Login with invalid credentials should stay on login page")
@pytest.mark.negative
def test_login_invalid_credentials(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)
    attach_screenshot(driver, "start")

    with allure.step("Enter invalid username"):
        el = wait.until(EC.presence_of_element_located((By.ID, "user-name")))
        el.clear()
        el.send_keys("invalid_user")

    with allure.step("Enter invalid password"):
        el = wait.until(EC.presence_of_element_located((By.ID, "password")))
        el.clear()
        el.send_keys("bad_password")

    with allure.step("Click login"):
        btn = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        btn.click()

    # No page change expected - assert still on login page
    assert driver.current_url == BASE_URL
    attach_screenshot(driver, "assertion_passed")

@allure.title("Checkout boundary: missing postal code prevents navigation")
@pytest.mark.boundary
def test_checkout_missing_postal_code(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)
    attach_screenshot(driver, "start")

    with allure.step("Login as standard_user"):
        el = wait.until(EC.presence_of_element_located((By.ID, "user-name")))
        el.clear()
        el.send_keys("standard_user")
        el = wait.until(EC.presence_of_element_located((By.ID, "password")))
        el.clear()
        el.send_keys("secret_sauce")
        btn = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
        btn.click()

    # PAGE_CHANGE to inventory
    wait.until(EC.url_contains("/inventory.html"))
    attach_screenshot(driver, "navigated_to_inventory")

    with allure.step("Add product to cart (with retry as first interaction after login)"):
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-backpack")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_add_to_cart_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_add_to_cart")
            raise RuntimeError(f"add_to_cart failed: {last_err}")

    with allure.step("Open cart"):
        cart_link = (By.CSS_SELECTOR, "a.shopping_cart_link")
        el = wait.until(EC.presence_of_element_located(cart_link))
        driver.execute_script("arguments[0].click();", el)
        wait.until(EC.url_contains("/cart.html"))
        attach_screenshot(driver, "navigated_to_cart")
        driver.implicitly_wait(10)

    with allure.step("Click checkout"):
        btn = wait.until(EC.element_to_be_clickable((By.ID, "checkout")))
        btn.click()

    # PAGE_CHANGE to checkout-step-one
    wait.until(EC.url_contains("/checkout-step-one.html"))
    attach_screenshot(driver, "navigated_to_checkout_step_one")

    # First interaction after page change: attempt to fill firstName with retry
    with allure.step("Fill first and last name but leave postal code empty (retry first interaction)"):
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el = wait.until(EC.presence_of_element_located((By.ID, "firstName")))
                el.clear()
                el.send_keys("Jane")
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_fill_firstname_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_fill_firstname")
            raise RuntimeError(f"fill_firstname failed: {last_err}")

        el = wait.until(EC.presence_of_element_located((By.ID, "lastName")))
        el.clear()
        el.send_keys("Smith")

        # Intentionally do NOT fill postalCode to test boundary

    with allure.step("Click continue with missing postal code"):
        btn = wait.until(EC.element_to_be_clickable((By.ID, "continue")))
        btn.click()

    # Expect to remain on checkout-step-one (no navigation to step-two)
    assert "/checkout-step-one.html" in driver.current_url
    attach_screenshot(driver, "assertion_passed")

@allure.title("Cart navigation verifies cart page")
@pytest.mark.smoke
def test_cart_navigation(setup):
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

    # PAGE_CHANGE to inventory
    wait.until(EC.url_contains("/inventory.html"))
    attach_screenshot(driver, "navigated_to_inventory")

    with allure.step("Add item to cart (retry first interaction)"):
        attempt, last_err = 0, None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-backpack")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_add_to_cart_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_add_to_cart")
            raise RuntimeError(f"add_to_cart failed: {last_err}")

    with allure.step("Open cart and verify URL"):
        cart_link = (By.CSS_SELECTOR, "a.shopping_cart_link")
        el = wait.until(EC.presence_of_element_located(cart_link))
        driver.execute_script("arguments[0].click();", el)
        wait.until(EC.url_contains("/cart.html"))
        attach_screenshot(driver, "navigated_to_cart")

    assert "/cart.html" in driver.current_url
    attach_screenshot(driver, "assertion_passed")

@allure.title("Logout from inventory via sidebar menu")
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

    # PAGE_CHANGE to inventory
    wait.until(EC.url_contains("/inventory.html"))
    attach_screenshot(driver, "navigated_to_inventory")

    with allure.step("Open sidebar menu"):
        btn = wait.until(EC.presence_of_element_located((By.ID, "react-burger-menu-btn")))
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.5)

    with allure.step("Click logout link in sidebar"):
        link = wait.until(EC.element_to_be_clickable((By.ID, "logout_sidebar_link")))
        link.click()
        # After logout expect to be back at the base login page
        wait.until(EC.url_to_be(BASE_URL))
        attach_screenshot(driver, "navigated_to_login_after_logout")

    assert driver.current_url == BASE_URL
    attach_screenshot(driver, "assertion_passed")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
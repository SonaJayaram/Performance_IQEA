import pytest
import time
import os
import allure
from allure_commons.types import AttachmentType
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from output.page_file_generator.new_page_file_sauce_demo import NewPageFileSauceDemo
from output.page_file_generator.inventory_sauce_demo import InventorySauceDemo
from output.page_file_generator.cart_sauce_demo import CartSauceDemo
from output.page_file_generator.checkout_step_one import CheckoutStepOne
from output.page_file_generator.checkout_step_two import CheckoutStepTwo
from output.page_file_generator.checkout_complete import CheckoutComplete
from output.page_file_generator.home_logout_sauce_demo import HomeLogoutSauceDemo

BASE_URL = "https://www.saucedemo.com/"
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def attach_screenshot(driver, name: str):
    try:
        png = driver.get_screenshot_as_png()
        allure.attach(png, name=name, attachment_type=AttachmentType.PNG)
        # also save to reports dir for external visibility
        try:
            filename = os.path.join(REPORTS_DIR, f"{name.replace(' ', '_')}_{int(time.time())}.png")
            with open(filename, "wb") as f:
                f.write(png)
        except Exception:
            pass
    except Exception:
        pass

def switch_to_new_window(driver, timeout: int = 10):
    try:
        WebDriverWait(driver, timeout).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
    except TimeoutException:
        raise RuntimeError("New window did not appear within timeout")

# helper: created because POM getter methods may return stale elements; use robust waiting and JS fallback
with allure.step("auto-fix: created helper_wait_and_click because robust click with waits and JS fallback is needed"):
    def wait_and_click(driver, getter_callable, timeout=10):
        """
        getter_callable: a callable that returns a WebElement when invoked (e.g., lambda: page.get_login_button())
        """
        end = time.time() + timeout
        last_exc = None
        while time.time() < end:
            try:
                elem = getter_callable()
                if elem is None:
                    raise NoSuchElementException("getter returned None")
                # wait until displayed and enabled
                if not (elem.is_displayed() and elem.is_enabled()):
                    time.sleep(0.2)
                    continue
                try:
                    elem.click()
                    return
                except (WebDriverException, Exception) as e:
                    last_exc = e
                    # attempt JS click fallback
                    try:
                        driver.execute_script("arguments[0].click();", elem)
                        return
                    except Exception as e2:
                        last_exc = e2
                time.sleep(0.2)
            except (StaleElementReferenceException, NoSuchElementException) as e:
                last_exc = e
                time.sleep(0.2)
        if last_exc:
            raise last_exc
        raise RuntimeError("Could not click element within timeout")

with allure.step("auto-fix: created helper_wait_and_send_keys because robust send_keys with waits is needed"):
    def wait_and_send_keys(driver, getter_callable, text, clear_first=True, timeout=10):
        """
        getter_callable: callable that returns a WebElement (e.g., lambda: page.get_user_name_input())
        """
        end = time.time() + timeout
        last_exc = None
        while time.time() < end:
            try:
                elem = getter_callable()
                if elem is None:
                    raise NoSuchElementException("getter returned None")
                if not elem.is_displayed():
                    time.sleep(0.2)
                    continue
                try:
                    if clear_first:
                        elem.clear()
                    elem.send_keys(text)
                    return
                except (WebDriverException, Exception) as e:
                    last_exc = e
                    # fallback: set value via JS
                    try:
                        driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'))", elem, text)
                        return
                    except Exception as e2:
                        last_exc = e2
                time.sleep(0.2)
            except (StaleElementReferenceException, NoSuchElementException) as e:
                last_exc = e
                time.sleep(0.2)
        if last_exc:
            raise last_exc
        raise RuntimeError("Could not send keys within timeout")

@pytest.fixture(scope="function")
def setup():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(options=options)
    # rely on explicit waits
    driver.implicitly_wait(0)

    new_page = NewPageFileSauceDemo(driver)
    inventory = InventorySauceDemo(driver)
    cart = CartSauceDemo(driver)
    checkout1 = CheckoutStepOne(driver)
    checkout2 = CheckoutStepTwo(driver)
    checkout_complete = CheckoutComplete(driver)
    home_logout = HomeLogoutSauceDemo(driver)

    yield driver, new_page, inventory, cart, checkout1, checkout2, checkout_complete, home_logout

    try:
        driver.quit()
    except Exception:
        pass

def _retry_action(driver, action_callable, retries=2):
    attempt = 0
    last_error = None
    while attempt < retries:
        try:
            action_callable()
            return
        except Exception as e:
            last_error = e
            attach_screenshot(driver, f"retry_attempt_{attempt+1}")
            time.sleep(0.5)
            attempt += 1
    attach_screenshot(driver, "action_failed_final")
    raise RuntimeError(f"Action failed after {retries} attempts: {last_error}")

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # after each test phase, if failed during call, attach screenshot
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        setup_fixture = item.funcargs.get("setup", None)
        if setup_fixture:
            driver = setup_fixture[0]
            try:
                attach_screenshot(driver, f"failure_{item.name}")
            except Exception:
                pass

def test_TC01_successful_purchase_standard_user(setup):
    driver, new_page, inventory, cart, checkout1, checkout2, checkout_complete, home_logout = setup

    with allure.step("Navigate to login page"):
        _retry_action(driver, lambda: new_page.navigate())
        attach_screenshot(driver, "Navigate to login page")

    with allure.step("Enter username"):
        _retry_action(driver, lambda: wait_and_send_keys(driver, lambda: new_page.get_user_name_input(), "standard_user"))
        attach_screenshot(driver, "Enter username")

    with allure.step("Enter password"):
        _retry_action(driver, lambda: wait_and_send_keys(driver, lambda: new_page.get_password_input(), "secret_sauce"))
        attach_screenshot(driver, "Enter password")

    with allure.step("Click login"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: new_page.get_login_button()))
        attach_screenshot(driver, "Click login")
        time.sleep(10)

    with allure.step("Add backpack to cart"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: inventory.get_add_to_cart_sauce_labs_backpack()))
        attach_screenshot(driver, "Add backpack to cart")
        time.sleep(10)
    with allure.step("Go to shopping cart"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: inventory.get_shopping_cart_link()))
        attach_screenshot(driver, "Go to shopping cart")
        time.sleep(10)
    with allure.step("Click checkout"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: cart.get_checkout_button()))
        attach_screenshot(driver, "Click checkout")
        time.sleep(10)
    with allure.step("Enter checkout information"):
        _retry_action(driver, lambda: wait_and_send_keys(driver, lambda: checkout1.get_first_name_input(), "test"))
        attach_screenshot(driver, "Enter first name")
        _retry_action(driver, lambda: wait_and_send_keys(driver, lambda: checkout1.get_last_name_input(), "test"))
        attach_screenshot(driver, "Enter last name")
        _retry_action(driver, lambda: wait_and_send_keys(driver, lambda: checkout1.get_postal_code_input(), "3242354"))
        attach_screenshot(driver, "Enter postal code")
        _retry_action(driver, lambda: wait_and_click(driver, lambda: checkout1.get_continue_button()))
        attach_screenshot(driver, "Click continue")
        time.sleep(10)
    with allure.step("Finish checkout"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: checkout2.get_finish_button()))
        attach_screenshot(driver, "Finish checkout")
        time.sleep(10)
    with allure.step("Back to products"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: checkout_complete.get_back_to_products_button()))
        attach_screenshot(driver, "Back to products")
        time.sleep(10)
    with allure.step("Open burger menu"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: inventory.get_react_burger_menu_btn()))
        attach_screenshot(driver, "Open burger menu")
    with allure.step("Logout"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: home_logout.get_logout_sidebar_link()))
        attach_screenshot(driver, "Logout")

    # After logout user should be back to login page
    assert driver.current_url.rstrip('/') + '/' == BASE_URL, "TC01 - Successful purchase (standard_user): expected to be on login page"
    attach_screenshot(driver, "assertion_passed")

def test_TC12_logout_from_inventory_page(setup):
    driver, new_page, inventory, cart, checkout1, checkout2, checkout_complete, home_logout = setup

    with allure.step("Navigate to login page"):
        _retry_action(driver, lambda: new_page.navigate())
        attach_screenshot(driver, "Navigate to login page")

    with allure.step("Enter username"):
        _retry_action(driver, lambda: wait_and_send_keys(driver, lambda: new_page.get_user_name_input(), "standard_user"))
        attach_screenshot(driver, "Enter username")

    with allure.step("Enter password"):
        _retry_action(driver, lambda: wait_and_send_keys(driver, lambda: new_page.get_password_input(), "secret_sauce"))
        attach_screenshot(driver, "Enter password")

    with allure.step("Click login"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: new_page.get_login_button()))
        attach_screenshot(driver, "Click login")

    with allure.step("Open burger menu"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: inventory.get_react_burger_menu_btn()))
        attach_screenshot(driver, "Open burger menu")

    with allure.step("Logout"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: home_logout.get_logout_sidebar_link()))
        attach_screenshot(driver, "Logout")

    # After logout user should be back to login page
    assert driver.current_url.rstrip('/') + '/' == BASE_URL, "TC12 - Logout from Inventory Page: expected to be on login page"
    attach_screenshot(driver, "assertion_passed")

def test_TC05_add_product_to_cart(setup):
    driver, new_page, inventory, cart, checkout1, checkout2, checkout_complete, home_logout = setup


    with allure.step("Navigate to login page"):
        _retry_action(driver, lambda: new_page.navigate())
        attach_screenshot(driver, "Navigate to login page")

    with allure.step("Enter username"):
        _retry_action(driver, lambda: wait_and_send_keys(driver, lambda: new_page.get_user_name_input(), "standard_user"))
        attach_screenshot(driver, "Enter username")

    with allure.step("Enter password"):
        _retry_action(driver, lambda: wait_and_send_keys(driver, lambda: new_page.get_password_input(), "secret_sauce"))
        attach_screenshot(driver, "Enter password")

    with allure.step("Click login"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: new_page.get_login_button()))
        attach_screenshot(driver, "Click login")

    with allure.step("Add backpack to cart"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: inventory.get_add_to_cart_sauce_labs_backpack()))
        attach_screenshot(driver, "Add backpack to cart")

    with allure.step("Go to shopping cart"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: inventory.get_shopping_cart_link()))
        attach_screenshot(driver, "Go to shopping cart")

    # Expect to be on cart page
    assert driver.current_url.rstrip('/') == "https://www.saucedemo.com/cart.html"
    attach_screenshot(driver, "assertion_passed")

def test_TC08_login_with_invalid_password(setup):
    driver, new_page, inventory, cart, checkout1, checkout2, checkout_complete, home_logout = setup


    with allure.step("Navigate to login page"):
        _retry_action(driver, lambda: new_page.navigate())
        attach_screenshot(driver, "Navigate to login page")

    with allure.step("Enter username"):
        _retry_action(driver, lambda: wait_and_send_keys(driver, lambda: new_page.get_user_name_input(), "standard_user"))
        attach_screenshot(driver, "Enter username")

    with allure.step("Enter invalid password"):
        _retry_action(driver, lambda: wait_and_send_keys(driver, lambda: new_page.get_password_input(), "invalid_password"))
        attach_screenshot(driver, "Enter invalid password")

    with allure.step("Click login"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: new_page.get_login_button()))
        attach_screenshot(driver, "Click login")

    # Invalid login should remain on login page
    assert driver.current_url.rstrip('/') + '/' == BASE_URL, "TC08 - Login with Invalid Password: expected to remain on login page"
    attach_screenshot(driver, "assertion_passed")

def test_TC10_add_multiple_products_to_cart(setup):
    driver, new_page, inventory, cart, checkout1, checkout2, checkout_complete, home_logout = setup

    with allure.step("Navigate to login page"):
        _retry_action(driver, lambda: new_page.navigate())
        attach_screenshot(driver, "Navigate to login page")

    with allure.step("Enter username"):
        _retry_action(driver, lambda: wait_and_send_keys(driver, lambda: new_page.get_user_name_input(), "standard_user"))
        attach_screenshot(driver, "Enter username")

    with allure.step("Enter password"):
        _retry_action(driver, lambda: wait_and_send_keys(driver, lambda: new_page.get_password_input(), "secret_sauce"))
        attach_screenshot(driver, "Enter password")

    with allure.step("Click login"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: new_page.get_login_button()))
        attach_screenshot(driver, "Click login")

    with allure.step("Add multiple products"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: inventory.get_add_to_cart_sauce_labs_backpack()))
        attach_screenshot(driver, "Add backpack to cart")
        _retry_action(driver, lambda: wait_and_click(driver, lambda: inventory.get_add_to_cart_sauce_labs_bike_light()))
        attach_screenshot(driver, "Add bike light to cart")
        _retry_action(driver, lambda: wait_and_click(driver, lambda: inventory.get_add_to_cart_sauce_labs_onesie()))
        attach_screenshot(driver, "Add onesie to cart")

    with allure.step("Go to shopping cart"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: inventory.get_shopping_cart_link()))
        attach_screenshot(driver, "Go to shopping cart")

    # Expect to be on cart page
    assert driver.current_url.rstrip('/') == "https://www.saucedemo.com/cart.html"
    attach_screenshot(driver, "assertion_passed")

def test_TC11_checkout_with_missing_first_name(setup):
    driver, new_page, inventory, cart, checkout1, checkout2, checkout_complete, home_logout = setup

    with allure.step("Navigate to login page"):
        _retry_action(driver, lambda: new_page.navigate())
        attach_screenshot(driver, "Navigate to login page")

    with allure.step("Enter username"):
        _retry_action(driver, lambda: wait_and_send_keys(driver, lambda: new_page.get_user_name_input(), "standard_user"))
        attach_screenshot(driver, "Enter username")

    with allure.step("Enter password"):
        _retry_action(driver, lambda: wait_and_send_keys(driver, lambda: new_page.get_password_input(), "secret_sauce"))
        attach_screenshot(driver, "Enter password")

    with allure.step("Click login"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: new_page.get_login_button()))
        attach_screenshot(driver, "Click login")

    with allure.step("Add backpack to cart"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: inventory.get_add_to_cart_sauce_labs_backpack()))
        attach_screenshot(driver, "Add backpack to cart")

    with allure.step("Go to shopping cart and checkout"):
        _retry_action(driver, lambda: wait_and_click(driver, lambda: inventory.get_shopping_cart_link()))
        attach_screenshot(driver, "Go to shopping cart")
        _retry_action(driver, lambda: wait_and_click(driver, lambda: cart.get_checkout_button()))
        attach_screenshot(driver, "Click checkout")

    with allure.step("Enter checkout information with missing first name"):
        _retry_action(driver, lambda: wait_and_send_keys(driver, lambda: checkout1.get_first_name_input(), ""))
        attach_screenshot(driver, "Enter empty first name")
        _retry_action(driver, lambda: wait_and_send_keys(driver, lambda: checkout1.get_last_name_input(), "test"))
        attach_screenshot(driver, "Enter last name")
        _retry_action(driver, lambda: wait_and_send_keys(driver, lambda: checkout1.get_postal_code_input(), "3242354"))
        attach_screenshot(driver, "Enter postal code")
        _retry_action(driver, lambda: wait_and_click(driver, lambda: checkout1.get_continue_button()))
        attach_screenshot(driver, "Click continue")

    # Missing first name should keep user on checkout-step-one page
    assert driver.current_url.rstrip('/') == "https://www.saucedemo.com/checkout-step-one.html"
    attach_screenshot(driver, "assertion_passed")
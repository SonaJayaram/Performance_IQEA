import pytest
import time
import os
import allure
from allure_commons.types import AttachmentType
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    StaleElementReferenceException,
    WebDriverException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
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
        try:
            filepath = os.path.join(REPORTS_DIR, f"{name.replace(' ','_')}_{int(time.time())}.png")
            with open(filepath, "wb") as f:
                f.write(png)
        except Exception:
            pass
    except Exception:
        pass


def safe_get(getter_callable, retries: int = 3, delay: float = 0.5):
    last_exc = None
    for _ in range(retries):
        try:
            elem = getter_callable()
            if elem is not None:
                return elem
        except Exception as e:
            last_exc = e
        time.sleep(delay)
    raise RuntimeError(f"safe_get failed after {retries} attempts: {last_exc}")


def safe_click(driver, getter_callable, label: str = "", retries: int = 3):
    last_exc = None
    for attempt in range(retries):
        try:
            elem = getter_callable()
            if elem is None:
                raise RuntimeError("Element not found for click")
            try:
                elem.click()
                return
            except (WebDriverException, StaleElementReferenceException) as e:
                last_exc = e
                try:
                    fresh = getter_callable()
                    driver.execute_script("arguments[0].click();", fresh)
                    return
                except Exception as e2:
                    last_exc = e2
        except Exception as e:
            last_exc = e
            attach_screenshot(driver, f"safe_click_retry_{label}_{attempt+1}")
        time.sleep(0.5)
    attach_screenshot(driver, f"safe_click_failed_{label}")
    raise RuntimeError(f"safe_click [{label}] failed: {last_exc}")


def safe_send_keys(driver, getter_callable, text: str, label: str = "", retries: int = 3):
    last_exc = None
    for attempt in range(retries):
        try:
            elem = getter_callable()
            if elem is None:
                raise RuntimeError("Element not found for send_keys")
            try:
                elem.clear()
                elem.send_keys(text)
                return
            except (WebDriverException, StaleElementReferenceException) as e:
                last_exc = e
                try:
                    fresh = getter_callable()
                    driver.execute_script("arguments[0].value = arguments[1];", fresh, text)
                    return
                except Exception as e2:
                    last_exc = e2
        except Exception as e:
            last_exc = e
            attach_screenshot(driver, f"safe_send_keys_retry_{label}_{attempt+1}")
        time.sleep(0.5)
    attach_screenshot(driver, f"safe_send_keys_failed_{label}")
    raise RuntimeError(f"safe_send_keys [{label}] failed: {last_exc}")


def wait_for_sidebar_item(driver, getter_callable, timeout: int = 5):
    try:
        return WebDriverWait(driver, timeout).until(lambda d: _verify_element_for_interaction(getter_callable()))
    except TimeoutException as e:
        raise RuntimeError(f"wait_for_sidebar_item timed out: {e}")


def _verify_element_for_interaction(elem):
    if elem is None:
        return False
    try:
        # ensure element is visible, enabled and has width > 0
        if elem.is_displayed() and elem.is_enabled():
            # getBoundingClientRect via driver.execute_script cannot be called here; return elem and let caller JS click
            return elem
    except Exception:
        return False
    return False


def do_login(driver, login_page_pom, inventory_pom,
             username="standard_user", password="secret_sauce"):
    login_page_pom.navigate()
    safe_send_keys(driver, lambda: login_page_pom.get_user_name_input(), username, label="username")
    safe_send_keys(driver, lambda: login_page_pom.get_password_input(), password, label="password")
    safe_click(driver, lambda: login_page_pom.get_login_button(), label="login_button")
    # wait for inventory page readiness using common patterns
    try:
        if hasattr(inventory_pom, "wait_until_page_ready"):
            inventory_pom.wait_until_page_ready()
        else:
            # wait for a known inventory element to be present and clickable
            WebDriverWait(driver, 5).until(lambda d: inventory_pom.get_add_to_cart_sauce_labs_backpack() is not None)
    except Exception:
        # fallback: small screenshot and continue, tests will fail later if broken
        attach_screenshot(driver, "do_login_post_wait_failed")


@pytest.fixture(scope="function")
def setup():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(0)

    login_page = NewPageFileSauceDemo(driver)
    inventory = InventorySauceDemo(driver)
    cart = CartSauceDemo(driver)
    checkout1 = CheckoutStepOne(driver)
    checkout2 = CheckoutStepTwo(driver)
    checkout_complete = CheckoutComplete(driver)
    home_logout = HomeLogoutSauceDemo(driver)

    yield driver, login_page, inventory, cart, checkout1, checkout2, checkout_complete, home_logout

    try:
        driver.quit()
    except Exception:
        pass


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        fixture = item.funcargs.get("setup")
        if fixture:
            try:
                attach_screenshot(fixture[0], f"FAILED_{item.name}")
            except Exception:
                pass


def _safe_js_click(driver, elem, label: str = ""):
    try:
        driver.execute_script("arguments[0].click();", elem)
    except Exception:
        attach_screenshot(driver, f"js_click_failed_{label}")
        raise


def switch_to_new_window(driver, timeout: int = 5):
    with allure.step("auto-fix: created helper_switch_to_new_window because test may open new window"):
        current = set(driver.window_handles)
        try:
            WebDriverWait(driver, timeout).until(lambda d: len(d.window_handles) > len(current))
        except TimeoutException:
            # no new window, return False
            return False
        new_handles = [h for h in driver.window_handles if h not in current]
        if new_handles:
            driver.switch_to.window(new_handles[-1])
            return True
        return False


def _click_and_attach(driver, getter_lambda, label):
    safe_click(driver, getter_lambda, label=label)
    attach_screenshot(driver, f"after_{label}")


def _send_and_attach(driver, getter_lambda, text, label):
    safe_send_keys(driver, getter_lambda, text, label=label)
    attach_screenshot(driver, f"after_{label}")


def _get_and_attach(driver, getter_lambda, label):
    elem = safe_get(getter_lambda)
    attach_screenshot(driver, f"after_get_{label}")
    return elem


def test_mar_saucedemo_action(setup):
    driver, login_page, inventory, cart, checkout1, checkout2, checkout_complete, home_logout = setup

    with allure.step("do_login"):
        do_login(driver, login_page, inventory)
        attach_screenshot(driver, "after_login")

    with allure.step("add_sauce_labs_backpack_to_cart"):
        _click_and_attach(driver, lambda: inventory.get_add_to_cart_sauce_labs_backpack(), "add_backpack")

    with allure.step("open_shopping_cart"):
        _click_and_attach(driver, lambda: inventory.get_shopping_cart_link(), "open_cart")

    with allure.step("click_checkout_on_cart"):
        _click_and_attach(driver, lambda: cart.get_checkout_button(), "cart_checkout")

    with allure.step("enter_first_name"):
        _send_and_attach(driver, lambda: checkout1.get_first_name_input(), "test", "first_name")

    with allure.step("enter_last_name"):
        _send_and_attach(driver, lambda: checkout1.get_last_name_input(), "test", "last_name")

    with allure.step("enter_postal_code"):
        _send_and_attach(driver, lambda: checkout1.get_postal_code_input(), "3242354", "postal_code")

    with allure.step("click_continue_on_checkout_step_one"):
        _click_and_attach(driver, lambda: checkout1.get_continue_button(), "checkout_continue")

    with allure.step("click_finish_on_checkout_step_two"):
        _click_and_attach(driver, lambda: checkout2.get_finish_button(), "checkout_finish")

    with allure.step("click_back_to_products_on_complete"):
        _click_and_attach(driver, lambda: checkout_complete.get_back_to_products_button(), "back_to_products")

    with allure.step("open_react_burger_menu"):
        _click_and_attach(driver, lambda: inventory.get_react_burger_menu_btn(), "open_burger_menu")

    with allure.step("wait_for_and_click_logout_sidebar_link"):
        elem = wait_for_sidebar_item(driver, lambda: home_logout.get_logout_sidebar_link())
        _safe_js_click(driver, elem, label="logout_sidebar")
        attach_screenshot(driver, "after_logout_click")

    with allure.step("assert_logged_out_and_back_to_base"):
        # Primary assert for this test
        assert driver.current_url.rstrip("/") + "/" == BASE_URL
        attach_screenshot(driver, "assertion_passed")
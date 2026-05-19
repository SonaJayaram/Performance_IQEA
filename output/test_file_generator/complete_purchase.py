import os
import time
import json
import pytest
import allure
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from allure_commons.types import AttachmentType

BASE_URL = "https://www.saucedemo.com/"

PAGE_FILE_KEY_SN = "jan_sauce_demo_login_py"


def ensure_reports_dir():
    reports_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir


def switch_to_new_window(driver, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            return
        time.sleep(0.5)
    raise RuntimeError("New window did not appear within timeout")


def _attach_screenshot(driver, name="screenshot"):
    try:
        allure.attach(driver.get_screenshot_as_png(), name=name, attachment_type=AttachmentType.PNG)
    except Exception:
        # best-effort
        pass


def _write_report_artifacts(driver, tag="failure"):
    reports_dir = ensure_reports_dir()
    ts = int(time.time() * 1000)
    safe_name = f"{tag}_{ts}"
    try:
        png_path = os.path.join(reports_dir, f"{safe_name}.png")
        with open(png_path, "wb") as f:
            f.write(driver.get_screenshot_as_png())
    except Exception:
        pass
    try:
        html_path = os.path.join(reports_dir, f"{safe_name}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    except Exception:
        pass
    try:
        meta = {"url": driver.current_url, "timestamp": ts}
        json_path = os.path.join(reports_dir, f"{safe_name}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(meta, f)
    except Exception:
        pass
    return reports_dir


def find_element_with_healing(driver, locator_candidates, desc, timeout=5):
    # locator_candidates: list of (By, selector) tuples
    last_exception = None
    with allure.step(f"Find element: {desc} using candidates: {locator_candidates}"):
        _attach_screenshot(driver, name=f"before_find_{desc}")
        # 1) Try direct attempts quickly
        for by, sel in locator_candidates:
            try:
                el = driver.find_element(by, sel)
                _attach_screenshot(driver, name=f"found_direct_{desc}")
                return el
            except Exception as e:
                last_exception = e
                continue
        # 2) Retry once after a short wait (replacing sleep with a short WebDriverWait)
        try:
            WebDriverWait(driver, 0.6).until(lambda d: True)
        except Exception:
            pass
        for by, sel in locator_candidates:
            try:
                el = driver.find_element(by, sel)
                _attach_screenshot(driver, name=f"found_retry_{desc}")
                return el
            except Exception as e:
                last_exception = e
                continue
        # 3) Explicit wait fallback per locator candidates
        for by, sel in locator_candidates:
            try:
                el = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((by, sel)))
                _attach_screenshot(driver, name=f"found_wait_{desc}")
                return el
            except Exception as e:
                last_exception = e
                with allure.step(f"healing: visibility wait failed for {by}={sel}"):
                    _attach_screenshot(driver, name=f"healing_wait_failed_{desc}")
                continue
        # 4) Attempt generated fallback selectors: by id, by name, by xpath visible text attempts
        for attempt in range(2):
            with allure.step(f"healing: attempt generated fallback {attempt+1} for {desc}"):
                # attempt1: id from desc if plausible
                guess_id = desc.replace(" ", "_")
                try:
                    el = driver.find_element(By.ID, guess_id)
                    _attach_screenshot(driver, name=f"found_fallback_id_{desc}")
                    return el
                except Exception:
                    pass
                # attempt2: visible text xpath
                try:
                    xpath = f"//*[text()='{desc}']"
                    el = driver.find_element(By.XPATH, xpath)
                    _attach_screenshot(driver, name=f"found_fallback_text_{desc}")
                    return el
                except Exception:
                    pass
                try:
                    WebDriverWait(driver, 0.5).until(lambda d: True)
                except Exception:
                    pass
        # If all fail, raise
        raise last_exception if last_exception is not None else RuntimeError(f"Element {desc} not found")


def click_with_healing(driver, locator_candidates, desc):
    with allure.step(f"Click action: {desc}"):
        try:
            el = find_element_with_healing(driver, locator_candidates, desc)
            try:
                el.click()
                _attach_screenshot(driver, name=f"clicked_{desc}")
                return
            except Exception:
                # fallback to JS click immediately
                driver.execute_script("arguments[0].click();", el)
                _attach_screenshot(driver, name=f"clicked_js_primary_{desc}")
                return
        except Exception as first_exc:
            with allure.step(f"click failed: retrying once for {desc}"):
                _attach_screenshot(driver, name=f"click_failed_first_{desc}")
                try:
                    WebDriverWait(driver, 0.6).until(lambda d: True)
                except Exception:
                    pass
                try:
                    el = find_element_with_healing(driver, locator_candidates, desc)
                    try:
                        el.click()
                        _attach_screenshot(driver, name=f"clicked_retry_{desc}")
                        return
                    except Exception:
                        driver.execute_script("arguments[0].click();", el)
                        _attach_screenshot(driver, name=f"clicked_js_retry_{desc}")
                        return
                except Exception:
                    with allure.step(f"healing: fallback click for {desc}"):
                        _attach_screenshot(driver, name=f"click_failed_second_{desc}")
                        # Last attempt: execute JavaScript click if element present via wait
                        try:
                            el = WebDriverWait(driver, 3).until(EC.element_to_be_clickable(locator_candidates[0]))
                            driver.execute_script("arguments[0].click();", el)
                            _attach_screenshot(driver, name=f"clicked_js_{desc}")
                            return
                        except Exception as e:
                            _attach_screenshot(driver, name=f"click_all_failed_{desc}")
                            raise


def send_keys_with_healing(driver, locator_candidates, desc, value):
    with allure.step(f"Send keys: {desc} -> '{value}'"):
        try:
            el = find_element_with_healing(driver, locator_candidates, desc)
            try:
                el.clear()
            except Exception:
                pass
            el.send_keys(value)
            _attach_screenshot(driver, name=f"sentkeys_{desc}")
            return
        except Exception as first_exc:
            with allure.step(f"send_keys failed: retrying once for {desc}"):
                _attach_screenshot(driver, name=f"sendkeys_failed_first_{desc}")
                try:
                    WebDriverWait(driver, 0.6).until(lambda d: True)
                except Exception:
                    pass
                try:
                    el = find_element_with_healing(driver, locator_candidates, desc)
                    try:
                        el.clear()
                    except Exception:
                        pass
                    el.send_keys(value)
                    _attach_screenshot(driver, name=f"sentkeys_retry_{desc}")
                    return
                except Exception:
                    with allure.step(f"healing: fallback send_keys for {desc}"):
                        _attach_screenshot(driver, name=f"sendkeys_failed_second_{desc}")
                        # fallback: set value via JS
                        try:
                            el = find_element_with_healing(driver, locator_candidates, desc)
                            driver.execute_script("arguments[0].value = arguments[1];", el, value)
                            _attach_screenshot(driver, name=f"sentkeys_js_{desc}")
                            return
                        except Exception:
                            _attach_screenshot(driver, name=f"sendkeys_all_failed_{desc}")
                            raise


def helper_login_jan_sauce_demo_login_py(driver, username, password):
    with allure.step("POM jan_sauce_demo_login.py not available — using helper_login_jan_sauce_demo_login_py (auto-healed)"):
        allure.attach(json.dumps({"healed": "created helper_login_jan_sauce_demo_login_py"}), name="healing_info", attachment_type=AttachmentType.JSON)
        _attach_screenshot(driver, name="login_helper_start")
        send_keys_with_healing(driver, [(By.ID, "user-name"), (By.NAME, "user-name"), (By.XPATH, "//*[@id='user-name']")], "user-name", username)
        send_keys_with_healing(driver, [(By.ID, "password"), (By.NAME, "password"), (By.XPATH, "//*[@id='password']")], "password", password)
        click_with_healing(driver, [(By.ID, "login-button"), (By.NAME, "login-button"), (By.XPATH, "//*[@id='login-button']")], "login-button")


def helper_add_to_cart_jan_sauce_demo_login_py(driver):
    with allure.step("POM jan_sauce_demo_login.py not available — using helper_add_to_cart_jan_sauce_demo_login_py (auto-healed)"):
        allure.attach(json.dumps({"healed": "created helper_add_to_cart_jan_sauce_demo_login_py"}), name="healing_info", attachment_type=AttachmentType.JSON)
        _attach_screenshot(driver, name="add_to_cart_start")
        click_with_healing(driver, [(By.ID, "add-to-cart-sauce-labs-backpack"), (By.XPATH, "//*[@id='add-to-cart-sauce-labs-backpack']")], "add-to-cart-sauce-labs-backpack")
        _attach_screenshot(driver, name="added_to_cart")


def helper_open_cart_jan_sauce_demo_login_py(driver):
    with allure.step("POM jan_sauce_demo_login.py not available — using helper_open_cart_jan_sauce_demo_login_py (auto-healed)"):
        allure.attach(json.dumps({"healed": "created helper_open_cart_jan_sauce_demo_login_py"}), name="healing_info", attachment_type=AttachmentType.JSON)
        _attach_screenshot(driver, name="open_cart_start")
        click_with_healing(driver, [(By.CLASS_NAME, "shopping_cart_link"), (By.XPATH, "//a[@class='shopping_cart_link']"), (By.ID, "shopping_cart_container")], "shopping_cart_link")


def helper_checkout_fill_jan_sauce_demo_login_py(driver, first_name, last_name, postal_code):
    with allure.step("POM jan_sauce_demo_login.py not available — using helper_checkout_fill_jan_sauce_demo_login_py (auto-healed)"):
        allure.attach(json.dumps({"healed": "created helper_checkout_fill_jan_sauce_demo_login_py"}), name="healing_info", attachment_type=AttachmentType.JSON)
        click_with_healing(driver, [(By.ID, "checkout"), (By.XPATH, "//*[@id='checkout']")], "checkout")
        _attach_screenshot(driver, name="checkout_page")
        send_keys_with_healing(driver, [(By.ID, "firstName"), (By.NAME, "firstName"), (By.XPATH, "//*[@id='firstName']")], "firstName", first_name)
        send_keys_with_healing(driver, [(By.ID, "lastName"), (By.NAME, "lastName"), (By.XPATH, "//*[@id='lastName']")], "last_name", last_name)
        send_keys_with_healing(driver, [(By.ID, "postalCode"), (By.NAME, "postalCode"), (By.XPATH, "//*[@id='postalCode']")], "postalCode", postal_code)
        click_with_healing(driver, [(By.ID, "continue"), (By.XPATH, "//*[@id='continue']")], "continue")


def helper_finish_purchase_jan_sauce_demo_login_py(driver):
    with allure.step("POM jan_sauce_demo_login.py not available — using helper_finish_purchase_jan_sauce_demo_login_py (auto-healed)"):
        allure.attach(json.dumps({"healed": "created helper_finish_purchase_jan_sauce_demo_login_py"}), name="healing_info", attachment_type=AttachmentType.JSON)
        click_with_healing(driver, [(By.ID, "finish"), (By.XPATH, "//*[@id='finish']")], "finish")
        _attach_screenshot(driver, name="finished_purchase")
        click_with_healing(driver, [(By.ID, "back-to-products"), (By.XPATH, "//*[@id='back-to-products']")], "back-to-products")
        _attach_screenshot(driver, name="back_to_products_clicked")


@pytest.fixture(scope="function")
def driver():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    try:
        yield driver
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def _handle_assertion_failure(driver, exc):
    with allure.step("Assertion failed - collecting artifacts"):
        try:
            allure.attach(driver.get_screenshot_as_png(), name="assertion_failure_screenshot", attachment_type=AttachmentType.PNG)
        except Exception:
            pass
        try:
            allure.attach(driver.page_source.encode("utf-8"), name="assertion_failure_page_source", attachment_type=AttachmentType.HTML)
        except Exception:
            pass
        reports_dir = _write_report_artifacts(driver, tag="assertion_failure")
        with open(os.path.join(reports_dir, "note.txt"), "w") as f:
            f.write(f"Artifacts saved in {reports_dir}\n")
        raise exc


@allure.feature("Purchase Flow")
@allure.story("TC01 - Successful purchase (standard_user)")
def test_TC01_successful_purchase_standard_user(driver):
    # Exactly one primary assertion at the end: user is back on inventory page after purchase
    with allure.step("Start test: TC01 - Successful purchase (standard_user)"):
        driver.get(BASE_URL)
        _attach_screenshot(driver, name="landing_page")
        try:
            if len(driver.window_handles) > 1:
                with allure.step("Switching to new window as recorded"):
                    switch_to_new_window(driver)
                    _attach_screenshot(driver, name="switched_to_new_window")
        except Exception:
            with allure.step("No new window to switch to or switch failed"):
                _attach_screenshot(driver, name="switch_new_window_failed")

    with allure.step("POM availability check and healing"):
        allure.attach(json.dumps({"note": "jan_sauce_demo_login.py methods present in source list but class name not provided; using helpers"}), name="healing_summary", attachment_type=AttachmentType.JSON)
        _attach_screenshot(driver, name="pom_healing")

    with allure.step("Login with standard_user"):
        try:
            helper_login_jan_sauce_demo_login_py(driver, "standard_user", "secret_sauce")
        except Exception as e:
            _attach_screenshot(driver, name="login_error")
            raise

    with allure.step("Add product to cart"):
        try:
            helper_add_to_cart_jan_sauce_demo_login_py(driver)
        except Exception as e:
            _attach_screenshot(driver, name="add_to_cart_error")
            raise

    with allure.step("Open cart"):
        try:
            helper_open_cart_jan_sauce_demo_login_py(driver)
        except Exception as e:
            _attach_screenshot(driver, name="open_cart_error")
            raise

    with allure.step("Checkout and fill information"):
        try:
            helper_checkout_fill_jan_sauce_demo_login_py(driver, "t", "t", "hg")
        except Exception as e:
            _attach_screenshot(driver, name="checkout_fill_error")
            raise

    with allure.step("Finish purchase and return to products"):
        try:
            helper_finish_purchase_jan_sauce_demo_login_py(driver)
        except Exception as e:
            _attach_screenshot(driver, name="finish_error")
            raise

    with allure.step("Primary assertion: verify we are back on inventory page (/inventory.html)"):
        try:
            WebDriverWait(driver, 5).until(lambda d: "/inventory.html" in d.current_url)
            current = driver.current_url
            _attach_screenshot(driver, name="final_page")
            assert current.endswith("/inventory.html"), f"expected to be on inventory.html, but was on {current}"
        except AssertionError as ae:
            _handle_assertion_failure(driver, ae)
        except Exception as e:
            _handle_assertion_failure(driver, AssertionError(f"Primary assertion failed due to exception: {e}"))
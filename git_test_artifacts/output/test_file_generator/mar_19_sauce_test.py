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
from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementClickInterceptedException,
    TimeoutException,
    NoSuchElementException,
)

BASE_URL = "https://www.saucedemo.com/"

REPORTS_DIR = os.path.join(os.getcwd(), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def save_artifacts_on_error(driver, name_prefix):
    try:
        png = driver.get_screenshot_as_png()
    except Exception:
        png = None
    try:
        page_src = driver.page_source
    except Exception:
        page_src = "<unable to get page source>"
    ts = int(time.time())
    png_path = os.path.join(REPORTS_DIR, f"{name_prefix}_{ts}.png")
    html_path = os.path.join(REPORTS_DIR, f"{name_prefix}_{ts}.html")
    try:
        if png:
            with open(png_path, "wb") as f:
                f.write(png)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(page_src)
    except Exception:
        pass
    return png_path, html_path

def switch_to_new_window(driver, timeout=10):
    with allure.step("Switch to new window if present"):
        try:
            WebDriverWait(driver, timeout).until(lambda d: len(d.window_handles) > 1)
            driver.switch_to.window(driver.window_handles[-1])
            return
        except TimeoutException:
            raise RuntimeError("New window did not appear within timeout")

def find_element_with_healing(driver, by, value, name_for_logs, timeout=5, alt_locators=None):
    alt_locators = alt_locators or []
    with allure.step(f"Locate element {name_for_logs} by {by}='{value}' (with healing)"):
        # Try explicit wait first for stability
        locator = (by, value)
        try:
            elem = WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))
            elem = WebDriverWait(driver, 1).until(EC.visibility_of(elem))
            allure.attach(driver.get_screenshot_as_png(), name=f"found_{name_for_logs}_wait", attachment_type=allure.attachment_type.PNG)
            return elem
        except Exception:
            allure.attach(driver.get_screenshot_as_png(), name=f"wait_failed_{name_for_logs}", attachment_type=allure.attachment_type.PNG)
        # try alternate locators
        for alt_by, alt_value in alt_locators:
            with allure.step(f"healing: trying alternate locator {alt_by}='{alt_value}' for {name_for_logs}"):
                try:
                    elem = WebDriverWait(driver, 4).until(EC.visibility_of_element_located((alt_by, alt_value)))
                    allure.attach(driver.get_screenshot_as_png(), name=f"found_{name_for_logs}_alt", attachment_type=allure.attachment_type.PNG)
                    return elem
                except Exception:
                    allure.attach(driver.get_screenshot_as_png(), name=f"alt_failed_{name_for_logs}", attachment_type=allure.attachment_type.PNG)
        # generated fallbacks
        generated_attempts = [
            (By.ID, value),
            (By.NAME, value),
            (By.XPATH, f"//button[contains(normalize-space(.),'{value}')]"),
            (By.XPATH, f"//*[contains(normalize-space(.),'{value}')]")
        ]
        for gby, gval in generated_attempts:
            with allure.step(f"healing: trying generated locator {gby}='{gval}' for {name_for_logs}"):
                try:
                    elem = WebDriverWait(driver, 3).until(EC.visibility_of_element_located((gby, gval)))
                    allure.attach(driver.get_screenshot_as_png(), name=f"found_{name_for_logs}_generated", attachment_type=allure.attachment_type.PNG)
                    return elem
                except Exception:
                    allure.attach(driver.get_screenshot_as_png(), name=f"generated_failed_{name_for_logs}", attachment_type=allure.attachment_type.PNG)
        # last ditch: try driver.find_element to raise clear error
        try:
            elem = driver.find_element(by, value)
            allure.attach(driver.get_screenshot_as_png(), name=f"found_{name_for_logs}_direct", attachment_type=allure.attachment_type.PNG)
            return elem
        except Exception:
            allure.attach(driver.get_screenshot_as_png(), name=f"not_found_{name_for_logs}", attachment_type=allure.attachment_type.PNG)
            raise RuntimeError(f"Element {name_for_logs} not found after healing attempts")

def click_element(driver, by, value, name_for_logs, alt_locators=None):
    with allure.step(f"Click {name_for_logs}"):
        try:
            elem = find_element_with_healing(driver, by, value, name_for_logs, alt_locators=alt_locators)
            try:
                # attempt normal click
                elem.click()
                allure.attach(driver.get_screenshot_as_png(), name=f"clicked_{name_for_logs}", attachment_type=allure.attachment_type.PNG)
                return
            except (ElementClickInterceptedException, StaleElementReferenceException, Exception):
                # fallback: try JS click after scrolling into view
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
                    driver.execute_script("arguments[0].click();", elem)
                    allure.attach(driver.get_screenshot_as_png(), name=f"js_clicked_{name_for_logs}", attachment_type=allure.attachment_type.PNG)
                    return
                except Exception:
                    # try re-find and JS click
                    elem = find_element_with_healing(driver, by, value, name_for_logs, alt_locators=alt_locators)
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
                    driver.execute_script("arguments[0].click();", elem)
                    allure.attach(driver.get_screenshot_as_png(), name=f"js_clicked_after_refind_{name_for_logs}", attachment_type=allure.attachment_type.PNG)
                    return
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name=f"click_failed_{name_for_logs}", attachment_type=allure.attachment_type.PNG)
            png_path, html_path = save_artifacts_on_error(driver, f"click_failed_{name_for_logs}")
            raise

def input_text(driver, by, value, text, name_for_logs, alt_locators=None):
    with allure.step(f"Input into {name_for_logs}: '{text}'"):
        try:
            elem = find_element_with_healing(driver, by, value, name_for_logs, alt_locators=alt_locators)
            try:
                elem.clear()
            except Exception:
                # if clear fails, try JS to set value to empty
                try:
                    driver.execute_script("arguments[0].value = '';", elem)
                except Exception:
                    pass
            try:
                elem.send_keys(text)
                allure.attach(driver.get_screenshot_as_png(), name=f"input_{name_for_logs}", attachment_type=allure.attachment_type.PNG)
                return
            except StaleElementReferenceException:
                elem = find_element_with_healing(driver, by, value, name_for_logs, alt_locators=alt_locators)
                elem.clear()
                elem.send_keys(text)
                allure.attach(driver.get_screenshot_as_png(), name=f"input_after_refind_{name_for_logs}", attachment_type=allure.attachment_type.PNG)
                return
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name=f"input_failed_{name_for_logs}", attachment_type=allure.attachment_type.PNG)
            png_path, html_path = save_artifacts_on_error(driver, f"input_failed_{name_for_logs}")
            raise

# Auto-fix logging: created helpers because POM file missing or mismatched
def log_autofix():
    with allure.step("auto-fix: created helper_login_mar_19_suce because POM mar_19_suce.py missing or incompatible"):
        allure.attach(json.dumps({"created_helper": "helper_login_mar_19_suce"}).encode(), name="autofix_login", attachment_type=allure.attachment_type.JSON)
    with allure.step("auto-fix: created helper_add_to_cart_mar_19_suce because POM mar_19_suce.py missing or incompatible"):
        allure.attach(json.dumps({"created_helper": "helper_add_to_cart_mar_19_suce"}).encode(), name="autofix_add_to_cart", attachment_type=allure.attachment_type.JSON)
    with allure.step("auto-fix: created helper_go_to_cart_and_checkout because POM mar_19_suce.py missing or incompatible"):
        allure.attach(json.dumps({"created_helper": "helper_go_to_cart_and_checkout"}).encode(), name="autofix_go_to_cart", attachment_type=allure.attachment_type.JSON)
    with allure.step("auto-fix: created helper_fill_checkout_info_mar_19_suce because POM mar_19_suce.py missing or incompatible"):
        allure.attach(json.dumps({"created_helper": "helper_fill_checkout_info_mar_19_suce"}).encode(), name="autofix_fill_checkout", attachment_type=allure.attachment_type.JSON)
    with allure.step("auto-fix: created helper_finish_checkout_mar_19_suce because POM mar_19_suce.py missing or incompatible"):
        allure.attach(json.dumps({"created_helper": "helper_finish_checkout_mar_19_suce"}).encode(), name="autofix_finish", attachment_type=allure.attachment_type.JSON)
    with allure.step("auto-fix: created helper_logout_mar_19_suce because POM mar_19_suce.py missing or incompatible"):
        allure.attach(json.dumps({"created_helper": "helper_logout_mar_19_suce"}).encode(), name="autofix_logout", attachment_type=allure.attachment_type.JSON)

@pytest.fixture(scope="function")
def driver():
    options = Options()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless=new")  # comment/uncomment as needed in CI
    drv = webdriver.Chrome(options=options)
    try:
        log_autofix()
        yield drv
    finally:
        try:
            drv.quit()
        except Exception:
            pass

def helper_login_mar_19_suce(driver, username, password):
    with allure.step("helper_login_mar_19_suce: perform login using site form"):
        try:
            # typical locators from recorded actions: user-name, password, login-button
            input_text(driver, By.ID, "user-name", username, "user-name", alt_locators=[(By.NAME, "user-name"), (By.XPATH, "//input[@placeholder='Username']")])
            input_text(driver, By.ID, "password", password, "password", alt_locators=[(By.NAME, "password"), (By.XPATH, "//input[@placeholder='Password']")])
            click_element(driver, By.ID, "login-button", "login-button", alt_locators=[(By.XPATH, "//input[@value='Login']"), (By.XPATH, "//button[contains(normalize-space(.),'Login')]")])
        except Exception as e:
            with allure.step("helper_login_mar_19_suce: failure, capturing artifacts"):
                png_path, html_path = save_artifacts_on_error(driver, "helper_login_failure")
                try:
                    allure.attach(open(html_path, "rb").read(), name="page_source_login_error", attachment_type=allure.attachment_type.HTML)
                except Exception:
                    pass
                allure.attach(driver.get_screenshot_as_png(), name="login_error", attachment_type=allure.attachment_type.PNG)
            raise

def helper_add_to_cart_mar_19_suce(driver, item_button_id="add-to-cart-sauce-labs-backpack"):
    with allure.step("helper_add_to_cart_mar_19_suce: add item to cart"):
        click_element(driver, By.ID, item_button_id, f"add-to-cart ({item_button_id})", alt_locators=[(By.XPATH, f"//button[contains(@id,'{item_button_id}')]"), (By.XPATH, f"//button[contains(normalize-space(.),'Add to cart') and contains(@id,'{item_button_id.split('add-to-cart-')[-1]}')]")])

def helper_go_to_cart_and_checkout(driver):
    with allure.step("helper_go_to_cart_and_checkout: go to cart then checkout"):
        try:
            click_element(driver, By.ID, "shopping_cart_container", "shopping_cart_container", alt_locators=[(By.XPATH, "//a[@class='shopping_cart_link']"), (By.XPATH, "//a[contains(@href,'cart.html')]")])
        except Exception:
            try:
                click_element(driver, By.XPATH, "//a[contains(@href,'cart.html')]", "cart_link_fallback")
            except Exception:
                raise
        click_element(driver, By.ID, "checkout", "checkout", alt_locators=[(By.XPATH, "//button[contains(normalize-space(),'Checkout')]"), (By.XPATH, "//input[@value='Checkout']")])

def helper_fill_checkout_info_mar_19_suce(driver, first="teast", last="test", postal="8756875"):
    with allure.step("helper_fill_checkout_info_mar_19_suce: fill name and postal code"):
        # Corrected IDs for Sauce Demo checkout info inputs
        input_text(driver, By.ID, "first-name", first, "first-name", alt_locators=[(By.NAME, "firstName"), (By.XPATH, "//input[@placeholder='First Name']")])
        input_text(driver, By.ID, "last-name", last, "last-name", alt_locators=[(By.NAME, "lastName"), (By.XPATH, "//input[@placeholder='Last Name']")])
        input_text(driver, By.ID, "postal-code", postal, "postal-code", alt_locators=[(By.NAME, "postalCode"), (By.XPATH, "//input[@placeholder='Zip/Postal Code']")])
        click_element(driver, By.ID, "continue", "continue", alt_locators=[(By.XPATH, "//input[@value='Continue']"), (By.XPATH, "//button[contains(normalize-space(),'Continue')]")])

def helper_finish_checkout_mar_19_suce(driver):
    with allure.step("helper_finish_checkout_mar_19_suce: finish checkout"):
        click_element(driver, By.ID, "finish", "finish", alt_locators=[(By.XPATH, "//button[contains(normalize-space(),'Finish')]"), (By.XPATH, "//input[@value='Finish']")])

def helper_logout_mar_19_suce(driver):
    with allure.step("helper_logout_mar_19_suce: logout via burger menu"):
        click_element(driver, By.ID, "react-burger-menu-btn", "react-burger-menu-btn", alt_locators=[(By.XPATH, "//button[contains(@id,'react-burger-menu-btn')]")])
        click_element(driver, By.ID, "logout_sidebar_link", "logout_sidebar_link", alt_locators=[(By.XPATH, "//a[contains(normalize-space(),'Logout')]")])

@pytest.mark.flaky(reruns=0)
def test_TC01_successful_login_and_checkout(driver):
    with allure.step("Start TC01 - Successful Login"):
        pass
    try:
        with allure.step("Open base URL"):
            driver.get(BASE_URL)
            WebDriverWait(driver, 8).until(EC.visibility_of_element_located((By.ID, "login-button")))
            allure.attach(driver.get_screenshot_as_png(), name="opened_homepage", attachment_type=allure.attachment_type.PNG)
        # Switch to new window if opened
        if len(driver.window_handles) > 1:
            with allure.step("Switching to new window as recorded"):
                switch_to_new_window(driver)
                allure.attach(driver.get_screenshot_as_png(), name="switched_window", attachment_type=allure.attachment_type.PNG)
        # Perform login using helper (POM missing so helper used)
        helper_login_mar_19_suce(driver, "standard_user", "secret_sauce")
        # After login, add item to cart
        helper_add_to_cart_mar_19_suce(driver, "add-to-cart-sauce-labs-backpack")
        # Go to cart and checkout
        helper_go_to_cart_and_checkout(driver)
        # Fill checkout info using recorded values
        helper_fill_checkout_info_mar_19_suce(driver, first="teast", last="test", postal="8756875")
        # Finish checkout
        helper_finish_checkout_mar_19_suce(driver)
        # Attach a screenshot after finishing
        allure.attach(driver.get_screenshot_as_png(), name="after_finish", attachment_type=allure.attachment_type.PNG)
        # Primary assertion: verify checkout complete container is visible (single primary assertion)
        with allure.step("Primary assertion: verify checkout completed page is displayed"):
            try:
                complete_elem = WebDriverWait(driver, 8).until(EC.visibility_of_element_located((By.ID, "checkout_complete_container")))
                assert complete_elem.is_displayed()
            except AssertionError:
                allure.attach(driver.get_screenshot_as_png(), name="assertion_failure", attachment_type=allure.attachment_type.PNG)
                png_path, html_path = save_artifacts_on_error(driver, "assertion_failure")
                try:
                    allure.attach(open(html_path, "rb").read(), name="page_source_on_failure", attachment_type=allure.attachment_type.HTML)
                except Exception:
                    pass
                raise
            except Exception:
                allure.attach(driver.get_screenshot_as_png(), name="element_lookup_failure", attachment_type=allure.attachment_type.PNG)
                png_path, html_path = save_artifacts_on_error(driver, "element_lookup_failure")
                try:
                    allure.attach(open(html_path, "rb").read(), name="page_source_failure", attachment_type=allure.attachment_type.HTML)
                except Exception:
                    pass
                pytest.fail("Primary assertion failed: checkout_complete_container not found or visible")
        # After successful flow, perform logout to cleanup state
        try:
            helper_logout_mar_19_suce(driver)
        except Exception:
            allure.attach(driver.get_screenshot_as_png(), name="logout_failed", attachment_type=allure.attachment_type.PNG)
    finally:
        with allure.step("Test TC01 finished (teardown will quit driver)"):
            try:
                allure.attach(driver.get_screenshot_as_png(), name="final_state", attachment_type=allure.attachment_type.PNG)
            except Exception:
                pass
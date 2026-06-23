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
    copied_password = ""

    driver.get(BASE_URL)
    attach_screenshot(driver, "page_loaded")

    with allure.step("Step 1: CLICK user-name"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "user-name")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_1_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_1")
            raise RuntimeError(f"Step 1 failed: {last_err}")
        attach_screenshot(driver, "step_1_done")

    with allure.step("Step 3: TYPE 'standard_user' user-name"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.presence_of_element_located((By.ID, "user-name")))
                el.clear()
                el.send_keys("standard_user")
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_3_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_3")
            raise RuntimeError(f"Step 3 failed: {last_err}")
        attach_screenshot(driver, "step_3_done")

    with allure.step("Step 4: TYPE 'secret_sacue' password"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.presence_of_element_located((By.ID, "password")))
                el.clear()
                el.send_keys("secret_sacue")
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_4_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_4")
            raise RuntimeError(f"Step 4 failed: {last_err}")
        attach_screenshot(driver, "step_4_done")

    with allure.step("Step 5: CLICK login-button"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_5_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_5")
            raise RuntimeError(f"Step 5 failed: {last_err}")
        attach_screenshot(driver, "step_5_done")

    with allure.step("Step 6: CLICK Password for all users: secret_sauce"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div[2]/div[2]/div/div[2]")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_6_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_6")
            raise RuntimeError(f"Step 6 failed: {last_err}")
        attach_screenshot(driver, "step_6_done")

    with allure.step("Step 7: COPY Password for all users: secret_sauce"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div/div/div[2]/div[2]/div/div[2]")))
                copied_password = el.text.strip()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_7_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_7")
            raise RuntimeError(f"Step 7 failed: {last_err}")
        attach_screenshot(driver, "step_7_done")

    with allure.step("Step 8: CLICK Epic sadface: Username and password do not match any user in this service"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div[2]/div")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_8_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_8")
            raise RuntimeError(f"Step 8 failed: {last_err}")
        attach_screenshot(driver, "step_8_done")

    with allure.step("Step 9: SHORTCUT_PASTE password (focus password field)"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "password")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_9_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_9")
            raise RuntimeError(f"Step 9 failed: {last_err}")
        attach_screenshot(driver, "step_9_done")

    with allure.step("Step 10: PASTE password into password field"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.presence_of_element_located((By.ID, "password")))
                el.clear()
                # If copied_password is empty, fallback to literal 'secret_sauce'
                paste_value = copied_password or "secret_sauce"
                el.send_keys(paste_value)
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_10_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_10")
            raise RuntimeError(f"Step 10 failed: {last_err}")
        attach_screenshot(driver, "step_10_done")

    with allure.step("Step 11: TYPE 'secret_sauce' password"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.presence_of_element_located((By.ID, "password")))
                el.clear()
                el.send_keys("secret_sauce")
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_11_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_11")
            raise RuntimeError(f"Step 11 failed: {last_err}")
        attach_screenshot(driver, "step_11_done")

    with allure.step("Step 12: CLICK login-button"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
                el.click()
                # wait for navigation to inventory
                wait.until(EC.url_contains("inventory.html"))
                attach_screenshot(driver, "navigated_to_inventory")
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_12_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_12")
            raise RuntimeError(f"Step 12 failed: {last_err}")
        attach_screenshot(driver, "step_12_done")

    with allure.step("Step 13: CLICK add-to-cart-sauce-labs-backpack"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-backpack")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_13_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_13")
            raise RuntimeError(f"Step 13 failed: {last_err}")
        attach_screenshot(driver, "step_13_done")

    with allure.step("Step 14: CLICK add-to-cart-sauce-labs-bike-light"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-bike-light")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_14_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_14")
            raise RuntimeError(f"Step 14 failed: {last_err}")
        attach_screenshot(driver, "step_14_done")

    with allure.step("Step 15: CLICK cart link (shopping_cart_link)"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "shopping_cart_link")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_15_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_15")
            raise RuntimeError(f"Step 15 failed: {last_err}")
        attach_screenshot(driver, "step_15_done")

    with allure.step("Step 16: CLICK cart link (shopping_cart_link) - ensure on cart page"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                # click again to ensure navigation, then wait for cart page
                el = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "shopping_cart_link")))
                el.click()
                wait.until(EC.url_contains("cart.html"))
                attach_screenshot(driver, "navigated_to_cart")
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_16_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_16")
            raise RuntimeError(f"Step 16 failed: {last_err}")
        attach_screenshot(driver, "step_16_done")

    with allure.step("Step 17: CLICK remove-sauce-labs-bike-light"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "remove-sauce-labs-bike-light")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_17_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_17")
            raise RuntimeError(f"Step 17 failed: {last_err}")
        attach_screenshot(driver, "step_17_done")

    with allure.step("Step 18: CLICK checkout"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "checkout")))
                el.click()
                wait.until(EC.url_contains("checkout-step-one.html"))
                attach_screenshot(driver, "navigated_to_checkout_step_one")
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_18_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_18")
            raise RuntimeError(f"Step 18 failed: {last_err}")
        attach_screenshot(driver, "step_18_done")

    with allure.step("Step 19: CLICK firstName (first-name)"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "first-name")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_19_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_19")
            raise RuntimeError(f"Step 19 failed: {last_err}")
        attach_screenshot(driver, "step_19_done")

    with allure.step("Step 21: TYPE 'test' firstName"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.presence_of_element_located((By.ID, "first-name")))
                el.clear()
                el.send_keys("test")
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_21_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_21")
            raise RuntimeError(f"Step 21 failed: {last_err}")
        attach_screenshot(driver, "step_21_done")

    with allure.step("Step 23: TYPE 'test' lastName"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.presence_of_element_located((By.ID, "last-name")))
                el.clear()
                el.send_keys("test")
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_23_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_23")
            raise RuntimeError(f"Step 23 failed: {last_err}")
        attach_screenshot(driver, "step_23_done")

    with allure.step("Step 24: TYPE '87687' postalCode"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.presence_of_element_located((By.ID, "postal-code")))
                el.clear()
                el.send_keys("87687")
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_24_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_24")
            raise RuntimeError(f"Step 24 failed: {last_err}")
        attach_screenshot(driver, "step_24_done")

    with allure.step("Step 25: CLICK continue"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "continue")))
                el.click()
                wait.until(EC.url_contains("checkout-step-two.html"))
                attach_screenshot(driver, "navigated_to_checkout_step_two")
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_25_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_25")
            raise RuntimeError(f"Step 25 failed: {last_err}")
        attach_screenshot(driver, "step_25_done")

    with allure.step("Step 26: CLICK finish"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "finish")))
                el.click()
                wait.until(EC.url_contains("checkout-complete.html"))
                attach_screenshot(driver, "navigated_to_checkout_complete")
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_26_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_26")
            raise RuntimeError(f"Step 26 failed: {last_err}")
        attach_screenshot(driver, "step_26_done")

    with allure.step("Step 27: CLICK back-to-products"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "back-to-products")))
                el.click()
                wait.until(EC.url_contains("inventory.html"))
                attach_screenshot(driver, "navigated_to_inventory_after_back")
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_27_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_27")
            raise RuntimeError(f"Step 27 failed: {last_err}")
        attach_screenshot(driver, "step_27_done")

    with allure.step("Step 28: CLICK react-burger-menu-btn"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "react-burger-menu-btn")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_28_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_28")
            raise RuntimeError(f"Step 28 failed: {last_err}")
        attach_screenshot(driver, "step_28_done")

    with allure.step("Step 29: CLICK inventory_sidebar_link (All Items)"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "inventory_sidebar_link")))
                el.click()
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_29_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_29")
            raise RuntimeError(f"Step 29 failed: {last_err}")
        attach_screenshot(driver, "step_29_done")

    with allure.step("Step 30: CLICK logout_sidebar_link"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, "logout_sidebar_link")))
                el.click()
                wait.until(EC.url_contains(BASE_URL))
                attach_screenshot(driver, "navigated_to_login_after_logout")
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_30_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_30")
            raise RuntimeError(f"Step 30 failed: {last_err}")
        attach_screenshot(driver, "step_30_done")

    with allure.step("Step 31: TYPE 'Logout' logout_sidebar_link (final interaction)"):
        attempt = 0
        last_err = None
        while attempt < 2:
            try:
                # attempt to locate logout link on the page; if not present, just pass
                el = wait.until(EC.presence_of_element_located((By.ID, "logout_sidebar_link")))
                # not an input; perform a click as a sensible final interaction
                try:
                    el.click()
                except Exception:
                    pass
                break
            except Exception as e:
                last_err = e
                attach_screenshot(driver, f"retry_step_31_attempt_{attempt}")
                time.sleep(0.5)
                attempt += 1
        if attempt == 2:
            attach_screenshot(driver, "failed_step_31")
            raise RuntimeError(f"Step 31 failed: {last_err}")
        attach_screenshot(driver, "step_31_done")

    # Final assertion
    with allure.step("Final Assertion"):
        el = wait.until(EC.visibility_of_element_located((By.ID, "user-name")))
        assert el.is_displayed(), "Expected: login page with username field visible"
        attach_screenshot(driver, "assertion_passed")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
import pytest
import allure
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from output.page_file_generator.saucedemo_login_details import saucedemo_login_details

# Constants
BASE_URL = "https://www.saucedemo.com/"
ALLURE_RESULTS_DIR = "./allure-results"

# Helper Functions
def click_via_locator(driver, locator):
    try:
        element = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(locator))
        element.click()
    except Exception as e:
        raise AssertionError(f"Failed to click on element with locator {locator}: {e}")

def enter_text_via_locator(driver, locator, text):
    try:
        element = WebDriverWait(driver, 5).until(EC.visibility_of_element_located(locator))
        element.clear()
        element.send_keys(text)
    except Exception as e:
        raise AssertionError(f"Failed to enter text '{text}' in element with locator {locator}: {e}")

# Reusable Flows
def login(driver, username, password):
    with allure.step("Enter username"):
        saucedemo_login_details.enter_username(driver, username)
    with allure.step("Enter password"):
        saucedemo_login_details.enter_password(driver, password)
    with allure.step("Click login button"):
        saucedemo_login_details.click_login_button(driver)

# Test Setup and Teardown
@pytest.fixture(scope="function")
def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    driver.get(BASE_URL)
    yield driver
    driver.quit()

# Test Case
@allure.feature("SauceDemo Login")
@allure.story("TC01 - Successful Login with Valid Credentials")
@allure.severity(allure.severity_level.CRITICAL)
def test_successful_login(setup_driver):
    driver = setup_driver

    # Step 1: Login
    with allure.step("Perform login with valid credentials"):
        login(driver, "standard_user", "secret_sauce")

    # Step 2: Add item to cart
    with allure.step("Add Sauce Labs Backpack to cart"):
        click_via_locator(driver, (By.ID, "add-to-cart-sauce-labs-backpack"))

    # Step 3: Proceed to checkout
    with allure.step("Proceed to checkout"):
        click_via_locator(driver, (By.ID, "shopping_cart_container"))
        click_via_locator(driver, (By.ID, "checkout"))

    # Step 4: Enter checkout information
    with allure.step("Enter checkout information"):
        enter_text_via_locator(driver, (By.ID, "first-name"), "test")
        enter_text_via_locator(driver, (By.ID, "last-name"), "test")
        enter_text_via_locator(driver, (By.ID, "postal-code"), "56564")
        click_via_locator(driver, (By.ID, "continue"))

    # Step 5: Finish checkout
    with allure.step("Finish checkout"):
        click_via_locator(driver, (By.ID, "finish"))

    # Assertion
    with allure.step("Verify checkout completion"):
        success_message = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "complete-header"))
        )
        assert success_message.text == "THANK YOU FOR YOUR ORDER", "Checkout was not successful"

    # Step 6: Logout
    with allure.step("Logout from the application"):
        click_via_locator(driver, (By.ID, "react-burger-menu-btn"))
        click_via_locator(driver, (By.ID, "logout_sidebar_link"))
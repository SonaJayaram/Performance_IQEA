import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import allure
from allure_commons.types import AttachmentType
from output.page_file_generator.jan_sauce_demo_login import jan_sauce_demo_login

@pytest.fixture(scope="function")
def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.saucedemo.com/")
    login_page = jan_sauce_demo_login(driver)
    yield driver, login_page
    driver.quit()

def helper_click_element(element):
    with allure.step(f"Clicking on element: {element}"):
        try:
            element.click()
        except Exception as e:
            raise e

def helper_enter_text(element, text):
    with allure.step(f"Entering text '{text}' into element: {element}"):
        try:
            element.clear()
            element.send_keys(text)
        except Exception as e:
            raise e

def test_successful_login(setup_driver):
    driver, login_page = setup_driver
    with allure.step("Test Case: TC01 - Successful Login"):
        try:
            with allure.step("Enter username"):
                username_input = login_page.get_user_name_input()
                helper_enter_text(username_input, "standard_user")
            with allure.step("Enter password"):
                password_input = login_page.get_password_input()
                helper_enter_text(password_input, "secret_sauce")
            with allure.step("Click login button"):
                login_button = login_page.get_login_button()
                helper_click_element(login_button)
            with allure.step("Verify successful login by checking the presence of the add-to-cart button"):
                add_to_cart_button = login_page.get_add_to_cart_button()
                assert add_to_cart_button.is_displayed(), "Add to cart button is not displayed. Login might have failed."
        except AssertionError as e:
            allure.attach(driver.get_screenshot_as_png(), name="assertion_failure", attachment_type=AttachmentType.PNG)
            allure.attach(driver.page_source, name="page_source", attachment_type=AttachmentType.HTML)
            raise e

def test_login_with_invalid_username(setup_driver):
    driver, login_page = setup_driver
    with allure.step("Test Case: TC02 - Login with Invalid Username"):
        try:
            with allure.step("Enter invalid username"):
                username_input = login_page.get_user_name_input()
                helper_enter_text(username_input, "invalid_user")
            with allure.step("Enter password"):
                password_input = login_page.get_password_input()
                helper_enter_text(password_input, "secret_sauce")
            with allure.step("Click login button"):
                login_button = login_page.get_login_button()
                helper_click_element(login_button)
            with allure.step("Verify error message is displayed"):
                error_message = login_page.get_element(By.XPATH, "//h3[@data-test='error']")
                assert error_message.is_displayed(), "Error message is not displayed for invalid login."
        except AssertionError as e:
            allure.attach(driver.get_screenshot_as_png(), name="assertion_failure", attachment_type=AttachmentType.PNG)
            allure.attach(driver.page_source, name="page_source", attachment_type=AttachmentType.HTML)
            raise e
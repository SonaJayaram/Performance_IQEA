import pytest
import allure
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from output.page_file_generator.sauce_demo_new_login import sauce_demo_new_login

@pytest.fixture(scope="function")
def driver():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)
    login_page = sauce_demo_new_login(driver)
    yield driver, login_page
    driver.quit()

def helper_enter_text(element, text, step_name):
    with allure.step(step_name):
        try:
            element.clear()
            element.send_keys(text)
        except Exception as e:
            raise e

def helper_click_element(element, step_name):
    with allure.step(step_name):
        try:
            element.click()
        except ElementClickInterceptedException:
            element.parent.execute_script("arguments[0].click();", element)
        except Exception as e:
            raise e

def test_TC01_successful_login(driver):
    driver, login_page = driver
    base_url = "https://www.saucedemo.com/"
    driver.get(base_url)
    with allure.step("Enter username"):
        user_name_input = login_page.get_user_name_input()
        helper_enter_text(user_name_input, "standard_user", "Enter username")
    with allure.step("Enter password"):
        password_input = login_page.get_password_input()
        helper_enter_text(password_input, "secret_sauce", "Enter password")
    with allure.step("Click login button"):
        login_button = login_page.get_login_button()
        helper_click_element(login_button, "Click login button")
    with allure.step("Verify successful login"):
        try:
            WebDriverWait(driver, 10).until(EC.url_contains("inventory.html"))
            assert "inventory.html" in driver.current_url
        except Exception as e:
            raise e

def test_TC03_login_with_empty_username(driver):
    driver, login_page = driver
    base_url = "https://www.saucedemo.com/"
    driver.get(base_url)
    with allure.step("Leave username empty and enter password"):
        password_input = login_page.get_password_input()
        helper_enter_text(password_input, "secret_sauce", "Enter password")
    with allure.step("Click login button"):
        login_button = login_page.get_login_button()
        helper_click_element(login_button, "Click login button")
    with allure.step("Verify error message for empty username"):
        try:
            error_message = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//h3[@data-test='error']"))).text
            assert "Username is required" in error_message
        except Exception as e:
            raise e

def test_TC04_login_with_empty_password(driver):
    driver, login_page = driver
    base_url = "https://www.saucedemo.com/"
    driver.get(base_url)
    with allure.step("Enter username and leave password empty"):
        user_name_input = login_page.get_user_name_input()
        helper_enter_text(user_name_input, "standard_user", "Enter username")
    with allure.step("Click login button"):
        login_button = login_page.get_login_button()
        helper_click_element(login_button, "Click login button")
    with allure.step("Verify error message for empty password"):
        try:
            error_message = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//h3[@data-test='error']"))).text
            assert "Password is required" in error_message
        except Exception as e:
            raise e
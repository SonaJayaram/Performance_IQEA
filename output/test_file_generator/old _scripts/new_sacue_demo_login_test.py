from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pytest
from output.page_file_generator.saucedemo_login_details import SauceDemoLoginDetails

@pytest.fixture(scope="function")
def driver():
    # Setup WebDriver
    driver = webdriver.Chrome()
    yield driver
    driver.quit()

@pytest.fixture(scope="function")
def login_page(driver):
    # Instantiate the Page Object
    return SauceDemoLoginDetails(driver)

def test_successful_login_with_valid_credentials(driver, login_page):
    # Launch the application
    driver.get("https://www.saucedemo.com/")

    # Enter valid username
    login_page.enter_username("standard_user")

    # Enter valid password
    login_page.enter_password("secret_sauce")

    # Click the login button
    login_page.click_login_button()

    # Assert successful login by checking the presence of a specific element on the home page
    assert driver.find_element(By.CLASS_NAME, "inventory_list").is_displayed(), "Login failed or inventory list not displayed."

def test_login_with_empty_password(driver, login_page):
    # Launch the application
    driver.get("https://www.saucedemo.com/")

    # Enter valid username
    login_page.enter_username("standard_user")

    # Leave the password field empty
    login_page.enter_password("")

    # Click the login button
    login_page.click_login_button()

    # Assert error message is displayed
    error_message = driver.find_element(By.CLASS_NAME, "error-message-container").text
    assert "Epic sadface: Password is required" in error_message, "Expected error message not displayed for empty password."

def test_login_with_empty_username(driver, login_page):
    # Launch the application
    driver.get("https://www.saucedemo.com/")

    # Leave the username field empty
    login_page.enter_username("")

    # Enter valid password
    login_page.enter_password("secret_sauce")

    # Click the login button
    login_page.click_login_button()

    # Assert error message is displayed
    error_message = driver.find_element(By.CLASS_NAME, "error-message-container").text
    assert "Epic sadface: Username is required" in error_message, "Expected error message not displayed for empty username."
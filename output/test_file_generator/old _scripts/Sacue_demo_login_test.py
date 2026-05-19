import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from output.page_file_generator.old_files.saucedemo_login_details import LoginPage

@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    driver.get("https://www.saucedemo.com/")
    driver.maximize_window()
    yield driver
    driver.quit()

# Helper method for login
def login(driver, username, password):
    login_page = LoginPage(driver)
    # Enter username
    login_page.enter_username(username)
    # Enter password
    login_page.enter_password(password)
    # Click login button
    login_page.click_login_button()

def logout(driver):
    login_page = LoginPage(driver)
    # Click menu button
    login_page.click_menu_button()
    # Click logout link
    login_page.click_logout_link()

# Test Case: Blank Password Test
def test_blank_password(driver):
    login_page = LoginPage(driver)
    # Enter username
    login_page.enter_username("standard_user")
    # Leave password blank and click login
    login_page.click_login_button()
    # Validate error message for blank password
    error_message = driver.find_element(By.XPATH, "//h3[@data-test='error']").text
    assert error_message == "Epic sadface: Password is required", "Error message does not match."

# Test Case: Blank Username Test
def test_blank_username(driver):
    login_page = LoginPage(driver)
    # Enter password
    login_page.enter_password("secret_sauce")
    # Leave username blank and click login
    login_page.click_login_button()
    # Validate error message for blank username
    error_message = driver.find_element(By.XPATH, "//h3[@data-test='error']").text
    assert error_message == "Epic sadface: Username is required", "Error message does not match."

# Test Case: Incorrect Password Test
def test_incorrect_password(driver):
    login_page = LoginPage(driver)
    # Enter username
    login_page.enter_username("standard_user")
    # Enter incorrect password
    login_page.enter_password("wrong_password")
    # Click login button
    login_page.click_login_button()
    # Validate error message for incorrect password
    error_message = driver.find_element(By.XPATH, "//h3[@data-test='error']").text
    assert error_message == "Epic sadface: Username and password do not match any user in this service", "Error message does not match."

# Test Case: Invalid Username Login Test
def test_invalid_username(driver):
    login_page = LoginPage(driver)
    # Enter invalid username
    login_page.enter_username("invalid_user")
    # Enter password
    login_page.enter_password("secret_sauce")
    # Click login button
    login_page.click_login_button()
    # Validate error message for invalid username
    error_message = driver.find_element(By.XPATH, "//h3[@data-test='error']").text
    assert error_message == "Epic sadface: Username and password do not match any user in this service", "Error message does not match."

# Test Case: Locked-Out User Test
def test_locked_out_user(driver):
    login_page = LoginPage(driver)
    # Enter locked-out username
    login_page.enter_username("locked_out_user")
    # Enter password
    login_page.enter_password("secret_sauce")
    # Click login button
    login_page.click_login_button()
    # Validate error message for locked-out user
    error_message = driver.find_element(By.XPATH, "//h3[@data-test='error']").text
    assert error_message == "Epic sadface: Sorry, this user has been locked out.", "Error message does not match."

# Test Case: Performance User Test
def test_performance_user(driver):
    login(driver, "performance_glitch_user", "secret_sauce")
    # Validate successful login by checking URL
    assert driver.current_url == "https://www.saucedemo.com/inventory.html", "Login failed for performance_user."
    logout(driver)

# Test Case: Problem User Test
def test_problem_user(driver):
    login(driver, "problem_user", "secret_sauce")
    # Validate successful login by checking URL
    assert driver.current_url == "https://www.saucedemo.com/inventory.html", "Login failed for problem_user."
    logout(driver)

# Test Case: UI Elements Test
def test_ui_elements(driver):
    # Validate that all expected UI elements are present on login page
    assert driver.find_element(By.ID, "user-name").is_displayed(), "Username field is not displayed."
    assert driver.find_element(By.ID, "password").is_displayed(), "Password field is not displayed."
    assert driver.find_element(By.ID, "login-button").is_displayed(), "Login button is not displayed."

# Test Case: Valid Login Standard User
def test_valid_login_standard_user(driver):
    login(driver, "standard_user", "secret_sauce")
    # Validate successful login by checking URL
    assert driver.current_url == "https://www.saucedemo.com/inventory.html", "Login failed for standard_user."
    logout(driver)
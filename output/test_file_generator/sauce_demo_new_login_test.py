import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import allure
from allure_commons.types import AttachmentType
from output.page_file_generator.sauce_demo_new_login import sauce_demo_new_login


@pytest.fixture(scope="function")
def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    pom = sauce_demo_new_login(driver)
    yield driver, pom
    driver.quit()


def helper_login_with_credentials(driver, pom, username, password):

    with allure.step("Enter username"):
        try:
            pom.get_user_name_input().clear()
            pom.get_user_name_input().send_keys(username)
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name="error_enter_username", attachment_type=AttachmentType.PNG)
            raise e

    with allure.step("Enter password"):
        try:
            pom.get_password_input().clear()
            pom.get_password_input().send_keys(password)
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name="error_enter_password", attachment_type=AttachmentType.PNG)
            raise e

    with allure.step("Click login button"):
        try:
            pom.get_login_button().click()
        except Exception:
            driver.execute_script("arguments[0].click();", pom.get_login_button())


@pytest.mark.usefixtures("setup_driver")
def test_tc05_successful_login(setup_driver):
    driver, pom = setup_driver
    driver.get("https://www.saucedemo.com/")

    helper_login_with_credentials(driver, pom, "standard_user", "secret_sauce")

    with allure.step("Verify successful login"):
        try:
            WebDriverWait(driver, 10).until(EC.url_contains("inventory.html"))
            assert "inventory.html" in driver.current_url
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name="login_failure", attachment_type=AttachmentType.PNG)
            raise e


@pytest.mark.usefixtures("setup_driver")
def test_tc04_login_with_empty_password(setup_driver):
    driver, pom = setup_driver
    driver.get("https://www.saucedemo.com/")

    helper_login_with_credentials(driver, pom, "standard_user", "")

    with allure.step("Verify error message"):
        msg = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(("xpath", "//h3[@data-test='error']"))
        ).text
        assert "Password is required" in msg


@pytest.mark.usefixtures("setup_driver")
def test_tc03_login_with_empty_username(setup_driver):
    driver, pom = setup_driver
    driver.get("https://www.saucedemo.com/")

    helper_login_with_credentials(driver, pom, "", "secret_sauce")

    with allure.step("Verify error message"):
        msg = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(("xpath", "//h3[@data-test='error']"))
        ).text
        assert "Username is required" in msg

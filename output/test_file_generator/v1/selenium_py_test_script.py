from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import allure
import pytest
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from output.page_file_generator.Equfix_home_page_playwright import EqufixHomePagePlaywright
from output.page_file_generator.Equfix_Place_On_Alert_playwright import EqufixPlaceOnAlertPlaywright

@pytest.fixture(scope="function")
def setup():
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/")
    yield driver
    driver.quit()

@allure.title("TC01 - Place an Alert - Successful Form Submission")
def test_place_alert_successful_submission(setup):
    driver = setup
    home_page = EqufixHomePagePlaywright(driver)
    alert_page = EqufixPlaceOnAlertPlaywright(driver)

    with allure.step("Click on 'Place an Alert' button"):
        home_page.clickPlaceAnAlert()
        allure.attach(driver.get_screenshot_as_png(), name="Place_Alert_Clicked", attachment_type=allure.attachment_type.PNG)

    with allure.step("Switch to new window for alert form"):
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        driver.switch_to.window(driver.window_handles[1])
        allure.attach(driver.get_screenshot_as_png(), name="Switched_to_Alert_Form", attachment_type=allure.attachment_type.PNG)

    with allure.step("Fill in the alert form"):
        alert_page.fillFirstName("test")
        alert_page.fillLastName("test")
        alert_page.fillSSN("***-**-6686")
        alert_page.fillPhoneNumber("786-876-****")
        alert_page.fillDOB("04/22/1990")
        alert_page.fillAddress("test")
        alert_page.fillCity("test")
        alert_page.fillAddressLine2("test")
        alert_page.selectState("Alaska")
        alert_page.fillZip("78686")
        allure.attach(driver.get_screenshot_as_png(), name="Form_Filled", attachment_type=allure.attachment_type.PNG)

    with allure.step("Submit the alert form"):
        alert_page.clickContinueButton()
        allure.attach(driver.get_screenshot_as_png(), name="Form_Submitted", attachment_type=allure.attachment_type.PNG)

    with allure.step("Verify successful submission"):
        success_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Your alert has been successfully placed')]"))
        )
        assert success_message.is_displayed(), "Success message not displayed"
        allure.attach(driver.get_screenshot_as_png(), name="Success_Message", attachment_type=allure.attachment_type.PNG)
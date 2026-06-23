import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import allure
from allure_commons.types import AttachmentType
from output.page_file_generator.mckesson_form import mckesson_form

@pytest.fixture(scope="function")
def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    form_page = mckesson_form(driver)
    yield driver, form_page
    driver.quit()



def helper_select_state(driver, state_value):
    with allure.step(f"Select state: {state_value}"):
        allure.attach(driver.get_screenshot_as_png(), name="before-select-state", attachment_type=AttachmentType.PNG)
        state_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//select[@id='State']"))
        )
        try:
            state_dropdown.click()
        except Exception:
            driver.execute_script("arguments[0].click();", state_dropdown)
        state_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//option[@value='{state_value}']"))
        )
        try:
            state_option.click()
        except Exception:
            driver.execute_script("arguments[0].click();", state_option)
        allure.attach(driver.get_screenshot_as_png(), name="after-select-state", attachment_type=AttachmentType.PNG)

def helper_select_checkbox(driver, checkbox_index):
    with allure.step(f"Select checkbox index: {checkbox_index}"):
        allure.attach(driver.get_screenshot_as_png(), name="before-select-checkbox", attachment_type=AttachmentType.PNG)
        checkbox = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//input[@id='mktoCheckbox_23066_{checkbox_index}']"))
        )
        try:
            checkbox.click()
        except Exception:
            driver.execute_script("arguments[0].click();", checkbox)
        allure.attach(driver.get_screenshot_as_png(), name="after-select-checkbox", attachment_type=AttachmentType.PNG)

def helper_select_radio(driver, radio_index):
    with allure.step(f"Select radio index: {radio_index}"):
        allure.attach(driver.get_screenshot_as_png(), name="before-select-radio", attachment_type=AttachmentType.PNG)
        radio = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//input[@id='mktoRadio_23069_{radio_index}']"))
        )
        try:
            radio.click()
        except Exception:
            driver.execute_script("arguments[0].click();", radio)
        allure.attach(driver.get_screenshot_as_png(), name="after-select-radio", attachment_type=AttachmentType.PNG)

@pytest.mark.usefixtures("setup_driver")
def test_successful_form_submission(setup_driver):
    driver, form_page = setup_driver

    with allure.step("Navigate to the form page"):
        driver.get("https://www.mckesson.com/business-solutions/our-businesses/specialized-care-pharmacies/")
        allure.attach(driver.get_screenshot_as_png(), name="form-page", attachment_type=AttachmentType.PNG)

    with allure.step("Fill out the form"):
        form_page.get_first_name_input().send_keys("test")
        form_page.get_last_name_input().send_keys("test")
        form_page.get_email_input().send_keys("test@test.com")
        form_page.get_company_input().send_keys("test")
        form_page.get_mktowebsite_input().send_keys("www.test.com")
        form_page.get_phone_input().send_keys("876876687686")
        form_page.get_title_input().send_keys("test")
        form_page.get_city_input().send_keys("test")
        helper_select_state(driver, "TN")
        helper_select_checkbox(driver, 0)
        helper_select_checkbox(driver, 1)
        helper_select_checkbox(driver, 2)
        helper_select_checkbox(driver, 3)
        helper_select_radio(driver, 0)
        form_page.get_primary_customer_number_input().send_keys("test")

    with allure.step("Submit the form"):
        allure.attach(driver.get_screenshot_as_png(), name="before-submit", attachment_type=AttachmentType.PNG)
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@class='mktoButton']"))
        )
        try:
            submit_button.click()
        except Exception:
            driver.execute_script("arguments[0].click();", submit_button)
        allure.attach(driver.get_screenshot_as_png(), name="after-submit", attachment_type=AttachmentType.PNG)

    with allure.step("Verify successful submission"):
        try:
            success_message = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), 'Thank you for your submission')]"))
            )
            assert success_message.is_displayed(), "Success message not displayed"
            allure.attach(driver.get_screenshot_as_png(), name="success-message", attachment_type=AttachmentType.PNG)
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name="failure-screenshot", attachment_type=AttachmentType.PNG)
            allure.attach(driver.page_source, name="failure-page-source", attachment_type=AttachmentType.HTML)
            raise AssertionError("Form submission failed") from e
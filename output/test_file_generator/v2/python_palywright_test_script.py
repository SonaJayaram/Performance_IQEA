from playwright.sync_api import sync_playwright
import allure
import pytest
from output.page_file_generator.Equfix_home_page_playwright import Equfix_home_page_playwright

@pytest.fixture(scope="function")
def setup_teardown():
    with sync_playwright() as p:
        browser = p.webkit.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        yield page
        browser.close()

def test_tc01_place_an_alert_successful_form_submission(setup_teardown):
    page = setup_teardown
    equfix_home_page = Equfix_home_page_playwright(page)

    with allure.step("Navigate to Equifax Fraud Alert Page"):
        page.goto("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/")
        allure.attach(page.screenshot(), name="Navigate to Equifax Fraud Alert Page", attachment_type=allure.attachment_type.PNG)

    with allure.step("Update banner description"):
        equfix_home_page.update_banner_description("Equifax and its partners use Cookies and similar technologies as necessary to provide digital services and for advertising and targeting, analytics and performance, and functionality and personalization purposes. For more information, please review our Privacy Statement.")
        allure.attach(page.screenshot(), name="Update banner description", attachment_type=allure.attachment_type.PNG)

    with allure.step("Close banner"):
        equfix_home_page.close_banner()
        allure.attach(page.screenshot(), name="Close banner", attachment_type=allure.attachment_type.PNG)

    with allure.step("Click on Place an Alert"):
        equfix_home_page.click_place_an_alert()
        allure.attach(page.screenshot(), name="Click on Place an Alert", attachment_type=allure.attachment_type.PNG)

    with allure.step("Switch to new window for personal info"):
        new_page = equfix_home_page.switch_to_new_window()
        allure.attach(new_page.screenshot(), name="Switched to new window", attachment_type=allure.attachment_type.PNG)

    with allure.step("Fill personal information form"):
        equfix_home_page.fill_personal_info(
            first_name="test",
            last_name="test",
            ssn="***-**-6686",
            phone_number="786-876-****",
            dob="04/22/1990",
            address="test",
            city="test",
            address_line2="test",
            state="Alaska",
            zip_code="78686"
        )
        allure.attach(new_page.screenshot(), name="Filled personal information form", attachment_type=allure.attachment_type.PNG)

def test_tc04_place_an_alert_empty_ssn_validation(setup_teardown):
    page = setup_teardown
    equfix_home_page = Equfix_home_page_playwright(page)

    with allure.step("Navigate to Equifax Fraud Alert Page"):
        page.goto("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/")
        allure.attach(page.screenshot(), name="Navigate to Equifax Fraud Alert Page", attachment_type=allure.attachment_type.PNG)

    with allure.step("Click on Place an Alert"):
        equfix_home_page.click_place_an_alert()
        allure.attach(page.screenshot(), name="Click on Place an Alert", attachment_type=allure.attachment_type.PNG)

    with allure.step("Switch to new window for personal info"):
        new_page = equfix_home_page.switch_to_new_window()
        allure.attach(new_page.screenshot(), name="Switched to new window", attachment_type=allure.attachment_type.PNG)

    with allure.step("Attempt to submit form with empty SSN"):
        equfix_home_page.fill_personal_info(
            first_name="test",
            last_name="test",
            ssn="",
            phone_number="786-876-****",
            dob="04/22/1990",
            address="test",
            city="test",
            address_line2="test",
            state="Alaska",
            zip_code="78686"
        )
        allure.attach(new_page.screenshot(), name="Attempted to submit form with empty SSN", attachment_type=allure.attachment_type.PNG)

    with allure.step("Validate error message for empty SSN"):
        error_message = new_page.locator("xpath=//div[contains(text(), 'SSN is required')]").text_content()
        assert error_message == "SSN is required", "Error message for empty SSN is not displayed correctly"
        allure.attach(new_page.screenshot(), name="Validated error message for empty SSN", attachment_type=allure.attachment_type.PNG)

def test_tc04_place_alert_invalid_phone_number(setup_teardown):
    page = setup_teardown
    equfix_home_page = Equfix_home_page_playwright(page)

    with allure.step("Navigate to Equifax Fraud Alert Page"):
        page.goto("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/")
        allure.attach(page.screenshot(), name="Navigate to Equifax Fraud Alert Page", attachment_type=allure.attachment_type.PNG)

    with allure.step("Click on Place an Alert"):
        equfix_home_page.click_place_an_alert()
        allure.attach(page.screenshot(), name="Click on Place an Alert", attachment_type=allure.attachment_type.PNG)

    with allure.step("Switch to new window for personal info"):
        new_page = equfix_home_page.switch_to_new_window()
        allure.attach(new_page.screenshot(), name="Switched to new window", attachment_type=allure.attachment_type.PNG)

    with allure.step("Attempt to submit form with invalid phone number"):
        equfix_home_page.fill_personal_info(
            first_name="test",
            last_name="test",
            ssn="***-**-6686",
            phone_number="invalid_phone",
            dob="04/22/1990",
            address="test",
            city="test",
            address_line2="test",
            state="Alaska",
            zip_code="78686"
        )
        allure.attach(new_page.screenshot(), name="Attempted to submit form with invalid phone number", attachment_type=allure.attachment_type.PNG)

    with allure.step("Validate error message for invalid phone number"):
        error_message = new_page.locator("xpath=//div[contains(text(), 'Invalid phone number')]").text_content()
        assert error_message == "Invalid phone number", "Error message for invalid phone number is not displayed correctly"
        allure.attach(new_page.screenshot(), name="Validated error message for invalid phone number", attachment_type=allure.attachment_type.PNG)
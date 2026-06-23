import os
import time
import pytest
import allure
from playwright.sync_api import sync_playwright
from output.page_file_generator.Sfdc_login import Sfdc_login
from output.page_file_generator.sfdc_otp import sfdc_otp
from output.page_file_generator.sfdc_homepage import sfdc_homepage
from output.page_file_generator.sfdc_contact_new import sfdc_contact_new

# Constants
DEFAULT_WAIT = 5
EXPLICIT_WAIT = 10
RETRY_ATTEMPTS = 1
HEADLESS = os.environ.get("HEADLESS", "false").lower() in ("1", "true", "yes")

# Create allure-results folder
os.makedirs("allure-results", exist_ok=True)

@pytest.fixture(scope="function")
def setup_playwright():
    with sync_playwright() as playwright:
        browser = playwright.webkit.launch()
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            java_script_enabled=True,
            ignore_https_errors=True,
            viewport={"width": 1400, "height": 900}
        )
        page = context.new_page()
        yield page
        context.close()
        browser.close()

def safe_goto(page, url, timeout=EXPLICIT_WAIT * 1000):
    with allure.step(f"Navigating to URL: {url}"):
        for attempt in range(RETRY_ATTEMPTS):
            try:
                page.goto(url, timeout=timeout)
                return
            except Exception as e:
                if attempt < RETRY_ATTEMPTS - 1:
                    time.sleep(0.5)
                else:
                    allure.attach(page.screenshot(), name="goto_failure", attachment_type=allure.attachment_type.PNG)
                    allure.attach(page.content(), name="page_html", attachment_type=allure.attachment_type.HTML)
                    raise e

def helper_click_with_healing(page, locator, alt_selector=None):
    with allure.step(f"Clicking on element: {locator}"):
        try:
            page.locator(locator).click()
        except Exception as e:
            allure.attach(page.screenshot(), name="click_failure", attachment_type=allure.attachment_type.PNG)
            allure.attach(page.content(), name="page_html", attachment_type=allure.attachment_type.HTML)
            time.sleep(0.5)
            try:
                page.locator(locator).click()
            except Exception as e2:
                if alt_selector:
                    with allure.step(f"Healing: Trying alternative selector: {alt_selector}"):
                        try:
                            page.locator(alt_selector).click()
                            return
                        except Exception as e3:
                            allure.attach(page.screenshot(), name="alt_click_failure", attachment_type=allure.attachment_type.PNG)
                            allure.attach(page.content(), name="page_html", attachment_type=allure.attachment_type.HTML)
                            raise e3
                else:
                    raise e2

@pytest.mark.parametrize("test_case_name", ["TC05 - Create New Contact (Positive)"])
def test_create_new_contact_positive(setup_playwright, test_case_name):
    page = setup_playwright
    base_url = "https://mindful-shark-fv3y29-dev-ed.trailblaze.lightning.force.com/"
    
    safe_goto(page, base_url)
    allure.attach(page.screenshot(), name="login_page", attachment_type=allure.attachment_type.PNG)
    
    login_page = Sfdc_login(page)
    with allure.step("Logging into Salesforce"):
        login_page.enter_text("username_locator", "[USERNAME]")
        login_page.enter_text("password_locator", "[PASSWORD]")
        login_page.click_element("login_button_locator")
        allure.attach(page.screenshot(), name="after_login", attachment_type=allure.attachment_type.PNG)
    
    with allure.step("Handling OTP Verification"):
        with page.expect_popup() as popup_info:
            otp_page = sfdc_otp(page)
            otp_page.enter_text("verification_code_locator", "[VERIFICATION_CODE]")
            otp_page.click_element("verify_button_locator")
        new_page = popup_info.value
        new_page.bring_to_front()
        allure.attach(new_page.screenshot(), name="otp_verification", attachment_type=allure.attachment_type.PNG)
    
    home_page = sfdc_homepage(new_page)
    with allure.step("Navigating to Contacts Tab"):
        home_page.click_contacts_tab()
        allure.attach(new_page.screenshot(), name="contacts_tab", attachment_type=allure.attachment_type.PNG)
    
    contact_page = sfdc_contact_new(new_page)
    with allure.step("Creating a New Contact"):
        contact_page.click_new_button()
        contact_page.enter_last_name("[CONTACT_LAST_NAME]")
        contact_page.enter_email("[CONTACT_EMAIL]")
        contact_page.enter_assistant_name("[ASSISTANT_NAME]")
        contact_page.enter_bio("[BIO]")
        contact_page.enter_assistant_phone("[ASSISTANT_PHONE]")
        contact_page.click_save_edit_button()
        allure.attach(new_page.screenshot(), name="new_contact_created", attachment_type=allure.attachment_type.PNG)
    
    with allure.step("Verifying Contact Creation"):
        success_message = new_page.locator("success_message_locator").inner_text()
        assert "Contact Saved" in success_message, "Contact creation failed"
        allure.attach(new_page.screenshot(), name="contact_creation_success", attachment_type=allure.attachment_type.PNG)
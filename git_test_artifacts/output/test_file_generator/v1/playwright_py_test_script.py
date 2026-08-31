from playwright.sync_api import sync_playwright
import allure
import pytest
from output.page_file_generator.Equfix_home_page_playwright import EqufixHomePagePlaywright
from output.page_file_generator.Equfix_Place_On_Alert_playwright import EqufixPlaceOnAlertPlaywright


@pytest.mark.allure_label("TC01 - Place an Alert - Successful Form Submission")
def test_place_alert_successful_form_submission():
    with allure.step("Launch browser and navigate to the base URL"):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/")
            allure.attach(page.screenshot(), name="Launch Page", attachment_type=allure.attachment_type.PNG)

            # Initialize Page Objects
            home_page = EqufixHomePagePlaywright(page)
            alert_page = EqufixPlaceOnAlertPlaywright(page)

            with allure.step("Click on 'Place an Alert' button"):
                home_page.clickPlaceAnAlert()
                allure.attach(page.screenshot(), name="Clicked Place an Alert", attachment_type=allure.attachment_type.PNG)

            with allure.step("Switch to new window for 'Place an Alert'"):
                new_page = context.expect_page(lambda: home_page.clickPlaceAnAlert())
                new_page.wait_for_load_state()
                allure.attach(new_page.screenshot(), name="New Window Loaded", attachment_type=allure.attachment_type.PNG)

                # Reinitialize page object for the new page
                alert_page = EqufixPlaceOnAlertPlaywright(new_page)

            with allure.step("Fill out the form for placing an alert"):
                alert_page.fillFirstName("test")
                allure.attach(new_page.screenshot(), name="First Name Entered", attachment_type=allure.attachment_type.PNG)

                alert_page.fillLastName("test")
                allure.attach(new_page.screenshot(), name="Last Name Entered", attachment_type=allure.attachment_type.PNG)

                alert_page.fillSSN("***-**-6686")
                allure.attach(new_page.screenshot(), name="SSN Entered", attachment_type=allure.attachment_type.PNG)

                alert_page.fillPhoneNumber("786-876-****")
                allure.attach(new_page.screenshot(), name="Phone Number Entered", attachment_type=allure.attachment_type.PNG)

                alert_page.fillDOB("04/22/1990")
                allure.attach(new_page.screenshot(), name="Date of Birth Entered", attachment_type=allure.attachment_type.PNG)

                alert_page.fillAddress("test")
                allure.attach(new_page.screenshot(), name="Address Line 1 Entered", attachment_type=allure.attachment_type.PNG)

                alert_page.fillCity("test")
                allure.attach(new_page.screenshot(), name="City Entered", attachment_type=allure.attachment_type.PNG)

                alert_page.fillAddressLine2("test")
                allure.attach(new_page.screenshot(), name="Address Line 2 Entered", attachment_type=allure.attachment_type.PNG)

                alert_page.selectState("Alaska")
                allure.attach(new_page.screenshot(), name="State Selected", attachment_type=allure.attachment_type.PNG)

                alert_page.fillZip("78686")
                allure.attach(new_page.screenshot(), name="Zip Code Entered", attachment_type=allure.attachment_type.PNG)

            with allure.step("Submit the form"):
                alert_page.clickContinueButton()
                allure.attach(new_page.screenshot(), name="Form Submitted", attachment_type=allure.attachment_type.PNG)

            with allure.step("Verify successful submission"):
                success_message = new_page.locator("xpath=//div[contains(text(), 'Your alert has been placed successfully')]")
                success_message.wait_for()
                assert success_message.is_visible(), "Success message not visible"
                allure.attach(new_page.screenshot(), name="Success Message", attachment_type=allure.attachment_type.PNG)

            browser.close()
from playwright.sync_api import sync_playwright
import time
import allure
from output.page_file_generator.Equfix_home_page_playwright import EqufixHomePagePlaywright

def test_place_alert_successful_form_submission():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        home_page = EqufixHomePagePlaywright(page)

        page.goto("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/")
        home_page.wait_for_element("xpath=//*[@id='banner-description']")
        home_page.update_banner_description("Equifax and its partners use Cookies and similar technologies as necessary to provide digital services and for advertising and targeting, analytics and performance, and functionality and personalization purposes. For more information, please review our Privacy Statement.")
        home_page.close_banner()
        home_page.click_place_an_alert()

        with page.expect_popup() as popup_info:
            home_page.click_place_an_alert()
        new_page = popup_info.value
        new_page.wait_for_load_state("networkidle")

        new_page.fill("xpath=//input[@id='firstNameId']", "test")
        new_page.fill("xpath=//input[@id='lastName']", "test")
        new_page.fill("xpath=//input[@id='ssn']", "***-**-6686")
        new_page.fill("xpath=//input[@id='phoneNumber']", "786-876-****")
        new_page.fill("xpath=//input[@id='dob']", "04/22/1990")
        new_page.fill("xpath=//input[@id='address']", "test")
        new_page.fill("xpath=//input[@id='city']", "test")
        new_page.fill("xpath=//input[@id='addressLine2Id']", "test")
        new_page.click("xpath=//button[@id='efx-dropdown-label-753393']")
        new_page.click("xpath=//li[text()='AK']")
        new_page.fill("xpath=//input[@id='zip']", "78686")

        browser.close()
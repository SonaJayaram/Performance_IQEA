# Run : pytest test_excel_onedrive_flow.py -s --alluredir=allure-results
# View: allure serve allure-results

import os
import time
import allure
import pytest
from allure_commons.types import AttachmentType
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# ─── Global Constants ─────────────────────────────────────────────────────────

APP_PATH  = r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"
FILE_NAME = "Application_details"
LOGIN_URL = "https://onedrive.live.com/login"
EMAIL     = "Sathanantham.aru@tigeranalytics.com"
PASSWORD  = "Automation@1234"


# ─── Desktop Functions ────────────────────────────────────────────────────────

@allure.step("Launch Excel application")
def launch_application(app_path):
    app = Application(backend="uia").start(app_path)
    time.sleep(5)
    dlg = app.window(title_re=".*Excel")
    dlg.wait("visible", timeout=30)
    assert dlg.exists(), \
        "Excel window did not launch or is not visible"
    assert dlg.is_enabled(), \
        "Excel window launched but is not enabled — may be blocked by a dialog"
    return app, dlg


@allure.step("Dismiss Excel start screen and open blank workbook")
def handle_start_screen(dlg):
    dlg.set_focus()
    time.sleep(3)
    send_keys("{ENTER}")
    time.sleep(5)
    assert dlg.exists(), \
        "Excel window lost after dismissing start screen"
    assert "Excel" in dlg.window_text(), \
        f"Unexpected window title after start screen dismissed: {dlg.window_text()}"


@allure.step("Enter column headers and data rows into workbook")
def enter_data(dlg):
    dlg.set_focus()
    time.sleep(2)
    with allure.step("Navigate to cell A1"):
        send_keys("^g")
        time.sleep(1)
        send_keys("A1{ENTER}")
        time.sleep(1)
    with allure.step("Enter column headers: application_name, application_url, user_type"):
        send_keys("application_name{TAB}application_url{TAB}user_type{ENTER}")
        time.sleep(1)
    with allure.step("Enter row 1: google, www.google.com, admin"):
        send_keys("google{TAB}www.google.com{TAB}admin{ENTER}")
        time.sleep(1)
    with allure.step("Enter row 2: amazon, www.amazon.com, localuser"):
        send_keys("amazon{TAB}www.amazon.com{TAB}localuser{ENTER}")
        time.sleep(2)
    assert dlg.is_enabled(), \
        "Excel window lost focus or became unresponsive during data entry"


@allure.step("Save workbook to OneDrive as 'Application_details'")
def save_file(dlg):
    dlg.set_focus()
    time.sleep(1)
    with allure.step("Trigger save with CTRL+S"):
        send_keys("^s")
        time.sleep(3)
    with allure.step("Clear default filename in save dialog"):
        send_keys("^a{BACKSPACE}")
        time.sleep(1)
    with allure.step("Type new filename: Application_details"):
        send_keys(FILE_NAME)
        time.sleep(1)
    with allure.step("Confirm save"):
        send_keys("{ENTER}")
        time.sleep(10)
    assert dlg.is_enabled(), \
        "Excel window became unresponsive after save — OneDrive upload may have failed"


@allure.step("Close Excel application")
def close_application():
    send_keys("%{F4}")
    time.sleep(5)
    try:
        send_keys("{ENTER}")   # confirm any unsaved changes prompt if it appears
    except:
        pass
    time.sleep(3)


# ─── Web Functions ────────────────────────────────────────────────────────────

@allure.step("Open Chrome browser")
def open_browser():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--remote-allow-origins=*")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    time.sleep(3)
    assert driver.current_url is not None, \
        "Chrome WebDriver initialized but current URL is None"
    return driver


@allure.step("Login to OneDrive web portal")
def login_to_web(driver, url, username, password):
    try:
        driver.get(url)
        time.sleep(5)
        actions = ActionChains(driver)
        with allure.step("Enter email address and click Next"):
            actions.send_keys(username).perform()
            time.sleep(2)
            actions.send_keys(Keys.ENTER).perform()
            time.sleep(5)
        with allure.step("Enter password and click Sign In"):
            actions.send_keys(password).perform()
            time.sleep(2)
            actions.send_keys(Keys.ENTER).perform()
            time.sleep(15)
        with allure.step("Dismiss optional Stay Signed In prompt"):
            try:
                actions.send_keys(Keys.ENTER).perform()
            except:
                pass
            time.sleep(10)
        assert_with_screenshot(
            driver,
            "login" not in driver.current_url.lower(),
            f"Login failed — still on login page after sign in. Current URL: {driver.current_url}"
        )
        assert_with_screenshot(
            driver,
            "onedrive" in driver.current_url.lower() or "sharepoint" in driver.current_url.lower(),
            f"Login succeeded but landed on unexpected page. Current URL: {driver.current_url}"
        )
    except Exception as e:
        allure.attach(
            driver.get_screenshot_as_png(),
            name="login_failure_screenshot",
            attachment_type=AttachmentType.PNG
        )
        raise


@allure.step("Open file '{item_name}' from OneDrive")
def open_item_in_web(driver, item_name):
    try:
        try:
            element = driver.find_element(
                By.XPATH, f"//button[contains(text(),'{item_name}')]"
            )
        except:
            element = driver.find_element(
                By.XPATH, f"//*[contains(text(),'{item_name}')]"
            )
        element.click()
        time.sleep(5)
        assert_with_screenshot(
            driver,
            len(driver.window_handles) > 1,
            f"Expected new tab to open after clicking '{item_name}' but no new tab was detected"
        )
    except Exception as e:
        allure.attach(
            driver.get_screenshot_as_png(),
            name="open_file_failure_screenshot",
            attachment_type=AttachmentType.PNG
        )
        raise


@allure.step("Execute in-app command: 'Download a copy'")
def execute_web_command(driver, command_text):
    try:
        actions = ActionChains(driver)
        with allure.step("Open ALT+Q command bar"):
            actions.key_down(Keys.ALT).send_keys("q").key_up(Keys.ALT).perform()
            time.sleep(3)
        with allure.step(f"Type command text: {command_text}"):
            actions.send_keys(command_text).perform()
            time.sleep(2)
        with allure.step("Select and execute the command"):
            actions.send_keys(Keys.ENTER).perform()
            time.sleep(10)
        with allure.step("Confirm download dialog"):
            actions.send_keys(Keys.ENTER).perform()
            time.sleep(10)
    except Exception as e:
        allure.attach(
            driver.get_screenshot_as_png(),
            name="command_execution_failure_screenshot",
            attachment_type=AttachmentType.PNG
        )
        raise


@allure.step("Close the browser")
def close_browser(driver):
    driver.quit()
    time.sleep(2)


# ─── Utility Functions ────────────────────────────────────────────────────────

@allure.step("Switch to new browser window or tab")
def switch_to_new_window(driver):
    current_window = driver.current_window_handle
    for handle in driver.window_handles:
        if handle != current_window:
            driver.switch_to.window(handle)
            break
    time.sleep(3)
    assert driver.current_window_handle != current_window, \
        "Window switch failed — still on the original window after switch attempt"


def assert_with_screenshot(driver, condition, message):
    """Asserts a condition; on failure attaches a screenshot to Allure and raises."""
    if not condition:
        allure.attach(
            driver.get_screenshot_as_png(),
            name="assertion_failure_screenshot",
            attachment_type=AttachmentType.PNG
        )
        raise AssertionError(message)


# ─── Main Test ────────────────────────────────────────────────────────────────

@allure.title("Excel Data Entry, OneDrive Save and File Download")
@allure.description(
    "End-to-end automation: open Excel, create a workbook with application data, "
    "save it to OneDrive, then log in to OneDrive web portal, open the saved file "
    "in a new tab, download a copy using the command bar, and close the browser."
)
@allure.severity(allure.severity_level.CRITICAL)
@allure.feature("Hybrid Automation")
@allure.story("Create Excel workbook, save to OneDrive, login to web, download file copy, close browser")
def test_end_to_end_flow():

    # ── Desktop: Excel ────────────────────────────────────────────────────────
    app, dlg = launch_application(APP_PATH)
    handle_start_screen(dlg)
    enter_data(dlg)
    save_file(dlg)
    close_application()

    # ── Web: OneDrive ─────────────────────────────────────────────────────────
    driver = open_browser()
    try:
        login_to_web(driver, LOGIN_URL, EMAIL, PASSWORD)
        open_item_in_web(driver, FILE_NAME)
        switch_to_new_window(driver)
        execute_web_command(driver, "Download a copy")

        # Final end-state assertion — browser still active after download triggered
        assert_with_screenshot(
            driver,
            len(driver.current_url) > 0,
            "Final state check failed — browser URL is empty after download command"
        )

    finally:
        # Close browser as final workflow step — runs whether test passes or fails
        close_browser(driver)
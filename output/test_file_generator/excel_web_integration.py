import os
import time
from pywinauto import Application
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# Global Variables
EXCEL_PATH = r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"
FILE_NAME = "Application_details"
ONEDRIVE_URL = "https://onedrive.live.com/login"
EMAIL = "Sathanantham.aru@tigeranayltics.com"
PASSWORD = "************"

# Desktop Automation Functions
def launch_application(app_path):
    app = Application(backend="uia").start(app_path)
    time.sleep(5)
    return app

def perform_desktop_actions(app):
    excel_window = app.window(title_re=".*Excel")
    excel_window.set_focus()
    excel_window.type_keys("^n")  # New workbook
    time.sleep(2)
    excel_window.type_keys("application_name{TAB}application_url{TAB}user type{ENTER}")
    excel_window.type_keys("google{TAB}www.google.com{TAB}admin{ENTER}")
    excel_window.type_keys("amazon{TAB}www.amazon.com{TAB}localuser{ENTER}")
    excel_window.type_keys("%f")  # File menu
    time.sleep(1)
    excel_window.type_keys("a")  # Save As
    time.sleep(2)
    excel_window.type_keys(FILE_NAME)
    time.sleep(1)
    excel_window.type_keys("{ENTER}")
    time.sleep(5)

# Web Automation Functions
def open_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    return driver

def perform_web_actions(driver):
    driver.get(ONEDRIVE_URL)
    time.sleep(5)
    actions = ActionChains(driver)
    actions.send_keys(EMAIL).perform()
    actions.send_keys(Keys.ENTER).perform()
    time.sleep(3)
    actions.send_keys(PASSWORD).perform()
    actions.send_keys(Keys.ENTER).perform()
    time.sleep(10)
    switch_to_new_window(driver)
    actions.send_keys(Keys.TAB * 5).perform()  # Navigate to file
    actions.send_keys(Keys.ENTER).perform()
    time.sleep(5)
    actions.send_keys(Keys.TAB * 10).perform()  # Navigate to download
    actions.send_keys(Keys.ENTER).perform()
    time.sleep(5)

# Utility Functions
def switch_to_new_window(driver):
    current_window = driver.current_window_handle
    for handle in driver.window_handles:
        if handle != current_window:
            driver.switch_to.window(handle)
            break

# Main Test Function
def test_end_to_end_flow():
    # Desktop Automation
    app = launch_application(EXCEL_PATH)
    perform_desktop_actions(app)
    
    # Web Automation
    driver = open_browser()
    try:
        perform_web_actions(driver)
    finally:
        driver.quit()
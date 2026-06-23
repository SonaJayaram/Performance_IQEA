import time
import os
import pytest
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# ─── Global Constants ─────────────────────────────────────────────────────────

APP_PATH = r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"
FILE_NAME = "Application_details_mar17_v1"
LOGIN_URL = "https://onedrive.live.com/login"
EMAIL = "Sathanantham.aru@tigeranalytics.com"
PASSWORD = "Automation@1234"


# ─── Desktop Functions ────────────────────────────────────────────────────────

def launch_application(app_path):
    app = Application(backend="uia").start(app_path)
    time.sleep(5)
    dlg = app.window(title_re=".*Excel")
    dlg.wait("visible", timeout=30)
    return app, dlg


def handle_start_screen(dlg):
    dlg.set_focus()
    time.sleep(3)
    send_keys("{ENTER}")  # select default highlighted Blank Workbook
    time.sleep(5)


def enter_data(dlg):
    dlg.set_focus()
    time.sleep(2)
    send_keys("^g")
    time.sleep(1)
    send_keys("A1{ENTER}")
    time.sleep(1)
    send_keys("application_name{TAB}application_url{TAB}user_type{ENTER}")
    time.sleep(1)
    send_keys("google{TAB}www.google.com{TAB}admin{ENTER}")
    time.sleep(1)
    send_keys("amazon{TAB}www.amazon.com{TAB}localuser{ENTER}")
    time.sleep(2)


def save_file(dlg):
    dlg.set_focus()
    time.sleep(1)
    send_keys("^s")
    time.sleep(3)
    send_keys("^a{BACKSPACE}")
    time.sleep(1)
    send_keys(FILE_NAME)
    time.sleep(1)
    send_keys("{ENTER}")
    time.sleep(10)


def close_application():
    send_keys("%{F4}")
    time.sleep(5)
    try:
        send_keys("{ENTER}")  # confirm any unsaved changes dialog
    except:
        pass
    time.sleep(3)


# ─── Web Functions ────────────────────────────────────────────────────────────

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
    return driver


def login_to_web(driver, url, username, password):
    driver.get(url)
    time.sleep(5)
    actions = ActionChains(driver)
    actions.send_keys(username).perform()
    time.sleep(2)
    actions.send_keys(Keys.ENTER).perform()
    time.sleep(5)
    actions.send_keys(password).perform()
    time.sleep(2)
    actions.send_keys(Keys.ENTER).perform()
    time.sleep(15)
    try:
        actions.send_keys(Keys.ENTER).perform()  # dismiss optional "Stay signed in" prompt
    except:
        pass
    time.sleep(10)


def open_item_in_web(driver, item_name):
    try:
        time.sleep(5)
        element = driver.find_element(By.XPATH, f"//button[contains(text(),'{item_name}')]")
    except:
        element = driver.find_element(By.XPATH, f"//*[contains(text(),'{item_name}')]")

    element.click()
    time.sleep(5)


def execute_web_command(driver, command_text):
    actions = ActionChains(driver)
    actions.key_down(Keys.ALT).send_keys("q").key_up(Keys.ALT).perform()
    time.sleep(3)
    actions.send_keys(command_text).perform()
    time.sleep(2)
    actions.send_keys(Keys.ENTER).perform()
    time.sleep(10)
    actions.send_keys(Keys.ENTER).perform()  # confirm any follow-up dialog
    time.sleep(10)


# ─── Utility Functions ────────────────────────────────────────────────────────

def switch_to_new_window(driver):
    current_window = driver.current_window_handle
    for handle in driver.window_handles:
        if handle != current_window:
            driver.switch_to.window(handle)
            break
    time.sleep(3)


# ─── Main Test ────────────────────────────────────────────────────────────────

def test_end_to_end_flow():
    # --- Desktop: Excel ---
    # app, dlg = launch_application(APP_PATH)
    # handle_start_screen(dlg)
    # enter_data(dlg)
    # save_file(dlg)
    # close_application()

    # --- Web: OneDrive ---
    driver = open_browser()
    try:
        login_to_web(driver, LOGIN_URL, EMAIL, PASSWORD)
        open_item_in_web(driver, FILE_NAME)
        switch_to_new_window(driver)
        execute_web_command(driver, "Download a copy")
    finally:
        driver.quit()
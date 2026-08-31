import time
import pytest
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

EXCEL_PATH = r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"



def download_using_command_bar(driver):

    print("Triggering command bar (ALT+Q)...")
    current_window = driver.current_window_handle
    # Switch to new window
    for window in driver.window_handles:
        if window != current_window:
            driver.switch_to.window(window)
            break

    print("Switched to new window")
    actions = ActionChains(driver)

    # Press ALT + Q
    actions.key_down(Keys.ALT).send_keys("q").key_up(Keys.ALT).perform()
    time.sleep(3)

    print("Typing 'Download a copy'...")

    actions.send_keys("Download a copy").perform()
    time.sleep(2)

    # Press ENTER
    actions.send_keys(Keys.ENTER).perform()
    time.sleep(10)
    actions.send_keys(Keys.ENTER).perform()
    time.sleep(10)

    print("Download triggered via command bar")

def onedrive_download():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")  # 🔑 prevents Skia/SharedImage GPU errors
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--remote-allow-origins=*")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.binary_location = chromedriver_path
    # service = Service(executable_path=chromedriver_path)
    # service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()

    print("Opening OneDrive login page...")
    driver.get("https://onedrive.live.com/login")
    time.sleep(5)

    # -------------------------------
    # Step 1: Enter Email
    # -------------------------------
    print("Entering email...")
    wait = WebDriverWait(driver, 20)
    time.sleep(5)
    actions = ActionChains(driver)
    actions.send_keys("Sathanantham.aru@tigeranalytics.com").perform()
    time.sleep(2)
    actions.send_keys(Keys.ENTER).perform()
    time.sleep(5)

    # -------------------------------
    # Step 2: Enter Password
    # -------------------------------
    print("Entering password...")
    time.sleep(5)
    actions.send_keys("Automation@1234").perform()
    time.sleep(2)
    actions.send_keys(Keys.ENTER).perform()
    time.sleep(15)

    # -------------------------------
    # Step 3: Stay signed in (optional)
    # -------------------------------
    try:
        actions.send_keys(Keys.ENTER).perform()
    except:
        pass

    time.sleep(15)

    # -------------------------------
    # Step 4: Search File
    # -------------------------------
    print("Searching for file...")

    search_box = driver.find_element(By.XPATH, "//button[contains(text(),'Application_details_mar17_v1')]")
    search_box.click()

    time.sleep(5)

    # -------------------------------
    # Step 5: Open File
    # -------------------------------
    print("Opening file...")

    download_using_command_bar(driver)

    # -------------------------------
    # Step 6: Download File
    # -------------------------------
    print("Downloading file...")
    driver.quit()
def launch_excel():
    app = Application(backend="uia").start(EXCEL_PATH)
    time.sleep(5)

    dlg = app.window(title_re=".*Excel")
    dlg.wait("visible", timeout=30)

    return app, dlg


def create_new_workbook_v1(dlg):
    dlg.set_focus()
    time.sleep(3)

    print("Trying to click Blank Workbook...")

    try:
        # More specific search
        blank_items = dlg.descendants(control_type="ListItem")

        for item in blank_items:
            name = item.window_text()

            if name and "blank" in name.lower():
                print(f"Found: {name}")
                item.click_input()
                time.sleep(5)
                return

        raise Exception("Blank workbook not found in list")

    except Exception as e:
        print("UI selection failed → fallback to CTRL+N")
        send_keys("^n")
        time.sleep(5)
def create_new_workbook(dlg):
    dlg.set_focus()
    time.sleep(3)

    print("Opening default selected Blank Workbook using ENTER")
    send_keys("{ENTER}")
    time.sleep(5)
def enter_excel_data(dlg):
    dlg.set_focus()
    time.sleep(2)

    # Go to A1
    send_keys("^g")
    time.sleep(1)
    send_keys("A1{ENTER}")
    time.sleep(1)

    # Headers
    send_keys("application_name{TAB}application_url{TAB}user_type{ENTER}")
    time.sleep(1)

    # Row 1
    send_keys("google{TAB}www.google.com{TAB}admin{ENTER}")
    time.sleep(1)

    # Row 2
    send_keys("amazon{TAB}www.amazon.com{TAB}localuser{ENTER}")
    time.sleep(2)


import os

def save_excel(dlg):
    dlg.set_focus()
    time.sleep(1)

    print("Saving using CTRL+S...")

    # Trigger Save dialog
    send_keys("^s")
    time.sleep(3)

    print("Entering file name...")

    # Clear default name (Book1)
    send_keys("^a{BACKSPACE}")
    time.sleep(1)


    # Enter your file name
    send_keys("Application_details_mar17_v1")
    time.sleep(1)

    # Save
    send_keys("{ENTER}")
    time.sleep(10)


    print("File saved successfully (default OneDrive location)")

def test_excel_desktop_flow():

    app, dlg = launch_excel()

    create_new_workbook(dlg)

    enter_excel_data(dlg)

    save_excel(dlg)

    # Optional close
    send_keys("%{F4}")
    time.sleep(5)
    send_keys("{ENTER}")
    onedrive_download()
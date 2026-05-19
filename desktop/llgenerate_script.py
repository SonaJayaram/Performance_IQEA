import time
import os
import pytest
from pywinauto import Application, keyboard
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options


APPLICATION_PATH = r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"
ONEDRIVE_URL = "https://onedrive.live.com/login"
EMAIL = "Sathanantham.aru@tigeranayltics.com"
PASSWORD = "************"


def launch_application():
    app = Application(backend="uia").start(APPLICATION_PATH)
    time.sleep(5)
    return app


def create_excel_and_enter_data(app):
    dlg = app.top_window()
    dlg.set_focus()
    time.sleep(2)

    keyboard.send_keys("^n")
    time.sleep(3)

    keyboard.send_keys("application_name{TAB}application_url{TAB}user_type")
    time.sleep(1)

    keyboard.send_keys("{ENTER}")
    keyboard.send_keys("google{TAB}www.google.com{TAB}admin")
    time.sleep(1)

    keyboard.send_keys("{ENTER}")
    keyboard.send_keys("amzzon{TAB}www.amazon.com{TAB}localuser")
    time.sleep(2)


def save_excel_file():
    keyboard.send_keys("^s")
    time.sleep(3)

    keyboard.send_keys("Apllication_details")
    time.sleep(1)

    keyboard.send_keys("{ENTER}")
    time.sleep(5)


def open_browser():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def login_onedrive(driver):
    driver.get(ONEDRIVE_URL)
    time.sleep(5)

    driver.find_element(By.NAME, "loginfmt").send_keys(EMAIL)
    time.sleep(2)

    driver.find_element(By.ID, "idSIButton9").click()
    time.sleep(3)

    driver.find_element(By.NAME, "passwd").send_keys(PASSWORD)
    time.sleep(2)

    driver.find_element(By.ID, "idSIButton9").click()
    time.sleep(10)


def open_file_and_download(driver):
    actions = ActionChains(driver)

    time.sleep(10)

    body = driver.find_element(By.TAG_NAME, "body")
    body.click()

    actions.send_keys("Apllication_details").perform()
    time.sleep(3)

    actions.send_keys("\n").perform()
    time.sleep(5)

    handles = driver.window_handles
    driver.switch_to.window(handles[-1])
    time.sleep(5)

    actions.send_keys("^f").perform()
    time.sleep(2)

    actions.send_keys("download a copy").perform()
    time.sleep(2)

    actions.send_keys("\n").perform()
    time.sleep(5)


@pytest.mark.end_to_end
def test_end_to_end_flow():
    app = launch_application()
    create_excel_and_enter_data(app)
    save_excel_file()

    driver = open_browser()
    login_onedrive(driver)
    open_file_and_download(driver)

    driver.quit()
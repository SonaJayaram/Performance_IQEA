from appium import webdriver
from action_logger import log_action

driver = None

def start_session(device_id, app_package=None, app_activity=None, browser=False):
    global driver

    desired_caps = {
        "platformName": "Android",
        "deviceName": device_id,
        "udid": device_id,
        "automationName": "UiAutomator2"
    }

    if browser:
        desired_caps["browserName"] = "Chrome"
    else:
        desired_caps["appPackage"] = app_package
        desired_caps["appActivity"] = app_activity

    driver = webdriver.Remote("http://localhost:4723/wd/hub", desired_caps)

def click(locator_type, locator_value):
    element = driver.find_element(locator_type, locator_value)
    log_action("click", {locator_type: locator_value})
    element.click()

def enter_text(locator_type, locator_value, text):
    element = driver.find_element(locator_type, locator_value)
    log_action("enter_text", {locator_type: locator_value}, text)
    element.send_keys(text)

def stop_session():
    global driver
    if driver:
        driver.quit()
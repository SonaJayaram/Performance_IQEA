import json

def generate_python_appium_script(action_file="actions.json"):
    with open(action_file) as f:
        actions = json.load(f)

    script = """
from appium import webdriver
import time

caps = {
    "platformName": "Android",
    "deviceName": "YOUR_DEVICE",
    "automationName": "UiAutomator2"
}

driver = webdriver.Remote("http://localhost:4723/wd/hub", caps)
time.sleep(3)
"""

    for step in actions:
        action = step["action"]
        locator = step.get("locator", {})
        value = step.get("value", "")

        if action == "click":
            key = list(locator.keys())[0]
            val = locator[key]
            script += f'driver.find_element("{key}", "{val}").click()\n'

        elif action == "enter_text":
            key = list(locator.keys())[0]
            val = locator[key]
            script += f'driver.find_element("{key}", "{val}").send_keys("{value}")\n'

    script += "\ndriver.quit()"

    return script
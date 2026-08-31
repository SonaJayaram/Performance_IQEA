import pytest
import allure
import time
import os
from allure_commons.types import AttachmentType
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://agentflow-uat.tigeranalyticstest.in/Home"
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def attach_screenshot(driver, name: str):
    try:
        allure.attach(driver.get_screenshot_as_png(),
                      name=name, attachment_type=AttachmentType.PNG)
    except Exception:
        pass

@pytest.fixture(scope="function")
def setup():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(0)
    yield driver
    driver.quit()

def _retry_click_first_after_page_change(driver, wait, locator, label):
    attempt, last_err = 0, None
    while attempt < 2:
        try:
            el = wait.until(EC.element_to_be_clickable(locator))
            el.click()
            break
        except Exception as e:
            last_err = e
            attach_screenshot(driver, f"retry_{label}_{attempt}")
            time.sleep(0.5)
            attempt += 1
    if attempt == 2:
        attach_screenshot(driver, f"failed_{label}")
        raise RuntimeError(f"{label} failed: {last_err}")

@allure.title("Happy path: Create agent, add nodes, configure and save")
@pytest.mark.smoke
def test_happy_path_create_and_configure_agent(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)
    attach_screenshot(driver, "start")

    with allure.step("Navigate to Agent Studio"):
        el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="link-Agent Studio"]')))
        el.click()
        wait.until(EC.url_contains("/workflow"))
        attach_screenshot(driver, "navigated_to_workflow")

    with allure.step("Click + New Agent (first interaction after page change, apply retry)"):
        _retry_click_first_after_page_change(driver, wait, (By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div/div[2]/button'), "click_new_agent")

    with allure.step("Fill Experiment Name and Description"):
        exp_name = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@aria-label="Experiment Name"]')))
        exp_name.clear()
        exp_name.send_keys("Test Experiment Selenium")
        desc = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="project_description"]')))
        desc.clear()
        desc.send_keys("This is an automated test description for the experiment.")
        attach_screenshot(driver, "filled_experiment_details")

    with allure.step("Click Continue to go to canvas"):
        btn_continue = wait.until(EC.element_to_be_clickable((By.ID, "Continue")))
        btn_continue.click()
        wait.until(EC.url_contains("/workflow/canvas"))
        attach_screenshot(driver, "navigated_to_canvas")

    with allure.step("Click primary button on canvas (first interaction after canvas page change, apply retry)"):
        _retry_click_first_after_page_change(driver, wait, (By.ID, "button"), "canvas_initial_button")

    with allure.step("Add first node"):
        add_node_locator = (By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div/div/div[4]/div/div/div')
        add_btn = wait.until(EC.element_to_be_clickable(add_node_locator))
        add_btn.click()
        attach_screenshot(driver, "added_node_1")

    with allure.step("Set Node Name and add"):
        node_name = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Node Name"]')))
        node_name.clear()
        node_name.send_keys("Node 1 - Base LLM")
        add_btn2 = wait.until(EC.element_to_be_clickable((By.ID, "Add")))
        add_btn2.click()
        attach_screenshot(driver, "node_1_added")

    with allure.step("Add second node (If Else) and name it"):
        # Open node menu and choose If Else
        ifelse_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[3]/div/div/div/div[3]/div[2]/div/button[3]')))
        ifelse_btn.click()
        add_node_locator2 = (By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div/div/div[4]/div/div/div')
        add_btn3 = wait.until(EC.element_to_be_clickable(add_node_locator2))
        add_btn3.click()
        node_name2 = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Node Name"]')))
        node_name2.clear()
        node_name2.send_keys("Node 2 - IfElse")
        add_btn4 = wait.until(EC.element_to_be_clickable((By.ID, "Add")))
        add_btn4.click()
        attach_screenshot(driver, "node_2_added")

    with allure.step("Add third node and name it"):
        add_btn5 = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div/div/div[4]/div/div/div')))
        add_btn5.click()
        node_name3 = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Node Name"]')))
        node_name3.clear()
        node_name3.send_keys("Node 3 - Final")
        add_btn6 = wait.until(EC.element_to_be_clickable((By.ID, "Add")))
        add_btn6.click()
        attach_screenshot(driver, "node_3_added")

    with allure.step("Open Edit Settings for specific node"):
        edit_node = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@data-testid="rf__node-3f08d940-9cd9-49eb-b0e8-7bbf24106056"]')))
        edit_node.click()
        attach_screenshot(driver, "opened_edit_settings")

    with allure.step("Select model option gpt-image-1.5"):
        opt = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div[3]/ul/li[2]')))
        opt.click()
        attach_screenshot(driver, "selected_model_option")

    with allure.step("Add Input -> User Query and set prompt"):
        add_input_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[3]/div/div/div/div[2]/div/div/div[2]/div/div/div/div[6]/div/div/div/div/button')))
        add_input_btn.click()
        user_query_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[3]/div/div/div/div[2]/div/div/div[2]/div/div/div/div[6]/div/div/div/div/div/div[2]/button')))
        user_query_btn.click()
        uq = wait.until(EC.element_to_be_clickable((By.ID, "user_query")))
        uq.click()
        prompt_el = wait.until(EC.presence_of_element_located((By.ID, "user_querytest")))
        try:
            prompt_el.clear()
        except Exception:
            pass
        prompt_el.send_keys("Test user's input message for automation.")
        attach_screenshot(driver, "entered_user_prompt")

    with allure.step("Save configuration"):
        save_btn = wait.until(EC.element_to_be_clickable((By.ID, "Save")))
        save_btn.click()
        attach_screenshot(driver, "after_save_flow")

    # Final assertion: ensure we are still on canvas with pageType=form
    assert "pageType=form" in driver.current_url
    attach_screenshot(driver, "assertion_passed")

@allure.title("Boundary: Attempt to continue without filling required fields")
@pytest.mark.boundary
def test_continue_without_filling_required_fields(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)
    attach_screenshot(driver, "start")

    with allure.step("Navigate to Agent Studio"):
        el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="link-Agent Studio"]')))
        el.click()
        wait.until(EC.url_contains("/workflow"))
        attach_screenshot(driver, "navigated_to_workflow")

    with allure.step("Click + New Agent (first interaction after page change, apply retry)"):
        _retry_click_first_after_page_change(driver, wait, (By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div/div[2]/button'), "click_new_agent_boundary")

    with allure.step("Click Continue without entering Experiment details"):
        btn_continue = wait.until(EC.element_to_be_clickable((By.ID, "Continue")))
        btn_continue.click()
        time.sleep(1)  # allow any navigation attempt
        attach_screenshot(driver, "clicked_continue_without_details")

    # Assert we did not navigate to canvas (boundary validation)
    assert "/workflow/canvas" not in driver.current_url
    attach_screenshot(driver, "assertion_passed")

@allure.title("Negative: Try to add node without providing a node name")
@pytest.mark.negative
def test_add_node_without_name_should_not_create_node(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)
    attach_screenshot(driver, "start")

    with allure.step("Navigate to Agent Studio"):
        el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="link-Agent Studio"]')))
        el.click()
        wait.until(EC.url_contains("/workflow"))
        attach_screenshot(driver, "navigated_to_workflow")

    with allure.step("Click + New Agent (first interaction after page change, apply retry)"):
        _retry_click_first_after_page_change(driver, wait, (By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div/div[2]/button'), "click_new_agent_neg")

    with allure.step("Fill only Experiment Name and leave Node Name empty, then Continue"):
        exp_name = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@aria-label="Experiment Name"]')))
        exp_name.clear()
        exp_name.send_keys("Neg Test Experiment")
        # Intentionally not filling description
        btn_continue = wait.until(EC.element_to_be_clickable((By.ID, "Continue")))
        btn_continue.click()
        wait.until(EC.url_contains("/workflow/canvas"))
        attach_screenshot(driver, "navigated_to_canvas")

    with allure.step("Add a node but attempt to Add without entering Node Name"):
        add_node_locator = (By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div/div/div[4]/div/div/div')
        add_btn = wait.until(EC.element_to_be_clickable(add_node_locator))
        add_btn.click()
        # Do not enter node name; click Add
        add_without_name = wait.until(EC.element_to_be_clickable((By.ID, "Add")))
        add_without_name.click()
        attach_screenshot(driver, "attempted_add_node_without_name")

    # Assert that Node Name input is still present (meaning node was not added/closed)
    node_input_present = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Node Name"]')))
    assert node_input_present.is_displayed()
    attach_screenshot(driver, "assertion_passed")

@allure.title("Regression: Edit settings and select model then save prompt")
@pytest.mark.regression
def test_edit_settings_select_model_and_save_prompt(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)
    attach_screenshot(driver, "start")

    with allure.step("Navigate to Agent Studio"):
        el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="link-Agent Studio"]')))
        el.click()
        wait.until(EC.url_contains("/workflow"))
        attach_screenshot(driver, "navigated_to_workflow")

    with allure.step("Click + New Agent (first interaction after page change, apply retry)"):
        _retry_click_first_after_page_change(driver, wait, (By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div/div[2]/button'), "click_new_agent_regression")

    with allure.step("Fill Experiment Name and Description"):
        exp_name = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@aria-label="Experiment Name"]')))
        exp_name.clear()
        exp_name.send_keys("Regression Experiment")
        desc = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="project_description"]')))
        desc.clear()
        desc.send_keys("Regression flow testing model selection.")
        attach_screenshot(driver, "filled_experiment_details_reg")

    with allure.step("Click Continue to go to canvas"):
        btn_continue = wait.until(EC.element_to_be_clickable((By.ID, "Continue")))
        btn_continue.click()
        wait.until(EC.url_contains("/workflow/canvas"))
        attach_screenshot(driver, "navigated_to_canvas_reg")

    with allure.step("Click primary canvas button (first interaction after page change, apply retry)"):
        _retry_click_first_after_page_change(driver, wait, (By.ID, "button"), "canvas_initial_button_reg")

    with allure.step("Add a node and open its settings"):
        add_node_locator = (By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div/div/div[4]/div/div/div')
        add_btn = wait.until(EC.element_to_be_clickable(add_node_locator))
        add_btn.click()
        node_name = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Node Name"]')))
        node_name.clear()
        node_name.send_keys("Reg Node")
        add_btn2 = wait.until(EC.element_to_be_clickable((By.ID, "Add")))
        add_btn2.click()
        attach_screenshot(driver, "reg_node_added")

    with allure.step("Open Edit Settings for node and select model"):
        edit_node = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@data-testid="rf__node-3f08d940-9cd9-49eb-b0e8-7bbf24106056"]')))
        edit_node.click()
        opt = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div[3]/ul/li[2]')))
        opt.click()
        attach_screenshot(driver, "model_selected_reg")

    with allure.step("Add User Query prompt and save"):
        add_input_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[3]/div/div/div/div[2]/div/div/div[2]/div/div/div/div[6]/div/div/div/div/button')))
        add_input_btn.click()
        user_query_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[3]/div/div/div/div[2]/div/div/div[2]/div/div/div/div[6]/div/div/div/div/div/div[2]/button')))
        user_query_btn.click()
        uq = wait.until(EC.element_to_be_clickable((By.ID, "user_query")))
        uq.click()
        prompt_el = wait.until(EC.presence_of_element_located((By.ID, "user_querytest")))
        try:
            prompt_el.clear()
        except Exception:
            pass
        prompt_el.send_keys("Regression test prompt content.")
        save_btn = wait.until(EC.element_to_be_clickable((By.ID, "Save")))
        save_btn.click()
        attach_screenshot(driver, "saved_reg_prompt")

    # Assert that we remain on canvas page after saving settings
    assert "/workflow/canvas" in driver.current_url
    attach_screenshot(driver, "assertion_passed")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
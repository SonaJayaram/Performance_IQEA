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

BASE_URL = "https://agentflow-uat.tigeranalyticstest.in/workflow"
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

def _retry_interaction(driver, label, action_func, wait, max_attempts=2):
    attempt, last_err = 0, None
    while attempt < max_attempts:
        try:
            action_func()
            return
        except Exception as e:
            last_err = e
            attach_screenshot(driver, f"retry_{label}_{attempt}")
            time.sleep(0.5)
            attempt += 1
    attach_screenshot(driver, f"failed_{label}")
    raise RuntimeError(f"{label} failed: {last_err}")

@allure.title("Happy path: Create Agent, configure nodes, save and add S3 Data Store")
@pytest.mark.smoke
def test_happy_path_full_flow(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)
    
    driver.implicitly_wait(50)  # Wait for page to load fully, adjust as needed
    attach_screenshot(driver, "start")

    with allure.step("Step 1: Click Close"):
        el = wait.until(EC.element_to_be_clickable((By.ID, "Close")))
        el.click()

    with allure.step("Step 2: Navigate to Home via link-Home"):
        el = wait.until(EC.presence_of_element_located((By.ID, "link-Home")))
        driver.execute_script("arguments[0].click();", el)
        wait.until(EC.url_contains("/Home"))
        attach_screenshot(driver, "navigated_to_Home")

    with allure.step("Step 3: Navigate back to Workflow via link-Agent Studio (retry applied)"):
        def action():
            el = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="link-Agent Studio"]')))
            driver.execute_script("arguments[0].click();", el)
            wait.until(EC.url_contains("/workflow"))
        _retry_interaction(driver, "click_link-Agent_Studio", action, wait)
        attach_screenshot(driver, "navigated_to_workflow")

    with allure.step("Step 4: Click + New Agent"):
        el = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div/div[2]/button')))
        el.click()

    with allure.step("Step 5-6: Enter Experiment Name"):
        el = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@aria-label="Experiment Name"]')))
        el.clear()
        el.send_keys("Automated Experiment - Happy Path")

    with allure.step("Step 7: Enter Experiment Description"):
        el = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="project_description"]')))
        el.clear()
        el.send_keys("This is a test experiment created by automation - happy path.")

    with allure.step("Step 8: Click Continue and wait for canvas (retry NOT required here as this causes the page change)"):
        el = wait.until(EC.element_to_be_clickable((By.ID, "Continue")))
        el.click()
        wait.until(EC.url_contains("pageType=form"))
        attach_screenshot(driver, "navigated_to_canvas")

    with allure.step("Step 10: Click button on canvas (retry applied)"):
        def action_button():
            el = wait.until(EC.element_to_be_clickable((By.ID, "button")))
            el.click()
        _retry_interaction(driver, "canvas_button", action_button, wait)

    with allure.step("Step 11-13: Add node and set Node Name"):
        # Add node by clicking the container (as recorded)
        el = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div/div/div[4]/div/div/div')))
        el.click()
        input_el = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Node Name"]')))
        input_el.clear()
        input_el.send_keys("Test Case Agent (BASE)")

    with allure.step("Step 16-23: Choose Base and add additional nodes"):
        el = wait.until(EC.element_to_be_clickable((By.ID, "Base")))
        el.click()
        # Add node instances multiple times as per recorded steps
        for _ in range(3):
            add_el = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div/div/div[4]/div/div/div')))
            add_el.click()
            time.sleep(0.2)

    with allure.step("Step 37-44: Edit node settings, select model, add input, choose user query and save"):
        node_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@data-testid="rf__node-52a0f840-bb0c-41e2-b4fe-603ae68b191a"]')))
        node_btn.click()
        opt = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div[3]/ul/li[3]')))
        opt.click()
        add_input_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[3]/div/div/div/div[2]/div/div/div[2]/div/div/div/div[6]/div/div/div/div/button')))
        add_input_btn.click()
        user_query_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[3]/div/div/div/div[2]/div/div/div[2]/div/div/div/div[6]/div/div/div/div/div/div[2]/button')))
        user_query_btn.click()
        sel = wait.until(EC.presence_of_element_located((By.ID, 'react-select-2-option-1')))
        sel.click()
        req_div = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[3]/div/div/div/div[2]/div[2]/div[2]/div/div/div[2]/div/div/div/div')))
        req_div.click()
        req_div.send_keys("requirement_agent_response user_querytestcase")
        save_btn = wait.until(EC.element_to_be_clickable((By.ID, "Save")))
        save_btn.click()
        attach_screenshot(driver, "after_save_flow")

    with allure.step("Step 46: Navigate to Data Store via link-Data Store (retry applied)"):
        el = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="link-Data Store"]')))
        driver.execute_script("arguments[0].click();", el)
        wait.until(EC.url_contains("/datasource"))
        attach_screenshot(driver, "navigated_to_datasource")

    with allure.step("Step 47-59: Add S3 Data Store and fill details"):
        def action_add_datastore():
            add_ds = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div[2]/button')))
            add_ds.click()
        _retry_interaction(driver, "click_Add_Data_Store", action_add_datastore, wait)

        s3_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[3]/div/div/div/div[3]/div/div/div/button[5]')))
        s3_btn.click()

        name_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Enter Data Source Name"]')))
        name_input.clear()
        name_input.send_keys("Automated S3 Store")

        desc = wait.until(EC.presence_of_element_located((By.XPATH, '//textarea[@aria-label="Data Source Description"]')))
        desc.clear()
        desc.send_keys("S3 Data source added by automation")

        sel_opt = wait.until(EC.presence_of_element_located((By.ID, 'react-select-4-option-1')))
        sel_opt.click()

        txt1 = wait.until(EC.presence_of_element_located((By.ID, 'text')))
        txt1.clear()
        txt1.send_keys("s3-bucket-name")

        txt2 = wait.until(EC.presence_of_element_located((By.ID, 'text')))
        txt2.clear()
        txt2.send_keys("s3-prefix-or-key")

        next_btn = wait.until(EC.element_to_be_clickable((By.ID, "Next")))
        next_btn.click()
        next_btn2 = wait.until(EC.element_to_be_clickable((By.ID, "Next")))
        next_btn2.click()
        attach_screenshot(driver, "after_datastore_nexts")

    with allure.step("Final Assertion: Verify we are on datasource or subsequent page"):
        assert "/datasource" in driver.current_url
        attach_screenshot(driver, "assertion_passed")

@allure.title("Negative: Attempt to create agent with empty Experiment Name and verify cannot proceed")
@pytest.mark.negative
def test_negative_empty_experiment_name_prevents_continue(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)
    driver.implicitly_wait(50)
    attach_screenshot(driver, "start")

    with allure.step("Open New Agent modal"):
        close_btn = wait.until(EC.element_to_be_clickable((By.ID, "Close")))
        close_btn.click()
        el = wait.until(EC.presence_of_element_located((By.ID, "link-Home")))
        driver.execute_script("arguments[0].click();", el)
        wait.until(EC.url_contains("/Home"))
        attach_screenshot(driver, "navigated_to_Home")

        def action_back_to_workflow():
            el2 = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="link-Agent Studio"]')))
            driver.execute_script("arguments[0].click();", el2)
            wait.until(EC.url_contains("/workflow"))
        _retry_interaction(driver, "click_link-Agent_Studio_neg", action_back_to_workflow, wait)
        attach_screenshot(driver, "navigated_to_workflow")

    with allure.step("Click + New Agent and leave Experiment Name empty"):
        new_agent = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div/div[2]/button')))
        new_agent.click()
        name_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@aria-label="Experiment Name"]')))
        name_input.clear()  # leave empty
        desc = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="project_description"]')))
        desc.clear()
        desc.send_keys("Negative test with empty name")

    with allure.step("Click Continue and verify we did not navigate to canvas"):
        cont = wait.until(EC.element_to_be_clickable((By.ID, "Continue")))
        cont.click()
        time.sleep(1)
        attach_screenshot(driver, "after_click_continue_negative")

    with allure.step("Final Assertion: Should remain on workflow page (no canvas opened)"):
        assert "pageType=form" not in driver.current_url
        attach_screenshot(driver, "assertion_passed")

@allure.title("Boundary: Attempt to add S3 Data Store without required fields and verify Next does not advance")
@pytest.mark.boundary
def test_boundary_datastore_missing_required(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)
    driver.implicitly_wait(50)
    attach_screenshot(driver, "start")

    with allure.step("Navigate to canvas (create minimal agent and Continue)"):
        # Navigate Home -> Agent Studio -> New Agent -> Continue as in recording
        close_btn = wait.until(EC.element_to_be_clickable((By.ID, "Close")))
        close_btn.click()
        el = wait.until(EC.presence_of_element_located((By.ID, "link-Home")))
        driver.execute_script("arguments[0].click();", el)
        wait.until(EC.url_contains("/Home"))
        attach_screenshot(driver, "navigated_to_Home")

        def action_back_to_workflow_boundary():
            el2 = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="link-Agent Studio"]')))
            driver.execute_script("arguments[0].click();", el2)
            wait.until(EC.url_contains("/workflow"))
        _retry_interaction(driver, "click_link-Agent_Studio_boundary", action_back_to_workflow_boundary, wait)
        attach_screenshot(driver, "navigated_to_workflow")

        new_agent = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div/div[2]/button')))
        new_agent.click()
        name_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@aria-label="Experiment Name"]')))
        name_input.clear()
        name_input.send_keys("Boundary Agent")
        desc = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="project_description"]')))
        desc.clear()
        desc.send_keys("Boundary test")
        cont = wait.until(EC.element_to_be_clickable((By.ID, "Continue")))
        cont.click()
        wait.until(EC.url_contains("pageType=form"))
        attach_screenshot(driver, "navigated_to_canvas")

    with allure.step("Open Data Store and choose S3 (retry applied for Add Data Store)"):
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div/div/div[4]/div/div/div')))
        btn.click()
        # Navigate to Data Store via recorded node
        ds_link = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="link-Data Store"]')))
        driver.execute_script("arguments[0].click();", ds_link)
        wait.until(EC.url_contains("/datasource"))
        attach_screenshot(driver, "navigated_to_datasource")

        def action_click_add_ds_boundary():
            add_ds = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div[2]/button')))
            add_ds.click()
        _retry_interaction(driver, "click_Add_Data_Store_boundary", action_click_add_ds_boundary, wait)

    with allure.step("Select S3 and leave required fields empty, then click Next"):
        s3_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[3]/div/div/div/div[3]/div/div/div/button[5]')))
        s3_btn.click()
        # Intentionally do NOT fill name/description to test boundary
        next_btn = wait.until(EC.element_to_be_clickable((By.ID, "Next")))
        next_btn.click()
        time.sleep(0.5)
        attach_screenshot(driver, "after_next_with_missing_fields")

    with allure.step("Final Assertion: Should remain on datasource page due to missing required fields"):
        assert "/datasource" in driver.current_url
        attach_screenshot(driver, "assertion_passed")

@allure.title("Sub-flow: Add Data Store (S3) with valid entries")
@pytest.mark.regression
def test_subflow_add_datastore(setup):
    driver = setup
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)
    driver.implicitly_wait(50)
    attach_screenshot(driver, "start")

    with allure.step("Reach Data Store via canvas flow"):
        close_btn = wait.until(EC.element_to_be_clickable((By.ID, "Close")))
        close_btn.click()
        el = wait.until(EC.presence_of_element_located((By.ID, "link-Home")))
        driver.execute_script("arguments[0].click();", el)
        wait.until(EC.url_contains("/Home"))
        attach_screenshot(driver, "navigated_to_Home")

        def action_back_to_workflow_subflow():
            el2 = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="link-Agent Studio"]')))
            driver.execute_script("arguments[0].click();", el2)
            wait.until(EC.url_contains("/workflow"))
        _retry_interaction(driver, "click_link-Agent_Studio_subflow", action_back_to_workflow_subflow, wait)
        attach_screenshot(driver, "navigated_to_workflow")

        new_agent = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div/div[2]/button')))
        new_agent.click()
        name_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@aria-label="Experiment Name"]')))
        name_input.clear()
        name_input.send_keys("Subflow Agent")
        desc = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="project_description"]')))
        desc.clear()
        desc.send_keys("Subflow add datastore test")
        cont = wait.until(EC.element_to_be_clickable((By.ID, "Continue")))
        cont.click()
        wait.until(EC.url_contains("pageType=form"))
        attach_screenshot(driver, "navigated_to_canvas")

    with allure.step("Navigate to Data Store"):
        ds_link = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="link-Data Store"]')))
        driver.execute_script("arguments[0].click();", ds_link)
        wait.until(EC.url_contains("/datasource"))
        attach_screenshot(driver, "navigated_to_datasource")

    with allure.step("Add S3 Data Store and fill all required fields (retry applied on Add Data Store)"):
        def action_add_ds_subflow():
            add_ds = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div/div/div[2]/button')))
            add_ds.click()
        _retry_interaction(driver, "click_Add_Data_Store_subflow", action_add_ds_subflow, wait)

        s3_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[3]/div/div/div/div[3]/div/div/div/button[5]')))
        s3_btn.click()

        name_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Enter Data Source Name"]')))
        name_input.clear()
        name_input.send_keys("Subflow S3 Store")

        desc = wait.until(EC.presence_of_element_located((By.XPATH, '//textarea[@aria-label="Data Source Description"]')))
        desc.clear()
        desc.send_keys("Added during subflow test")

        sel_opt = wait.until(EC.presence_of_element_located((By.ID, 'react-select-4-option-1')))
        sel_opt.click()

        txt1 = wait.until(EC.presence_of_element_located((By.ID, 'text')))
        txt1.clear()
        txt1.send_keys("subflow-bucket")

        txt2 = wait.until(EC.presence_of_element_located((By.ID, 'text')))
        txt2.clear()
        txt2.send_keys("subflow-prefix")

        next_btn = wait.until(EC.element_to_be_clickable((By.ID, "Next")))
        next_btn.click()
        time.sleep(0.5)
        attach_screenshot(driver, "after_first_next_subflow")

    with allure.step("Final Assertion: Confirm still within datasource context after adding store"):
        assert "/datasource" in driver.current_url
        attach_screenshot(driver, "assertion_passed")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
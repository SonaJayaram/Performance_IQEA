import time

import pytest
import allure
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from output.page_file_generator.page_file_mckesson.Mckesson.mckesson_compression_gloves import mckesson_compression_gloves
from output.page_file_generator.page_file_mckesson.Mckesson.mckesson_exam_gloves import mckesson_exam_gloves
from output.page_file_generator.page_file_mckesson.Mckesson.mckesson_finger_cots import mckesson_finger_cots
from output.page_file_generator.page_file_mckesson.Mckesson.mckesson_Glove_Liners import mckesson_Glove_Liners
from output.page_file_generator.page_file_mckesson.Mckesson.Mckesson_home_1 import Mckesson_home_1


# ---------------- FIXTURE ----------------
@pytest.fixture(scope="function")
def driver_setup():
    options = Options()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    home_page = Mckesson_home_1(driver)
    compression_gloves_page = mckesson_compression_gloves(driver)
    exam_gloves_page = mckesson_exam_gloves(driver)
    finger_cots_page = mckesson_finger_cots(driver)
    glove_liners_page = mckesson_Glove_Liners(driver)

    yield (
        driver,
        home_page,
        compression_gloves_page,
        exam_gloves_page,
        finger_cots_page,
        glove_liners_page,
    )

    driver.quit()


# ---------------- HELPERS ----------------
def helper_click_element_1(driver, element, step_name):
    with allure.step(step_name):
        try:
            element.click()
        except Exception:
            driver.execute_script("arguments[0].click();", element)
        finally:
            allure.attach(
                driver.get_screenshot_as_png(),
                name=step_name,
                attachment_type=allure.attachment_type.PNG,
            )

def helper_click_element(driver, element, step_name):
    with allure.step(f"Clicking on element: {step_name}"):
        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(element)).click()
            allure.attach(driver.get_screenshot_as_png(), name=f"{step_name}_clicked", attachment_type=allure.attachment_type.PNG)
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name=f"{step_name}_error", attachment_type=allure.attachment_type.PNG)
            raise e
# ---------------- TESTS ----------------
def test_navigate_to_compression_gloves(driver_setup):
    driver, home_page, compression_gloves_page, _, _, _ = driver_setup

    base_url = "https://mms.mckesson.com/shop-products"

    with allure.step("Open base URL"):
        driver.get(base_url)
        time.sleep(5)

    with allure.step("Open Gloves"):
        home_page.click_glove().click()

    with allure.step("Navigate to Compression Gloves"):
        compression_gloves_page.open_compression_gloves_page()

    assert "Compression Gloves" in driver.title


def test_navigate_to_exam_gloves(driver_setup):
    driver, home_page, _, exam_gloves_page, _, _ = driver_setup

    base_url = "https://mms.mckesson.com/shop-products"

    with allure.step("Open base URL"):
        driver.get(base_url)
        time.sleep(5)

    with allure.step("Open Gloves"):
        home_page.click_glove().click()
    with allure.step("Navigate to Exam Gloves"):
        exam_gloves_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, exam_gloves_page.get_exam_gloves_link())
            )
        )
        helper_click_element(driver, exam_gloves_link, "Navigate to Exam Gloves")

    assert "Exam Gloves" in driver.title


def test_navigate_to_finger_cots(driver_setup):
    driver, home_page, _, _, finger_cots_page, _ = driver_setup

    base_url = "https://mms.mckesson.com/shop-products"

    with allure.step("Open base URL"):
        driver.get(base_url)
        time.sleep(5)

    with allure.step("Open Gloves"):
        home_page.click_glove().click()
    with (allure.step("Navigate to Finger Cots")):
        finger_cots_link =WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, finger_cots_page.open_fingers_cots())
            )
        )

        helper_click_element(driver, finger_cots_link, "Navigate to Finger Cots")

    assert "Finger Cots" in driver.title


def test_navigate_to_glove_liners(driver_setup):
    driver, home_page, _, _, _, glove_liners_page = driver_setup

    base_url = "https://mms.mckesson.com/shop-products"

    with allure.step("Open base URL"):
        driver.get(base_url)
        time.sleep(5)

    with allure.step("Open Gloves"):
        home_page.click_glove().click()
    with allure.step("Navigate to Glove Liners"):
        glove_liner_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, glove_liners_page.click_glove_liner_flow())
            )
        )
        helper_click_element(driver, glove_liner_link, "Navigate to Glove Liners")

    assert "Glove Liners" in driver.title

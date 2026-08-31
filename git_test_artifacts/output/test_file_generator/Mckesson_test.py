import time

import pytest
import allure
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from output.page_file_generator.Mckesson_Home import Mckesson_Home
from output.page_file_generator.Mckesson_compare import Mckesson_compare
from output.page_file_generator.Mckesson_product import Mckesson_product

@pytest.fixture(scope="function")
def driver():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    home_page = Mckesson_Home(driver)
    compare_page = Mckesson_compare(driver)
    product_page = Mckesson_product(driver)
    yield driver, home_page, compare_page, product_page
    driver.quit()

def switch_to_new_window(driver, timeout=10):
    with allure.step("Switching to new window"):
        WebDriverWait(driver, timeout).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])

def helper_click_element(driver, element, step_name):
    with allure.step(f"Clicking on element: {step_name}"):
        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(element)).click()
            allure.attach(driver.get_screenshot_as_png(), name=f"{step_name}_clicked", attachment_type=allure.attachment_type.PNG)
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name=f"{step_name}_error", attachment_type=allure.attachment_type.PNG)
            raise e

def helper_enter_text(driver, element, text, step_name):
    with allure.step(f"Entering text '{text}' into element: {step_name}"):
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located(element))
            element.clear()
            element.send_keys(text)
            allure.attach(driver.get_screenshot_as_png(), name=f"{step_name}_text_entered", attachment_type=allure.attachment_type.PNG)
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name=f"{step_name}_error", attachment_type=allure.attachment_type.PNG)
            raise e

@pytest.mark.usefixtures("driver")
def test_compare_two_products(driver):
    driver, home_page, compare_page, product_page = driver
    base_url = "https://mms.mckesson.com/shop-products"

    with allure.step("Navigating to base URL"):
        driver.get(base_url)
        time.sleep(5)
        allure.attach(driver.get_screenshot_as_png(), name="base_url_loaded", attachment_type=allure.attachment_type.PNG)

    # with allure.step("Clicking on search icon"):
    #     home_page.get_search_icon().click()


    # with allure.step("Entering 'Gloves' in search input"):
    #     search_input = home_page.get_search_input()
    #     search_input.send_keys("Gloves")
    #     #helper_enter_text(driver, search_input, "Gloves", "Search Input")
    #
    # with allure.step("Clicking on search button"):
    #     home_page.get_search_button().click()
    #     allure.attach(driver.get_screenshot_as_png(), name="search_button_clicked", attachment_type=allure.attachment_type.PNG)
    with allure.step("Clicking on glove  button"):
        home_page.get_gloves_button().click()
        allure.attach(driver.get_screenshot_as_png(), name="get_gloves_button", attachment_type=allure.attachment_type.PNG)

    with allure.step("Clicking on 'Impact Gloves'"):
        helper_click_element(driver, (By.XPATH, "//a[contains(text(), 'Exam Gloves')]"), "Impact Gloves")

    with allure.step("Clicking on 'COMPARE' button for first product"):
        home_page.get_compare_button_first().click()
        allure.attach(driver.get_screenshot_as_png(), name="compare_button_clicked", attachment_type=allure.attachment_type.PNG)

    with allure.step("Clicking on 'COMPARE' button for second product"):
        home_page.get_compare_button_second().click()
        allure.attach(driver.get_screenshot_as_png(), name="compare_button_clicked_2", attachment_type=allure.attachment_type.PNG)

    with allure.step("Clicking on 'COMPARE PRODUCTS' link"):
        compare_page.get_compare_products_link().click()
        allure.attach(driver.get_screenshot_as_png(), name="compare_products_link_clicked", attachment_type=allure.attachment_type.PNG)

    with allure.step("Verifying comparison page is displayed"):
        WebDriverWait(driver, 10).until(EC.url_contains("compare"))
        allure.attach(driver.get_screenshot_as_png(), name="comparison_page_loaded", attachment_type=allure.attachment_type.PNG)
        assert "compare" in driver.current_url, "Comparison page did not load as expected."
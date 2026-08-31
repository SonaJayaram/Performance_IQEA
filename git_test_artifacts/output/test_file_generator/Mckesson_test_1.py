import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import allure
from allure_commons.types import AttachmentType
from output.page_file_generator.Mckesson_Home import Mckesson_Home
from output.page_file_generator.Mckesson_compare import Mckesson_compare
from output.page_file_generator.Mckesson_product import Mckesson_product

@pytest.fixture(scope="function")
def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    home_page = Mckesson_Home(driver)
    compare_page = Mckesson_compare(driver)
    product_page = Mckesson_product(driver)
    yield driver, home_page, compare_page, product_page
    driver.quit()

def switch_to_new_window(driver, timeout=10):
    WebDriverWait(driver, timeout).until(lambda d: len(d.window_handles) > 1)
    driver.switch_to.window(driver.window_handles[-1])

def helper_click_element(driver, element, step_name):
    with allure.step(f"Click on element: {step_name}"):
        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, element)))
            driver.find_element(By.XPATH, element).click()
            allure.attach(driver.get_screenshot_as_png(), name=f"{step_name}_clicked", attachment_type=AttachmentType.PNG)
        except Exception as e:
            try:
                driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, element))
                allure.attach(driver.get_screenshot_as_png(), name=f"{step_name}_js_clicked", attachment_type=AttachmentType.PNG)
            except Exception as js_e:
                allure.attach(driver.get_screenshot_as_png(), name=f"{step_name}_error", attachment_type=AttachmentType.PNG)
                raise js_e

def helper_enter_text(driver, element, text, step_name):
    with allure.step(f"Enter text '{text}' in element: {step_name}"):
        try:
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, element)))
            input_field = driver.find_element(By.XPATH, element)
            input_field.clear()
            input_field.send_keys(text)
            allure.attach(driver.get_screenshot_as_png(), name=f"{step_name}_text_entered", attachment_type=AttachmentType.PNG)
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name=f"{step_name}_error", attachment_type=AttachmentType.PNG)
            raise e

@pytest.mark.usefixtures("setup_driver")
def test_compare_two_products(setup_driver):
    driver, home_page, compare_page, product_page = setup_driver
    base_url = "https://mms.mckesson.com/shop-products"

    with allure.step("Navigate to base URL"):
        driver.get(base_url)
        allure.attach(driver.get_screenshot_as_png(), name="Base_URL_Loaded", attachment_type=AttachmentType.PNG)

    with allure.step("Click on search icon"):
        home_page.get_search_icon().click()
        allure.attach(driver.get_screenshot_as_png(), name="Search_Icon_Clicked", attachment_type=AttachmentType.PNG)

    with allure.step("Enter 'Gloves' in search input"):
        helper_enter_text(driver, home_page.get_search_input(), "Gloves", "Search_Input")

    with allure.step("Click on search button"):
        home_page.get_search_button().click()
        allure.attach(driver.get_screenshot_as_png(), name="Search_Button_Clicked", attachment_type=AttachmentType.PNG)

    with allure.step("Click on first product compare button"):
        home_page.get_compare_button_first().click()
        allure.attach(driver.get_screenshot_as_png(), name="First_Product_Compare_Clicked", attachment_type=AttachmentType.PNG)

    with allure.step("Click on second product compare button"):
        home_page.get_compare_button_second().click()
        allure.attach(driver.get_screenshot_as_png(), name="Second_Product_Compare_Clicked", attachment_type=AttachmentType.PNG)

    with allure.step("Click on compare products link"):
        home_page.get_compare_products().click()
        allure.attach(driver.get_screenshot_as_png(), name="Compare_Products_Link_Clicked", attachment_type=AttachmentType.PNG)

    with allure.step("Switch to new window for comparison"):
        switch_to_new_window(driver)
        allure.attach(driver.get_screenshot_as_png(), name="Switched_To_New_Window", attachment_type=AttachmentType.PNG)

    with allure.step("Verify comparison page is displayed"):
        assert compare_page.get_compare_button().is_displayed(), "Comparison page is not displayed"
        allure.attach(driver.get_screenshot_as_png(), name="Comparison_Page_Displayed", attachment_type=AttachmentType.PNG)
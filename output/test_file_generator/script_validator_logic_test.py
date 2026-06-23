import pytest
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import allure
from allure_commons.types import AttachmentType
from output.page_file_generator.Mckesson_home_1 import Mckesson_home_1
from output.page_file_generator.mckesson_Glove_Liners import mckesson_Glove_Liners
from output.page_file_generator.mckesson_finger_cots import mckesson_finger_cots
from output.page_file_generator.mckesson_exam_gloves import mckesson_exam_gloves
from output.page_file_generator.mckesson_compression_gloves import mckesson_compression_gloves

@pytest.fixture(scope="function")
def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    home_page = Mckesson_home_1(driver)
    glove_liners_page = mckesson_Glove_Liners(driver)
    finger_cots_page = mckesson_finger_cots(driver)
    exam_gloves_page = mckesson_exam_gloves(driver)
    compression_gloves_page = mckesson_compression_gloves(driver)
    yield driver, home_page, glove_liners_page, finger_cots_page, exam_gloves_page, compression_gloves_page
    driver.quit()

@pytest.mark.usefixtures("setup_driver")
def test_verify_navigation_to_finger_cots_by_size(setup_driver):
    driver, home_page, glove_liners_page, finger_cots_page, exam_gloves_page, compression_gloves_page = setup_driver
    base_url = "https://mms.mckesson.com/shop-products"
    driver.get(base_url)

    # with allure.step("Accept cookies"):
    #     try:
    #         glove_liners_page.accept_cookies()
    #         allure.attach(driver.get_screenshot_as_png(), name="accept_cookies", attachment_type=AttachmentType.PNG)
    #     except Exception as e:
    #         allure.attach(driver.get_screenshot_as_png(), name="accept_cookies_failed", attachment_type=AttachmentType.PNG)
    #         raise e

    with allure.step("Click on Gloves"):
        try:
            home_page.click_glove()
            allure.attach(driver.get_screenshot_as_png(), name="click_glove", attachment_type=AttachmentType.PNG)
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name="click_glove_failed", attachment_type=AttachmentType.PNG)
            raise e

    with allure.step("Click on Finger Cots"):
        try:
            finger_cots_page.get_finger_cots_link().click()
            allure.attach(driver.get_screenshot_as_png(), name="click_finger_cots", attachment_type=AttachmentType.PNG)
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name="click_finger_cots_failed", attachment_type=AttachmentType.PNG)
            raise e

    with allure.step("Verify navigation to Finger Cots page"):
        try:
            assert "Finger Cots" in driver.title
            allure.attach(driver.get_screenshot_as_png(), name="verify_finger_cots_page", attachment_type=AttachmentType.PNG)
        except AssertionError as e:
            allure.attach(driver.get_screenshot_as_png(), name="verify_finger_cots_page_failed", attachment_type=AttachmentType.PNG)
            raise e

@pytest.mark.usefixtures("setup_driver")
def test_verify_navigation_to_exam_gloves_by_size(setup_driver):
    driver, home_page, glove_liners_page, finger_cots_page, exam_gloves_page, compression_gloves_page = setup_driver
    base_url = "https://mms.mckesson.com/shop-products"
    driver.get(base_url)

    # with allure.step("Accept cookies"):
    #     try:
    #         exam_gloves_page.get_accept_cookies_button().click()
    #         allure.attach(driver.get_screenshot_as_png(), name="accept_cookies", attachment_type=AttachmentType.PNG)
    #     except Exception as e:
    #         allure.attach(driver.get_screenshot_as_png(), name="accept_cookies_failed", attachment_type=AttachmentType.PNG)
    #         raise e

    with allure.step("Click on Gloves"):
        try:
            home_page.click_glove()
            allure.attach(driver.get_screenshot_as_png(), name="click_glove", attachment_type=AttachmentType.PNG)
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name="click_glove_failed", attachment_type=AttachmentType.PNG)
            raise e

    with allure.step("Click on Exam Gloves"):
        try:
            exam_gloves_page.get_exam_gloves_link().click()
            allure.attach(driver.get_screenshot_as_png(), name="click_exam_gloves", attachment_type=AttachmentType.PNG)
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name="click_exam_gloves_failed", attachment_type=AttachmentType.PNG)
            raise e

    with allure.step("Verify navigation to Exam Gloves page"):
        try:
            assert "Exam Gloves" in driver.title
            allure.attach(driver.get_screenshot_as_png(), name="verify_exam_gloves_page", attachment_type=AttachmentType.PNG)
        except AssertionError as e:
            allure.attach(driver.get_screenshot_as_png(), name="verify_exam_gloves_page_failed", attachment_type=AttachmentType.PNG)
            raise e

@pytest.mark.usefixtures("setup_driver")
def test_verify_navigation_to_compression_gloves(setup_driver):
    driver, home_page, glove_liners_page, finger_cots_page, exam_gloves_page, compression_gloves_page = setup_driver
    base_url = "https://mms.mckesson.com/shop-products"
    driver.get(base_url)

    # with allure.step("Accept cookies"):
    #     try:
    #         compression_gloves_page.get_accept_cookies_button().click()
    #         allure.attach(driver.get_screenshot_as_png(), name="accept_cookies", attachment_type=AttachmentType.PNG)
    #     except Exception as e:
    #         allure.attach(driver.get_screenshot_as_png(), name="accept_cookies_failed", attachment_type=AttachmentType.PNG)
    #         raise e

    with allure.step("Click on Gloves"):
        try:
            home_page.click_glove()
            allure.attach(driver.get_screenshot_as_png(), name="click_glove", attachment_type=AttachmentType.PNG)
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name="click_glove_failed", attachment_type=AttachmentType.PNG)
            raise e

    with allure.step("Click on Compression Gloves"):
        try:
            compression_gloves_page.open_compression_gloves_page()
            allure.attach(driver.get_screenshot_as_png(), name="click_compression_gloves", attachment_type=AttachmentType.PNG)
        except Exception as e:
            allure.attach(driver.get_screenshot_as_png(), name="click_compression_gloves_failed", attachment_type=AttachmentType.PNG)
            raise e

    with allure.step("Verify navigation to Compression Gloves page"):
        try:
            assert "Compression Gloves" in driver.title
            allure.attach(driver.get_screenshot_as_png(), name="verify_compression_gloves_page", attachment_type=AttachmentType.PNG)
        except AssertionError as e:
            allure.attach(driver.get_screenshot_as_png(), name="verify_compression_gloves_page_failed", attachment_type=AttachmentType.PNG)
            raise e
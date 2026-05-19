from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import allure
from output.page_file_generator.Equfix_home_page_palywright import EqufixHomePage
from output.page_file_generator.Equfix_Place_On_Alert_selenium import EqufixPlaceOnAlert

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 20)

@allure.title("TC01 - Place an Alert - Successful Form Submission")
def test_place_alert_successful_submission():
    driver.get("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/")
    home_page = EqufixHomePage(driver)
    place_alert_page = EqufixPlaceOnAlert(driver)

    home_page.enter_banner_description("Equifax and its partners use Cookies and similar technologies as necessary to provide digital services and for advertising and targeting, analytics and performance, and functionality and personalization purposes. For more information, please review our Privacy Statement.")
    home_page.close_banner()

    home_page.place_alert()

    home_page.switch_to_new_window()
    wait.until(EC.visibility_of_element_located((By.ID, "firstName")))
    place_alert_page.enter_first_name("test")
    place_alert_page.enter_last_name("test")
    place_alert_page.enter_ssn("***-**-6686")
    place_alert_page.enter_phone_number("786-876-****")
    place_alert_page.enter_dob("04/22/1990")
    place_alert_page.enter_address("test")
    place_alert_page.enter_address_line2("test")
    place_alert_page.enter_city("test")
    place_alert_page.click_efx_dropdown()
    place_alert_page.enter_zip("78686")
    place_alert_page.click_continue_button()

    time.sleep(2)
    driver.quit()
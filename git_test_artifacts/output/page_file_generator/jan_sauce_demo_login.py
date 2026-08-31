from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class jan_sauce_demo_login:
    def __init__(self, driver):
        self.driver = driver

    def get_element(self, by, locator, timeout=10):
        return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, locator)))

    def get_user_name_input(self):
        return self.get_element(By.ID, "user-name")

    def get_password_input(self):
        return self.get_element(By.ID, "password")

    def get_login_button(self):
        return self.get_element(By.ID, "login-button")

    def get_add_to_cart_button(self):
        return self.get_element(By.ID, "add-to-cart-sauce-labs-backpack")

    def get_cart_count(self):
        return self.get_element(By.CLASS_NAME, "shopping_cart_badge")

    def get_checkout_button(self):
        return self.get_element(By.ID, "checkout")

    def get_first_name_input(self):
        return self.get_element(By.ID, "first-name")

    def get_last_name_input(self):
        return self.get_element(By.ID, "last-name")

    def get_postal_code_input(self):
        return self.get_element(By.ID, "postal-code")

    def get_continue_button(self):
        return self.get_element(By.ID, "continue")

    def get_finish_button(self):
        return self.get_element(By.ID, "finish")

    def get_back_to_products_button(self):
        return self.get_element(By.ID, "back-to-products")

    def get_menu_button(self):
        return self.get_element(By.ID, "react-burger-menu-btn")

    def get_all_items_link(self):
        return self.get_element(By.ID, "inventory_sidebar_link")

    def get_logout_link(self):
        return self.get_element(By.ID, "logout_sidebar_link")
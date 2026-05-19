from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class InventorySauceDemo:
    LOCATORS = {
        "react_burger_menu_btn": (By.XPATH, "//button[@id='react-burger-menu-btn']"),
        "shopping_cart_link": (By.XPATH, "//a[@class='shopping_cart_link']"),
        "add_to_cart_sauce_labs_backpack": (By.XPATH, "//button[@id='add-to-cart-sauce-labs-backpack']"),
        "add_to_cart_sauce_labs_bike_light": (By.XPATH, "//button[@id='add-to-cart-sauce-labs-bike-light']"),
        "add_to_cart_sauce_labs_bolt_t_shirt": (By.XPATH, "//button[@id='add-to-cart-sauce-labs-bolt-t-shirt']"),
        "add_to_cart_sauce_labs_fleece_jacket": (By.XPATH, "//button[@id='add-to-cart-sauce-labs-fleece-jacket']"),
        "add_to_cart_sauce_labs_onesie": (By.XPATH, "//button[@name='add-to-cart-sauce-labs-onesie']"),
        "add_to_cart_test_allthethings_t_shirt_red": (By.XPATH, "//button[@id='add-to-cart-test.allthethings()-t-shirt-(red)']"),
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def navigate(self):
        self.driver.get("https://www.saucedemo.com/")

    def get_react_burger_menu_btn(self):
        locator = self.LOCATORS.get("react_burger_menu_btn")
        if locator is None:
            raise RuntimeError("Locator 'react_burger_menu_btn' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def get_shopping_cart_link(self):
        locator = self.LOCATORS.get("shopping_cart_link")
        if locator is None:
            raise RuntimeError("Locator 'shopping_cart_link' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def get_add_to_cart_sauce_labs_backpack(self):
        locator = self.LOCATORS.get("add_to_cart_sauce_labs_backpack")
        if locator is None:
            raise RuntimeError("Locator 'add_to_cart_sauce_labs_backpack' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def get_add_to_cart_sauce_labs_bike_light(self):
        locator = self.LOCATORS.get("add_to_cart_sauce_labs_bike_light")
        if locator is None:
            raise RuntimeError("Locator 'add_to_cart_sauce_labs_bike_light' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def get_add_to_cart_sauce_labs_bolt_t_shirt(self):
        locator = self.LOCATORS.get("add_to_cart_sauce_labs_bolt_t_shirt")
        if locator is None:
            raise RuntimeError("Locator 'add_to_cart_sauce_labs_bolt_t_shirt' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def get_add_to_cart_sauce_labs_fleece_jacket(self):
        locator = self.LOCATORS.get("add_to_cart_sauce_labs_fleece_jacket")
        if locator is None:
            raise RuntimeError("Locator 'add_to_cart_sauce_labs_fleece_jacket' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def get_add_to_cart_sauce_labs_onesie(self):
        locator = self.LOCATORS.get("add_to_cart_sauce_labs_onesie")
        if locator is None:
            raise RuntimeError("Locator 'add_to_cart_sauce_labs_onesie' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def get_add_to_cart_test_allthethings_t_shirt_red(self):
        locator = self.LOCATORS.get("add_to_cart_test_allthethings_t_shirt_red")
        if locator is None:
            raise RuntimeError("Locator 'add_to_cart_test_allthethings_t_shirt_red' not found in LOCATORS")
        return self.wait.until(EC.element_to_be_clickable(locator))

    def click_react_burger_menu_btn(self):
        self.get_react_burger_menu_btn().click()

    def click_shopping_cart_link(self):
        self.get_shopping_cart_link().click()

    def click_add_to_cart_sauce_labs_backpack(self):
        self.get_add_to_cart_sauce_labs_backpack().click()

    def click_add_to_cart_sauce_labs_bike_light(self):
        self.get_add_to_cart_sauce_labs_bike_light().click()

    def click_add_to_cart_sauce_labs_bolt_t_shirt(self):
        self.get_add_to_cart_sauce_labs_bolt_t_shirt().click()

    def click_add_to_cart_sauce_labs_fleece_jacket(self):
        self.get_add_to_cart_sauce_labs_fleece_jacket().click()

    def click_add_to_cart_sauce_labs_onesie(self):
        self.get_add_to_cart_sauce_labs_onesie().click()

    def click_add_to_cart_test_allthethings_t_shirt_red(self):
        self.get_add_to_cart_test_allthethings_t_shirt_red().click()

    def switch_to_new_window(self, timeout: int = 10):
        import time
        deadline = time.time() + timeout
        while time.time() < deadline:
            if len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                return
            time.sleep(0.5)
        raise RuntimeError("New window did not appear within timeout")

    def switch_to_main_window(self):
        self.driver.switch_to.window(self.driver.window_handles[0])

class InventoryPage:
    def __init__(self, driver):
        self.driver = driver
        self.add_to_cart_backpack = "//button[@id='add-to-cart-sauce-labs-backpack']"
        self.add_to_cart_bike_light = "//button[@id='add-to-cart-sauce-labs-bike-light']"
        self.add_to_cart_bolt_tshirt = "//button[@id='add-to-cart-sauce-labs-bolt-t-shirt' and text()='Add to cart']"
        self.remove_backpack = "//button[@id='remove-sauce-labs-backpack']"
        self.sorting_option = "//select[@data-test='product_sort_container']"
        self.hamburger_menu = "//button[@id='react-burger-menu-btn']"
        self.close_menu = "//button[@id='react-burger-cross-btn']"

    def click_add_to_cart_backpack(self):
        add_to_cart_button = self.driver.find_element("xpath", self.add_to_cart_backpack)
        add_to_cart_button.click()

    def click_add_to_cart_bike_light(self):
        add_to_cart_button = self.driver.find_element("xpath", self.add_to_cart_bike_light)
        add_to_cart_button.click()

    def click_add_to_cart_bolt_tshirt(self):
        add_to_cart_button = self.driver.find_element("xpath",self.add_to_cart_bolt_tshirt)
        add_to_cart_button.click()

    def click_remove_backpack(self):
        remove_button = self.driver.find_element("xpath",self.remove_backpack)
        remove_button.click()

    def select_sorting_option(self, visible_text):
        sorting_dropdown = self.driver.find_element("xpath", self.sorting_option)
        from selenium.webdriver.support.ui import Select
        select = Select(sorting_dropdown)
        select.select_by_visible_text(visible_text)

    def click_hamburger_menu(self):
        menu_button = self.driver.find_element("xpath", self.hamburger_menu)
        menu_button.click()

    def click_close_menu(self):
        close_button = self.driver.find_element("xpath", self.close_menu)
        close_button.click()


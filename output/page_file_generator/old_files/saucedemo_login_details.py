class LoginPage:
    def __init__(self, driver):
        self.driver = driver
        self.user_name_xpath = "//input[@id='user-name']"
        self.password_xpath = "//input[@id='password']"
        self.login_button_xpath = "//input[@id='login-button']"

    def enter_username(self, username):
        user_name_field = self.driver.find_element("xpath", self.user_name_xpath)
        user_name_field.click()
        user_name_field.clear()
        user_name_field.send_keys(username)

    def enter_password(self, password):
        password_field = self.driver.find_element("xpath", self.password_xpath)
        password_field.clear()
        password_field.send_keys(password)

    def click_login_button(self):
        login_button = self.driver.find_element("xpath", self.login_button_xpath)
        login_button.click()
class LoginPage:

    def __init__(self, driver):
        self.driver = driver
        self.username_input_xpath = "//input[@id='user-name']"
        self.password_input_xpath = "//input[@id='password']"
        self.login_button_xpath = "//input[@id='login-button']"

    def enter_username(self, username):
        username_input = self.driver.find_element("xpath", self.username_input_xpath)
        username_input.clear()
        username_input.send_keys(username)

    def enter_password(self, password):
        password_input = self.driver.find_element("xpath", self.password_input_xpath)
        password_input.clear()
        password_input.send_keys(password)

    def click_login_button(self):
        login_button = self.driver.find_element("xpath", self.login_button_xpath)
        login_button.click()
Feature: Sauce Demo Website Basic Functionality

  Background:
    Given the user is on the Sauce Demo login page

  Scenario: Successful login with valid credentials
    When the user enters username "standard_user" and password "secret_sauce"
    And the user clicks the login button
    Then the user should be redirected to the inventory page
    And the inventory items should be displayed

  Scenario: Add a product to the shopping cart
    Given the user is logged in with username "standard_user" and password "secret_sauce"
    When the user adds the first product to the cart
    Then the shopping cart badge should show "1"
    And the cart icon should indicate 1 item

  Scenario: Checkout process with valid details
    Given the user has added a product to the cart
    When the user clicks on the shopping cart
    And the user clicks the checkout button
    And the user enters first name "John"
    And the user enters last name "Doe"
    And the user enters postal code "12345"
    And the user clicks the continue button
    And the user clicks the finish button
    Then the order confirmation message should be displayed

  Scenario: Logout from the application
    Given the user is logged in with username "standard_user" and password "secret_sauce"
    When the user opens the menu
    And the user clicks the logout link
    Then the user should be redirected to the login page

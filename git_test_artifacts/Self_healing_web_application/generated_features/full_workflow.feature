Feature: Checkout and Logout Workflow

  Background:
    Given I navigate to "https://www.saucedemo.com/"
    And I log in with username "standard_user" and password "secret_sauce"

  Scenario: Add product to cart and view cart
    When I add the "Sauce Labs Backpack" product to the cart
    And I open the cart
    Then I should see "Sauce Labs Backpack" in the cart
    And the cart badge should display "1"

  Scenario: Proceed to checkout from cart
    Given I am viewing my cart
    When I click the "checkout" button
    Then I should be on the checkout information page

  Scenario: Enter checkout information
    Given I am on the checkout information page
    When I enter first name "test"
    And I enter last name "teest"
    And I enter postal code "7657"
    And I click the "continue" button
    Then I should be on the checkout overview page

  Scenario: Complete the checkout
    Given I am on the checkout overview page
    When I click the "finish" button
    Then I should be on the checkout complete page
    And I should see an order confirmation

  Scenario: Return to products
    Given I am on the checkout complete page
    When I click the "back to products" button
    Then I should be on the inventory page

  Scenario: Logout
    Given I am on the inventory page
    When I open the side menu
    And I click the "logout" link
    Then I should be redirected to the login page
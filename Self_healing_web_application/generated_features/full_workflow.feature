Feature: Purchase a product from Saucedemo

  Background:
    Given I navigate to "https://www.saucedemo.com/"
    When I enter "standard_user" in the "user-name" field
    And I enter "secret_sauce" in the "password" field
    And I click on "login-button"
    Then I should be on the inventory page

  Scenario: Add a product to the cart
    When I click on "add-to-cart-sauce-labs-backpack"
    Then the product should be added to the cart

  Scenario: View the cart
    When I click on "1"
    Then I should be on the cart page

  Scenario: Proceed to checkout
    When I click on "checkout"
    Then I should be on the checkout information page

  Scenario: Enter checkout information
    When I enter "test" in the "firstName" field
    And I enter "test" in the "lastName" field
    And I enter "67857" in the "postalCode" field
    And I click on "continue"
    Then I should be on the checkout summary page

  Scenario: Complete the checkout
    When I click on "checkout_summary_container"
    And I click on "finish"
    Then I should see the order confirmation on the checkout complete page

  Scenario: Return to the product page
    When I click on "back-to-products"
    Then I should be on the inventory page

  Scenario: Logout
    When I click on "react-burger-menu-btn"
    And I click on "logout_sidebar_link"
    Then I should be logged out and redirected to the login page
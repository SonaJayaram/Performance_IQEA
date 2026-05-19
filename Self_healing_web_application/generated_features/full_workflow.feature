Feature: User Login and Navigation

  Background:
    Given I navigate to "https://www.saucedemo.com/"
    When I enter "standard_user" in the "user-name" field
    And I enter "secret_sauce" in the "password" field
    And I click on "login-button"

  Scenario: Navigate to Inventory Page
    Then I should be on the inventory page
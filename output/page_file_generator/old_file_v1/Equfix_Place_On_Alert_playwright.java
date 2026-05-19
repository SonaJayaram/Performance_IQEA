import com.microsoft.playwright.Locator;
import com.microsoft.playwright.Page;

public class Equfix_Place_On_Alert {
    private Page page;

    // Locators
    private Locator continueButton;
    private Locator zipField;
    private Locator stateDropdown;
    private Locator cityField;
    private Locator addressLine2Field;
    private Locator addressField;
    private Locator phoneNumberField;
    private Locator ssnField;
    private Locator dobField;
    private Locator lastNameField;
    private Locator firstNameField;

    // Constructor
    public Equfix_Place_On_Alert(Page page) {
        this.page = page;
        this.continueButton = page.locator("xpath=//button[@id='continue-button']");
        this.zipField = page.locator("xpath=//input[@id='zip']");
        this.stateDropdown = page.locator("xpath=//button[@id='efx-dropdown-label-753393']");
        this.cityField = page.locator("xpath=//input[@id='city']");
        this.addressLine2Field = page.locator("xpath=//input[@id='addressLine2Id']");
        this.addressField = page.locator("xpath=//input[@id='address']");
        this.phoneNumberField = page.locator("xpath=//input[@id='phoneNumber']");
        this.ssnField = page.locator("xpath=//input[@id='ssn']");
        this.dobField = page.locator("xpath=//input[@id='dob']");
        this.lastNameField = page.locator("xpath=//input[@id='lastName']");
        this.firstNameField = page.locator("xpath=//input[@id='firstNameId']");
    }

    // Helper Methods
    private void waitForElement(Locator locator) {
        locator.waitFor();
    }

    private void click(Locator locator) {
        waitForElement(locator);
        locator.click();
    }

    private void enterText(Locator locator, String text) {
        waitForElement(locator);
        locator.fill(text);
    }

    private void switchToWindowByIndex(int index) {
        page.context().pages().get(index).bringToFront();
    }

    private void switchToWindowByHandle(String handle) {
        page.context().pages().stream().filter(p -> p.browserContext().browser().newContext().toString().equals(handle))
                .findFirst().ifPresent(Page::bringToFront);
    }

    private void switchToWindowMatchingUrl(String url) {
        for (Page p : page.context().pages()) {
            if (p.url().equals(url)) {
                p.bringToFront();
                return;
            }
        }
    }

    private void switchToNewWindow(String url) {
        int initialPageCount = page.context().pages().size();
        Page newPage = page.context().waitForEvent("page", p -> page.context().pages().size() > initialPageCount);
        if (!newPage.url().equals(url)) {
            throw new RuntimeException("New window URL does not match expected URL: " + url);
        }
        newPage.bringToFront();
    }

    // Action Methods
    public void switchToEquifaxFraudAlertPage(String url) {
        switchToWindowMatchingUrl(url);
    }

    public void setBannerDescription(String text) {
        Locator bannerDescription = page.locator("xpath=//*[@id='banner-description']");
        enterText(bannerDescription, text);
    }

    public void clickBannerCloseButton() {
        Locator closeButton = page.locator("xpath=//*[@class='ketch-h-6 ketch-w-6 !ketch-fill-[--k-banner-header-returnButton-icon-color]']");
        click(closeButton);
    }

    public void clickPlaceAnAlertButton() {
        Locator placeAlertButton = page.locator("xpath=//*[text()='Place an Alert']");
        click(placeAlertButton);
    }

    public void fillFirstName(String firstName) {
        enterText(this.firstNameField, firstName);
    }

    public void fillLastName(String lastName) {
        enterText(this.lastNameField, lastName);
    }

    public void fillSSN(String ssn) {
        enterText(this.ssnField, ssn);
    }

    public void fillPhoneNumber(String phoneNumber) {
        enterText(this.phoneNumberField, phoneNumber);
    }

    public void fillDOB(String dob) {
        enterText(this.dobField, dob);
    }

    public void fillAddress(String address) {
        enterText(this.addressField, address);
    }

    public void fillCity(String city) {
        enterText(this.cityField, city);
    }

    public void fillAddressLine2(String addressLine2) {
        enterText(this.addressLine2Field, addressLine2);
    }

    public void selectState(String state) {
        click(this.stateDropdown);
        Locator option = page.locator("xpath=//li[text()='" + state + "']");
        click(option);
    }

    public void fillZip(String zip) {
        enterText(this.zipField, zip);
    }

    public void navigateToAboutUs(String url) {
        switchToWindowMatchingUrl(url);
        Locator aboutUsLink = page.locator("xpath=//*[contains(@id, 'aboutus')]");
        click(aboutUsLink);
    }
}
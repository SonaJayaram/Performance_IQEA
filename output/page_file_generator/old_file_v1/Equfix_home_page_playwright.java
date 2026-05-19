import com.microsoft.playwright.Locator;
import com.microsoft.playwright.Page;

public class Equfix_home_page {
    private Page page;

    // Locators
    private Locator placeAnAlertButton;
    private Locator closeButton;
    private Locator firstNameInput;
    private Locator ssnInput;
    private Locator lastNameInput;
    private Locator phoneNumberInput;
    private Locator dateOfBirthInput;
    private Locator addressLine1Input;
    private Locator cityNameInput;
    private Locator addressLine2Input;
    private Locator stateDropDown;
    private Locator zipCodeInput;
    private Locator learnButton;
    private Locator businessButton;
    private Locator apiDeveloperPortalButton;
    private Locator becomeCustomerButton;
    private Locator userGuideButton;
    private Locator registerButton;
    private Locator firstNameRegisterInput;
    private Locator lastNameRegisterInput;
    private Locator companyRegisterInput;
    private Locator emailRegisterInput;
    private Locator aboutUsButton;
    private Locator leadershipButton;
    private Locator boardOfDirectorsTab;

    // Constructor
    public Equfix_home_page(Page page) {
        this.page = page;

        // Initialize locators
        this.placeAnAlertButton = page.locator("//a[contains(@class, 'btn') and text()='PLACE AN ALERT']");
        this.closeButton = page.locator("//button[@name='close']");
        this.firstNameInput = page.locator("xpath=//input[@id='firstName']");
        this.ssnInput = page.locator("xpath=//input[@id='ssn']");
        this.lastNameInput = page.locator("xpath=//input[@id='lastName']");
        this.phoneNumberInput = page.locator("xpath=//input[@id='phoneNumber']");
        this.dateOfBirthInput = page.locator("xpath=//input[@id='dateOfBirthMasked']");
        this.addressLine1Input = page.locator("xpath=//input[@id='addressLine1']");
        this.cityNameInput = page.locator("xpath=//input[@id='cityName']");
        this.addressLine2Input = page.locator("xpath=//input[@id='addressLine2']");
        this.stateDropDown = page.locator("xpath=//div[@id='efx-dropdown-label-372614']");
        this.zipCodeInput = page.locator("xpath=//input[@id='zipCode']");
        this.learnButton = page.locator("xpath=//button[@id='learn']");
        this.businessButton = page.locator("xpath=//button[@id='Business']");
        this.apiDeveloperPortalButton = page.locator("xpath=//button[@id='API Developer Portal']");
        this.becomeCustomerButton = page.locator("xpath=//button[text()='Become a Customer']");
        this.userGuideButton = page.locator("xpath=//button[text()='User Guide']");
        this.registerButton = page.locator("xpath=//button[@id='register']");
        this.firstNameRegisterInput = page.locator("xpath=//input[@id='first_name[0][value]']");
        this.lastNameRegisterInput = page.locator("xpath=//input[@id='last_name[0][value]']");
        this.companyRegisterInput = page.locator("xpath=//input[@id='field_company[0][value]']");
        this.emailRegisterInput = page.locator("xpath=//input[@id='mail']");
        this.aboutUsButton = page.locator("xpath=//button[@id='aboutus']");
        this.leadershipButton = page.locator("xpath=//button[@id='Leadership']");
        this.boardOfDirectorsTab = page.locator("xpath=//button[@id='tab-1420970-1']");
    }

    // Helper methods
    public void waitForElement(Locator locator) {
        locator.waitFor();
    }

    public void click(Locator locator) {
        waitForElement(locator);
        locator.click();
    }

    public void enterText(Locator locator, String text) {
        waitForElement(locator);
        locator.fill(text);
    }

    public void switchToWindowByIndex(int index) {
        page.context().pages().get(index).bringToFront();
    }

    public void switchToWindowByHandle(String handle) {
        for (Page p : page.context().pages()) {
            if (p.context().toString().equals(handle)) {
                p.bringToFront();
                break;
            }
        }
    }

    public void switchToWindowMatchingUrl(String url) {
        for (Page p : page.context().pages()) {
            if (p.url().equals(url)) {
                p.bringToFront();
                break;
            }
        }
    }

    public void switchToNewWindow(String url) {
        int existingCount = page.context().pages().size();
        page.context().waitForEvent("page", () -> {
            // Waits for a new page to be opened
        });
        for (Page newPage : page.context().pages()) {
            if (newPage.url().equals(url)) {
                newPage.bringToFront();
                break;
            }
        }
    }

    // Action methods
    public void clickPlaceAnAlert() {
        click(placeAnAlertButton);
    }

    public void clickClose() {
        click(closeButton);
    }

    public void fillFirstName(String firstName) {
        enterText(firstNameInput, firstName);
    }

    public void fillSSN(String ssn) {
        enterText(ssnInput, ssn);
    }

    public void fillLastName(String lastName) {
        enterText(lastNameInput, lastName);
    }

    public void fillPhoneNumber(String phoneNumber) {
        enterText(phoneNumberInput, phoneNumber);
    }

    public void fillDateOfBirth(String dob) {
        enterText(dateOfBirthInput, dob);
    }

    public void fillAddressLine1(String addressLine1) {
        enterText(addressLine1Input, addressLine1);
    }

    public void fillCity(String cityName) {
        enterText(cityNameInput, cityName);
    }

    public void fillAddressLine2(String addressLine2) {
        enterText(addressLine2Input, addressLine2);
    }

    public void selectState(String state) {
        click(stateDropDown);
        enterText(stateDropDown, state);
    }

    public void fillZipCode(String zipCode) {
        enterText(zipCodeInput, zipCode);
    }

    public void clickLearnButton() {
        click(learnButton);
    }

    public void clickBusinessButton() {
        click(businessButton);
    }

    public void clickAPIDeveloperPortal() {
        click(apiDeveloperPortalButton);
    }

    public void clickBecomeCustomerButton() {
        click(becomeCustomerButton);
    }

    public void clickUserGuideButton() {
        click(userGuideButton);
    }

    public void clickRegisterButton() {
        click(registerButton);
    }

    public void fillRegisterFirstName(String firstName) {
        enterText(firstNameRegisterInput, firstName);
    }

    public void fillRegisterLastName(String lastName) {
        enterText(lastNameRegisterInput, lastName);
    }

    public void fillRegisterCompany(String company) {
        enterText(companyRegisterInput, company);
    }

    public void fillRegisterEmail(String email) {
        enterText(emailRegisterInput, email);
    }

    public void clickAboutUs() {
        click(aboutUsButton);
    }

    public void clickLeadership() {
        click(leadershipButton);
    }

    public void clickBoardOfDirectorsTab() {
        click(boardOfDirectorsTab);
    }
}
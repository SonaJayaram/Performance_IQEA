import com.microsoft.playwright.Locator;
import com.microsoft.playwright.Page;

public class Equfix_Place_On_Alert {

    private Page page;
    private Locator continueButton;
    private Locator zip;
    private Locator efxDropdownLabel753393;
    private Locator city;
    private Locator addressLine2Id;
    private Locator address;
    private Locator phoneNumber;
    private Locator ssn;
    private Locator dob;
    private Locator lastName;
    private Locator firstNameId;

    public Equfix_Place_On_Alert(Page page) {
        this.page = page;
        this.continueButton = page.locator("xpath=//button[@id='continue-button']");
        this.zip = page.locator("xpath=//input[@id='zip']");
        this.efxDropdownLabel753393 = page.locator("xpath=//button[@id='efx-dropdown-label-753393']");
        this.city = page.locator("xpath=//input[@id='city']");
        this.addressLine2Id = page.locator("xpath=//input[@id='addressLine2Id']");
        this.address = page.locator("xpath=//input[@id='address']");
        this.phoneNumber = page.locator("xpath=//input[@id='phoneNumber']");
        this.ssn = page.locator("xpath=//input[@id='ssn']");
        this.dob = page.locator("xpath=//input[@id='dob']");
        this.lastName = page.locator("xpath=//input[@id='lastName']");
        this.firstNameId = page.locator("xpath=//input[@id='firstNameId']");
    }

    private void waitForElement(Locator locator) {
        if (!locator.isVisible()) {
            throw new RuntimeException("Element not visible: " + locator);
        }
    }

    public Page switchToNewWindow(Page page) {
        return page.context().pages().get(page.context().pages().size() - 1);
    }

    public void clickContinueButton() {
        waitForElement(continueButton);
        continueButton.click();
    }

    public void enterZip(String zipCode) {
        waitForElement(zip);
        zip.fill(zipCode);
    }

    public void clickEfxDropdownLabel() {
        waitForElement(efxDropdownLabel753393);
        efxDropdownLabel753393.click();
    }

    public void enterCity(String cityName) {
        waitForElement(city);
        city.fill(cityName);
    }

    public void enterAddressLine2(String addressLine2) {
        waitForElement(addressLine2Id);
        addressLine2Id.fill(addressLine2);
    }

    public void enterAddress(String addressText) {
        waitForElement(address);
        address.fill(addressText);
    }

    public void enterPhoneNumber(String phone) {
        waitForElement(phoneNumber);
        phoneNumber.fill(phone);
    }

    public void enterSsn(String socialSecurityNumber) {
        waitForElement(ssn);
        ssn.fill(socialSecurityNumber);
    }

    public void enterDob(String dateOfBirth) {
        waitForElement(dob);
        dob.fill(dateOfBirth);
    }

    public void enterLastName(String lastNameText) {
        waitForElement(lastName);
        lastName.fill(lastNameText);
    }

    public void enterFirstName(String firstName) {
        waitForElement(firstNameId);
        firstNameId.fill(firstName);
    }

    public void selectState(String state) {
        waitForElement(efxDropdownLabel753393);
        efxDropdownLabel753393.click();
        Locator stateOption = page.locator("xpath=//li[text()='" + state + "']");
        waitForElement(stateOption);
        stateOption.click();
    }

    public void performPlaceOnAlertActions() {
        Page newWindow;

        newWindow = switchToNewWindow(page);
        clickEfxDropdownLabel();
        newWindow.locator("xpath=//button[contains(text(),'Place an Alert')]").click();

        enterSsn("***-**-7575");
        enterLastName("test");
        enterPhoneNumber("768-676-****");
        enterDob("04/22/1990");
        enterAddress("test");
        enterCity("test");
        enterAddressLine2("test");
        selectState("Alaska");
        enterZip("67567");
    }
}
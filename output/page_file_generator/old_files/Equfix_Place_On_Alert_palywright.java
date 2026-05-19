import com.microsoft.playwright.Locator;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.BrowserContext;
import com.microsoft.playwright.Page.WaitForSelectorOptions;

import java.util.ArrayList;
import java.util.List;

public class EquifixFlowActions {

    private Page page;

    private Locator continueButton;
    private Locator zip;
    private Locator efxDropdownLabel;
    private Locator city;
    private Locator addressLine2;
    private Locator address;
    private Locator phoneNumber;
    private Locator ssn;
    private Locator dob;
    private Locator lastName;
    private Locator firstNameId;

    public EquifixFlowActions(Page page) {
        this.page = page;
        this.continueButton = page.locator("//button[@id='continue-button']");
        this.zip = page.locator("//input[@id='zip']");
        this.efxDropdownLabel = page.locator("//button[@id='efx-dropdown-label-753393']");
        this.city = page.locator("//input[@id='city']");
        this.addressLine2 = page.locator("//input[@id='addressLine2Id']");
        this.address = page.locator("//input[@id='address']");
        this.phoneNumber = page.locator("//input[@id='phoneNumber']");
        this.ssn = page.locator("//input[@id='ssn']");
        this.dob = page.locator("//input[@id='dob']");
        this.lastName = page.locator("//input[@id='lastName']");
        this.firstNameId = page.locator("//input[@id='firstNameId']");
    }

    private void waitForElement(Locator locator) {
        locator.waitFor(new WaitForSelectorOptions().setState(WaitForSelectorOptions.State.ATTACHED));
    }

    private void click(Locator locator) {
        locator.click();
    }

    private void enterText(Locator locator, String text) {
        locator.fill(text);
    }

    private void switchToWindowByIndex(int index) {
        List<Page> pages = new ArrayList<>(page.context().pages());
        if (index >= pages.size()) {
            throw new RuntimeException("Invalid window index: " + index);
        }
        page = pages.get(index);
    }

    private void switchToWindowByHandle(String handle) {
        List<Page> pages = new ArrayList<>(page.context().pages());
        for (Page p : pages) {
            if (p.mainFrame().url().equals(handle)) {
                page = p;
                return;
            }
        }
        throw new RuntimeException("No window with handle: " + handle);
    }

    private void switchToWindowMatchingUrl(String url) {
        List<Page> pages = new ArrayList<>(page.context().pages());
        for (Page p : pages) {
            if (p.url().equals(url)) {
                page = p;
                return;
            }
        }
        throw new RuntimeException("No window with URL: " + url);
    }

    private void switchToNewWindow(String url) {
        List<Page> pages = new ArrayList<>(page.context().pages());
        page.context().waitForEvent("page");
        Page newPage = pages.get(pages.size() - 1);
        if (!newPage.url().equals(url)) {
            throw new RuntimeException("New window with URL not found: " + url);
        }
        page = newPage;
    }

    public void enterFirstName(String firstName) {
        waitForElement(firstNameId);
        enterText(firstNameId, firstName);
    }
    
    public void clickSSNField() {
        waitForElement(ssn);
        click(ssn);
    }
    
    public void enterSSN(String ssnValue) {
        waitForElement(ssn);
        enterText(ssn, ssnValue);
    }

    public void clickLastNameField() {
        waitForElement(lastName);
        click(lastName);
    }

    public void enterLastName(String lastNameValue) {
        waitForElement(lastName);
        enterText(lastName, lastNameValue);
    }

    public void clickPhoneNumberField() {
        waitForElement(phoneNumber);
        click(phoneNumber);
    }

    public void enterPhoneNumber(String phoneValue) {
        waitForElement(phoneNumber);
        enterText(phoneNumber, phoneValue);
    }

    public void clickDOBField() {
        waitForElement(dob);
        click(dob);
    }

    public void enterDOB(String dobValue) {
        waitForElement(dob);
        enterText(dob, dobValue);
    }

    public void clickAddressField() {
        waitForElement(address);
        click(address);
    }

    public void enterAddress(String addressValue) {
        waitForElement(address);
        enterText(address, addressValue);
    }

    public void clickCityField() {
        waitForElement(city);
        click(city);
    }

    public void enterCity(String cityValue) {
        waitForElement(city);
        enterText(city, cityValue);
    }

    public void clickAddressLine2Field() {
        waitForElement(addressLine2);
        click(addressLine2);
    }

    public void enterAddressLine2(String addressLine2Value) {
        waitForElement(addressLine2);
        enterText(addressLine2, addressLine2Value);
    }

    public void clickZipCodeField() {
        waitForElement(zip);
        click(zip);
    }

    public void enterZipCode(String zipCodeValue) {
        waitForElement(zip);
        enterText(zip, zipCodeValue);
    }

    public void clickContinueButton() {
        waitForElement(continueButton);
        click(continueButton);
    }

    public void selectState(String state) {
        waitForElement(efxDropdownLabel);
        click(efxDropdownLabel);
        Locator stateOption = page.locator("//button[@id='efx-dropdown-label-" + state + "']");
        waitForElement(stateOption);
        click(stateOption);
    }
}
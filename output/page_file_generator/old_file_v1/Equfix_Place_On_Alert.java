import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.By;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.openqa.selenium.support.PageFactory;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.How;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

public class Equfix_Place_On_Alert {

    private WebDriver driver;
    private WebDriverWait wait;

    @FindBy(how = How.XPATH, using = "//button[@id='continue-button']")
    private WebElement continueButton;

    @FindBy(how = How.XPATH, using = "//input[@id='zip']")
    private WebElement zip;

    @FindBy(how = How.XPATH, using = "//button[@id='efx-dropdown-label-753393']")
    private WebElement dropdownLabel;

    @FindBy(how = How.XPATH, using = "//input[@id='city']")
    private WebElement city;

    @FindBy(how = How.XPATH, using = "//input[@id='addressLine2Id']")
    private WebElement addressLine2;

    @FindBy(how = How.XPATH, using = "//input[@id='address']")
    private WebElement address;

    @FindBy(how = How.XPATH, using = "//input[@id='phoneNumber']")
    private WebElement phoneNumber;

    @FindBy(how = How.XPATH, using = "//input[@id='ssn']")
    private WebElement ssn;

    @FindBy(how = How.XPATH, using = "//input[@id='dob']")
    private WebElement dob;

    @FindBy(how = How.XPATH, using = "//input[@id='lastName']")
    private WebElement lastName;

    @FindBy(how = How.XPATH, using = "//input[@id='firstNameId']")
    private WebElement firstName;

    public Equfix_Place_On_Alert(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(20));
        PageFactory.initElements(driver, this);
    }

    private void waitForElement(WebElement element) {
        wait.until(ExpectedConditions.visibilityOf(element));
    }

    private void click(WebElement element) {
        waitForElement(element);
        element.click();
    }

    private void enterText(WebElement element, String text) {
        waitForElement(element);
        element.clear();
        element.sendKeys(text);
    }

    private void switchToWindowByIndex(int index) {
        List<String> windowHandles = new ArrayList<>(driver.getWindowHandles());
        if (index < windowHandles.size()) {
            driver.switchTo().window(windowHandles.get(index));
        }
    }

    private void switchToWindowByHandle(String handle) {
        driver.switchTo().window(handle);
    }

    private void switchToWindowMatchingUrl(String url) {
        for (String handle : driver.getWindowHandles()) {
            driver.switchTo().window(handle);
            if (driver.getCurrentUrl().equals(url)) {
                return;
            }
        }
    }

    private void switchToNewWindow(String url) {
        List<String> existingHandles = new ArrayList<>(driver.getWindowHandles());
        driver.getWindowHandles().stream().filter(handle -> !existingHandles.contains(handle)).findFirst().ifPresent(handle -> {
            driver.switchTo().window(handle);
            if (!driver.getCurrentUrl().equals(url)) {
                throw new RuntimeException("The new window URL does not match the expected URL: " + url);
            }
        });
    }

    public void clickContinueButton() {
        click(continueButton);
    }

    public void enterZipCode(String text) {
        enterText(zip, text);
    }

    public void clickDropdownLabel() {
        click(dropdownLabel);
    }

    public void enterCity(String text) {
        enterText(city, text);
    }

    public void enterAddressLine2(String text) {
        enterText(addressLine2, text);
    }

    public void enterAddress(String text) {
        enterText(address, text);
    }

    public void enterPhoneNumber(String text) {
        enterText(phoneNumber, text);
    }

    public void enterSSN(String text) {
        enterText(ssn, text);
    }

    public void enterDob(String text) {
        enterText(dob, text);
    }

    public void enterLastName(String text) {
        enterText(lastName, text);
    }

    public void enterFirstName(String text) {
        enterText(firstName, text);
    }

    public void performEquifixFlowActions() {
        // Example implementation for complex recorded actions:
        // This method will sequence all interactions from your recorded actions
        enterFirstName("test");
        click(ssn);
        enterSSN("***-**-6686");
        click(lastName);
        enterLastName("test");
        click(phoneNumber);
        enterPhoneNumber("786-876-****");
        click(dob);
        enterDob("04/22/1990");
        click(address);
        enterAddress("test");
        click(city);
        enterCity("test");
        click(addressLine2);
        enterAddressLine2("test");
        // Similarly, continue other actions from recorded actions
    }
}
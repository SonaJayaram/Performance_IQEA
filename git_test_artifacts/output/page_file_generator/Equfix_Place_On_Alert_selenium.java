import org.openqa.selenium.*;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.How;
import org.openqa.selenium.support.PageFactory;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.openqa.selenium.support.ui.ExpectedConditions;
import java.time.Duration;
import java.util.List;
import java.util.ArrayList;

public class Equfix_Place_On_Alert {

    private WebDriver driver;
    private WebDriverWait wait;

    @FindBy(how = How.XPATH, using = "//button[@id='continue-button']")
    private WebElement continueButton;

    @FindBy(how = How.XPATH, using = "//input[@id='zip']")
    private WebElement zipCode;

    @FindBy(how = How.XPATH, using = "//button[@id='efx-dropdown-label-753393']")
    private WebElement stateDropdown;

    @FindBy(how = How.XPATH, using = "//input[@id='city']")
    private WebElement cityName;

    @FindBy(how = How.XPATH, using = "//input[@id='addressLine2Id']")
    private WebElement addressLine2;

    @FindBy(how = How.XPATH, using = "//input[@id='address']")
    private WebElement addressLine1;

    @FindBy(how = How.XPATH, using = "//input[@id='phoneNumber']")
    private WebElement phoneNumber;

    @FindBy(how = How.XPATH, using = "//input[@id='ssn']")
    private WebElement ssn;

    @FindBy(how = How.XPATH, using = "//input[@id='dob']")
    private WebElement dateOfBirthMasked;

    @FindBy(how = How.XPATH, using = "//input[@id='lastName']")
    private WebElement lastName;

    @FindBy(how = How.XPATH, using = "//input[@id='firstNameId']")
    private WebElement firstNameId;

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

    public void switchToNewWindow() {
        List<String> handles = new ArrayList<>(driver.getWindowHandles());
        if (handles.size() > 1) {
            driver.switchTo().window(handles.get(handles.size() - 1));
        }
    }

    public void clickContinueButton() {
        click(continueButton);
    }

    public void enterZipCode(String zip) {
        enterText(zipCode, zip);
    }

    public void clickStateDropdown() {
        click(stateDropdown);
    }

    public void enterCityName(String city) {
        enterText(cityName, city);
    }

    public void enterAddressLine2(String address) {
        enterText(addressLine2, address);
    }

    public void enterAddressLine1(String address) {
        enterText(addressLine1, address);
    }

    public void enterPhoneNumber(String phone) {
        enterText(phoneNumber, phone);
    }

    public void enterSSN(String socialSecurityNumber) {
        enterText(ssn, socialSecurityNumber);
    }

    public void enterDateOfBirth(String dob) {
        enterText(dateOfBirthMasked, dob);
    }

    public void enterLastName(String lastNameVal) {
        enterText(lastName, lastNameVal);
    }
}
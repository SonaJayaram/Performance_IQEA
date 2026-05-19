import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.By;
import org.openqa.selenium.support.PageFactory;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.How;
import java.time.Duration;
import java.util.Set;

public class EquifaxPage {

    private WebDriver driver;
    private WebDriverWait wait;

    @FindBy(how = How.XPATH, using = "//button[@id='continue-button']")
    private WebElement continueButton;

    @FindBy(how = How.XPATH, using = "//input[@id='zip']")
    private WebElement zip;

    @FindBy(how = How.XPATH, using = "//button[@id='efx-dropdown-label-753393']")
    private WebElement dropdownCity;

    @FindBy(how = How.XPATH, using = "//input[@id='city']")
    private WebElement city;

    @FindBy(how = How.XPATH, using = "//input[@id='addressLine2Id']")
    private WebElement addressLine2;

    @FindBy(how = How.XPATH, using = "//input[@id='address']")
    private WebElement addressLine1;

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

    public EquifaxPage(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(20));
        PageFactory.initElements(driver, this);
    }

    public void waitForElement(WebElement element) {
        wait.until(ExpectedConditions.visibilityOf(element));
    }

    public void click(WebElement element) {
        waitForElement(element);
        element.click();
    }

    public void enterText(WebElement element, String text) {
        waitForElement(element);
        element.clear();
        element.sendKeys(text);
    }

    public void switchToWindowByIndex(int index) {
        Set<String> windowHandles = driver.getWindowHandles();
        String[] handles = windowHandles.toArray(new String[0]);
        if (index < windowHandles.size()) {
            driver.switchTo().window(handles[index]);
        } else {
            throw new RuntimeException("Invalid window index: " + index);
        }
    }

    public void switchToWindowByHandle(String handle) {
        driver.switchTo().window(handle);
    }

    public void switchToWindowMatchingUrl(String url) {
        for (String handle : driver.getWindowHandles()) {
            driver.switchTo().window(handle);
            if (driver.getCurrentUrl().equals(url)) {
                return;
            }
        }
        throw new RuntimeException("No window matching URL: " + url);
    }

    public void switchToNewWindow(String expectedUrl) {
        String currentHandle = driver.getWindowHandle();
        Set<String> windowHandles = driver.getWindowHandles();
        for (String handle : windowHandles) {
            if (!handle.equals(currentHandle)) {
                driver.switchTo().window(handle);
                if (driver.getCurrentUrl().contains(expectedUrl)) {
                    return;
                }
            }
        }
        throw new RuntimeException("Failed to switch to new window with URL: " + expectedUrl);
    }

    public void clickContinueButton() {
        click(continueButton);
    }

    public void enterZip(String zipCode) {
        enterText(zip, zipCode);
    }

    public void clickDropdownCity() {
        click(dropdownCity);
    }

    public void enterCity(String cityName) {
        enterText(city, cityName);
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

    public void clickSsn() {
        click(ssn);
    }

    public void enterSsn(String ssnValue) {
        enterText(ssn, ssnValue);
    }

    public void clickLastName() {
        click(lastName);
    }

    public void enterLastName(String lastNameValue) {
        enterText(lastName, lastNameValue);
    }

    public void clickFirstName() {
        click(firstName);
    }

    public void enterFirstName(String firstNameValue) {
        enterText(firstName, firstNameValue);
    }
}
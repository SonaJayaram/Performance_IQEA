import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.PageFactory;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.annotations.*;
import org.testng.Assert;
import io.qameta.allure.Allure;
import io.qameta.allure.Step;
import output.page_file_generator.Equfix_home_page_selenium;
import output.page_file_generator.Equfix_Place_On_Alert_selenium;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;

import java.io.ByteArrayInputStream;
import java.time.Duration;

public class PlaceAlertTests {

    private WebDriver driver;
    private WebDriverWait wait;
    private Equfix_home_page_selenium homePage;
    private Equfix_Place_On_Alert_selenium placeOnAlertPage;

    @BeforeClass
    public void setUp() {
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--start-maximized");
        driver = new ChromeDriver(options);
        wait = new WebDriverWait(driver, Duration.ofSeconds(20));
        driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(10));
        homePage = new Equfix_home_page_selenium(driver);
        placeOnAlertPage = new Equfix_Place_On_Alert_selenium(driver);
    }

    @AfterClass
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }

    @Test
    public void testPlaceAlertMissingLastName() {
        navigateToHomePage();
        homePage.switchToNewWindow();
        clickWithJS(homePage.getPlaceAlertButton());
        placeOnAlertPage.switchToNewWindow();

        placeOnAlertPage.enterSSN("***-**-7575");
        placeOnAlertPage.enterPhoneNumber("768-676-****");
        placeOnAlertPage.enterDateOfBirth("04/22/1990");
        placeOnAlertPage.enterAddressLine1("test");
        placeOnAlertPage.enterCityName("test");
        placeOnAlertPage.enterAddressLine2("test");
        clickWithJS(placeOnAlertPage.getStateDropdown());
        helper_selectState("Alaska");
        placeOnAlertPage.enterZipCode("67567");
        clickWithJS(placeOnAlertPage.getContinueButton());

        String errorMessage = wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath("//div[contains(text(),'Last Name is required')]"))).getText();
        Assert.assertEquals(errorMessage, "Last Name is required", "Error message for missing last name is incorrect.");
    }

    @Test
    public void testPlaceAlertInvalidPhoneNumber() {
        navigateToHomePage();
        homePage.switchToNewWindow();
        clickWithJS(homePage.getPlaceAlertButton());
        placeOnAlertPage.switchToNewWindow();

        placeOnAlertPage.enterSSN("***-**-7575");
        placeOnAlertPage.enterLastName("test");
        placeOnAlertPage.enterPhoneNumber("123");
        clickWithJS(placeOnAlertPage.getContinueButton());

        String errorMessage = wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath("//div[contains(text(),'Invalid phone number')]"))).getText();
        Assert.assertEquals(errorMessage, "Invalid phone number", "Error message for invalid phone number is incorrect.");
    }

    @Test
    public void testPlaceAlertInvalidSSN() {
        navigateToHomePage();
        homePage.switchToNewWindow();
        clickWithJS(homePage.getPlaceAlertButton());
        placeOnAlertPage.switchToNewWindow();

        placeOnAlertPage.enterSSN("123-45-678");
        clickWithJS(placeOnAlertPage.getContinueButton());

        String errorMessage = wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath("//div[contains(text(),'Invalid SSN')]"))).getText();
        Assert.assertEquals(errorMessage, "Invalid SSN", "Error message for invalid SSN is incorrect.");
    }

    @Step("Navigate to Equifax home page")
    private void navigateToHomePage() {
        driver.get("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/");
        Allure.addAttachment("screenshot", new ByteArrayInputStream(((TakesScreenshot) driver).getScreenshotAs(OutputType.BYTES)));
    }

    @Step("Click using JavaScript Executor")
    private void clickWithJS(WebElement element) {
        try {
            wait.until(ExpectedConditions.elementToBeClickable(element)).click();
        } catch (Exception e) {
            JavascriptExecutor js = (JavascriptExecutor) driver;
            js.executeScript("arguments[0].click();", element);
        }
    }

    @Step("Select state: {state}")
    private void helper_selectState(String state) {
        WebElement stateOption = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//option[text()='" + state + "']")));
        clickWithJS(stateOption);
    }
}
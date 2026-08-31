import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.openqa.selenium.support.PageFactory;
import io.qameta.allure.Step;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Set;

import output.page_file_generator.Equfix_home_page_selenium;
import output.page_file_generator.Equfix_Place_On_Alert_selenium;

public class TC01_PlaceAnAlert_SuccessfulFormSubmission {

    private WebDriver driver;
    private WebDriverWait wait;
    private Equfix_home_page_selenium homePage;
    private Equfix_Place_On_Alert_selenium placeOnAlertPage;

    public TC01_PlaceAnAlert_SuccessfulFormSubmission(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(20));
        this.homePage = new Equfix_home_page_selenium(driver);
        this.placeOnAlertPage = new Equfix_Place_On_Alert_selenium(driver);
        PageFactory.initElements(driver, this);
    }

    @Step("Execute test case: TC01 - Place an Alert - Successful Form Submission")
    public void executeTest() {
        switchToNewWindow("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/");
        homePage.updateBannerDescription("Equifax and its partners use Cookies and similar technologies as necessary to provide digital services and for advertising and targeting, analytics and performance, and functionality and personalization purposes. For more information, please review our Privacy Statement.");
        homePage.clickCloseButton();
        homePage.clickPlaceAnAlert();
        switchToNewWindow("https://my.equifax.com/consumer-registration/UCSC/#/personal-info");
        placeOnAlertPage.enterFirstName("test");
        placeOnAlertPage.clickSSN();
        placeOnAlertPage.enterSSN("***-**-6686");
        placeOnAlertPage.clickLastName();
        placeOnAlertPage.enterLastName("test");
        placeOnAlertPage.clickPhoneNumber();
        placeOnAlertPage.enterPhoneNumber("786-876-****");
        placeOnAlertPage.clickDob();
        placeOnAlertPage.enterDob("04/22/1990");
        placeOnAlertPage.clickAddress();
        placeOnAlertPage.enterAddress("test");
        placeOnAlertPage.clickCity();
        placeOnAlertPage.enterCity("test");
        placeOnAlertPage.clickAddressLine2();
        placeOnAlertPage.enterAddressLine2("test");
        placeOnAlertPage.clickDropdownLabel();
        placeOnAlertPage.clickContinueButton();
    }

    private void switchToNewWindow(String expectedUrl) {
        Set<String> existingWindows = driver.getWindowHandles();
        driver.switchTo().newWindow();
        Set<String> newWindows = driver.getWindowHandles();
        newWindows.removeAll(existingWindows);
        String newWindowHandle = newWindows.iterator().next();
        driver.switchTo().window(newWindowHandle);
        if (!driver.getCurrentUrl().equals(expectedUrl)) {
            throw new RuntimeException("New window does not have the expected URL: " + expectedUrl);
        }
    }
}
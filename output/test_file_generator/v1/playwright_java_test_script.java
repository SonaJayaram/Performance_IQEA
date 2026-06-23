
package tests;

import com.microsoft.playwright.*;
import com.microsoft.playwright.assertions.PlaywrightAssertions;
import io.qameta.allure.Allure;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;
import output.page_file_generator.Equfix_home_page_playwright;
import output.page_file_generator.Equfix_Place_On_Alert_playwright;

import java.io.ByteArrayInputStream;

public class TC01_PlaceAnAlert_SuccessfulFormSubmission {
    private Playwright playwright;
    private Browser browser;
    private BrowserContext context;
    private Page page;
    private Equfix_home_page_playwright homePage;
    private Equfix_Place_On_Alert_playwright alertPage;

    @BeforeClass
    public void setUp() {
        playwright = Playwright.create();
        browser = playwright.chromium().launch(new BrowserType.LaunchOptions().setHeadless(false));
        context = browser.newContext();
        page = context.newPage();
        homePage = new Equfix_home_page_playwright(page);
        alertPage = new Equfix_Place_On_Alert_playwright(page);
    }

    @Test
    public void testPlaceAnAlertSuccessfulFormSubmission() {
        Allure.step("Navigate to Equifax Fraud Alert page");
        page.navigate("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/");
        attachScreenshot("Navigated to Equifax Fraud Alert page");

        Allure.step("Click on 'Place an Alert' button");
        homePage.clickPlaceAnAlert();
        attachScreenshot("Clicked on 'Place an Alert' button");

        Allure.step("Switch to new window for placing an alert");
        Page alertPageWindow = context.waitForEvent("page", () -> {
            homePage.clickPlaceAnAlert();
        });
        alertPageWindow.bringToFront();
        attachScreenshot("Switched to new window for placing an alert");

        Allure.step("Fill in the form fields");
        alertPage.fillFirstName("test");
        attachScreenshot("Entered first name");
        alertPage.fillLastName("test");
        attachScreenshot("Entered last name");
        alertPage.fillSSN("***-**-6686");
        attachScreenshot("Entered SSN");
        alertPage.fillPhoneNumber("786-876-****");
        attachScreenshot("Entered phone number");
        alertPage.fillDOB("04/22/1990");
        attachScreenshot("Entered date of birth");
        alertPage.fillAddress("test");
        attachScreenshot("Entered address line 1");
        alertPage.fillCity("test");
        attachScreenshot("Entered city");
        alertPage.fillAddressLine2("test");
        attachScreenshot("Entered address line 2");
        alertPage.selectState("Alaska");
        attachScreenshot("Selected state");
        alertPage.fillZip("78686");
        attachScreenshot("Entered zip code");

        Allure.step("Click on 'Continue' button to submit the form");
        alertPage.clickContinueButton();
        attachScreenshot("Clicked on 'Continue' button");

        Allure.step("Verify successful form submission");
        PlaywrightAssertions.assertThat(alertPageWindow.locator("xpath=//h1[text()='Success']")).isVisible();
        attachScreenshot("Verified successful form submission");
    }

    @AfterClass
    public void tearDown() {
        if (context != null) {
            context.close();
        }
        if (browser != null) {
            browser.close();
        }
        if (playwright != null) {
            playwright.close();
        }
    }

    private void attachScreenshot(String stepDescription) {
        byte[] screenshot = page.screenshot(new Page.ScreenshotOptions().setFullPage(true));
        Allure.addAttachment(stepDescription, "image/png", new ByteArrayInputStream(screenshot), "png");
    }
}

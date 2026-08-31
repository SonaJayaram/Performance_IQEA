package tests;

import com.microsoft.playwright.*;
import com.microsoft.playwright.options.*;
import org.testng.annotations.*;
import io.qameta.allure.Allure;
import output.page_file_generator.Equfix_home_page_playwright;
import output.page_file_generator.Equfix_Place_On_Alert_playwright;

import java.io.ByteArrayInputStream;
import java.nio.file.Paths;

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
        attachScreenshot("Initial Page");

        Allure.step("Click on 'Place an Alert' button");
        homePage.clickPlaceAnAlert();
        attachScreenshot("Clicked Place an Alert");

        Allure.step("Switch to new window for personal info");
        Page personalInfoPage = context.waitForEvent("page", () -> {});
        personalInfoPage.bringToFront();
        alertPage = new Equfix_Place_On_Alert_playwright(personalInfoPage);

        Allure.step("Fill in personal information form");
        alertPage.fillFirstName("test");
        attachScreenshot("Filled First Name");
        alertPage.fillLastName("test");
        attachScreenshot("Filled Last Name");
        alertPage.fillSSN("***-**-6686");
        attachScreenshot("Filled SSN");
        alertPage.fillPhoneNumber("786-876-****");
        attachScreenshot("Filled Phone Number");
        alertPage.fillDOB("04/22/1990");
        attachScreenshot("Filled DOB");
        alertPage.fillAddress("test");
        attachScreenshot("Filled Address");
        alertPage.fillCity("test");
        attachScreenshot("Filled City");
        alertPage.fillAddressLine2("test");
        attachScreenshot("Filled Address Line 2");
        alertPage.selectState("Alaska");
        attachScreenshot("Selected State");
        alertPage.fillZip("78686");
        attachScreenshot("Filled Zip Code");

        Allure.step("Submit the form");
        alertPage.clickContinueButton();
        attachScreenshot("Form Submitted");

        Allure.step("Verify successful submission");
        String confirmationMessage = personalInfoPage.locator("xpath=//div[contains(text(), 'Thank you for placing an alert')]").textContent();
        assert confirmationMessage.contains("Thank you for placing an alert") : "Confirmation message not found!";
        attachScreenshot("Confirmation Message");
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

    private void attachScreenshot(String stepName) {
        byte[] screenshot = page.screenshot(new Page.ScreenshotOptions().setPath(Paths.get("screenshots/" + stepName + ".png")));
        Allure.addAttachment(stepName, "image/png", new ByteArrayInputStream(screenshot), "png");
    }
}
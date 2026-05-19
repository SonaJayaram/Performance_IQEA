import com.microsoft.playwright.*;
import com.microsoft.playwright.options.*;
import io.qameta.allure.Allure;
import org.testng.Assert;
import org.testng.annotations.*;

import java.io.ByteArrayInputStream;
import java.nio.file.Paths;
import java.util.Map;

public class TC02_PlaceAlert_InvalidSSN {

    private Playwright playwright;
    private Browser browser;
    private BrowserContext context;
    private Page page;

    @BeforeClass
    public void setup() {
        playwright = Playwright.create();
        browser = playwright.chromium().launch(new BrowserType.LaunchOptions().setHeadless(false));
        context = browser.newContext();
        page = context.newPage();
    }

    @Test
    public void testPlaceAlertInvalidSSN() {
        Allure.step("Navigate to Equifax homepage");
        page.navigate("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/");
        attachScreenshot("Homepage");

        Allure.step("Click on 'Place an Alert'");
        page.locator("text=Place an Alert").click();
        Page alertPage = context.waitForEvent("page", () -> {
            page.locator("text=Place an Alert").click();
        });
        attachScreenshot("Place Alert Page");

        Allure.step("Fill in personal information with invalid SSN");
        alertPage.locator("input[name='firstName']").fill("test");
        alertPage.locator("input[name='lastName']").fill("test");
        alertPage.locator("input[name='ssn']").fill("***-**-6686");
        alertPage.locator("input[name='phoneNumber']").fill("786-876-****");
        alertPage.locator("input[name='dateOfBirthMasked']").fill("04/22/1990");
        alertPage.locator("input[name='addressLine1']").fill("test");
        alertPage.locator("input[name='cityName']").fill("test");
        alertPage.locator("input[name='addressLine2']").fill("test");
        alertPage.locator("select[name='state']").selectOption("AK");
        alertPage.locator("input[name='zipCode']").fill("78686");
        attachScreenshot("Filled Form");

        Allure.step("Submit the form");
        alertPage.locator("button[type='submit']").click();

        Allure.step("Validate error message for invalid SSN");
        Locator errorMessage = alertPage.locator("text=Invalid SSN");
        errorMessage.waitFor(new Locator.WaitForOptions().setTimeout(5000));
        Assert.assertTrue(errorMessage.isVisible(), "Error message for invalid SSN is not visible");
        attachScreenshot("Error Message");
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
        byte[] screenshot = page.screenshot(new Page.ScreenshotOptions().setPath(Paths.get("allure-results", stepName + ".png")));
        Allure.addAttachment(stepName, "image/png", new ByteArrayInputStream(screenshot), "png");
    }
}
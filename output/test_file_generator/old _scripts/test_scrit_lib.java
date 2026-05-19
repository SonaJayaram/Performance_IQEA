import com.microsoft.playwright.*;
import com.microsoft.playwright.options.*;
import io.qameta.allure.*;
import org.testng.annotations.*;

import java.util.HashMap;
import java.util.Map;

@Epic("Equifax Automation")
@Feature("Place Alert Tests")
public class EquifaxPlaceAlertTests {

    private Playwright playwright;
    private Browser browser;
    private BrowserContext context;
    private Page page;
    private EqufixHomepage equfixHomepage;
    private EqufixPlaceOnAlert equfixPlaceOnAlert;

    @BeforeClass
    @Step("Setup Playwright and Browser")
    public void setup() {
        playwright = Playwright.create();
        browser = playwright.chromium().launch(new BrowserType.LaunchOptions().setHeadless(false));
        context = browser.newContext();
        page = context.newPage();
        equfixHomepage = new EqufixHomepage(page);
        equfixPlaceOnAlert = new EqufixPlaceOnAlert(page);
    }

    @AfterClass
    @Step("Close Playwright and Browser")
    public void teardown() {
        if (context != null) context.close();
        if (browser != null) browser.close();
        if (playwright != null) playwright.close();
    }

    @Test(description = "TC01 - Place Alert - Successful Data Entry")
    @Severity(SeverityLevel.CRITICAL)
    @Story("Place Alert with valid data")
    public void testPlaceAlertSuccessfulDataEntry() {
        Allure.step("Navigate to Equifax homepage");
        page.navigate("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/");

        Allure.step("Click on 'Place an Alert' button");
        equfixHomepage.clickPlaceAnAlert();

        Allure.step("Switch to new window for alert placement");
        Page alertPage = context.waitForEvent("page", () -> {
            equfixHomepage.switchToNewWindow();
        });

        Allure.step("Fill in alert placement form with valid data");
        Map<String, String> formData = new HashMap<>();
        formData.put("ssn", "***-**-7575");
        formData.put("lastName", "test");
        formData.put("phoneNumber", "768-676-****");
        formData.put("dateOfBirthMasked", "04/22/1990");
        formData.put("addressLine1", "test");
        formData.put("cityName", "test");
        formData.put("addressLine2", "test");
        formData.put("state", "Alaska");
        formData.put("zipCode", "67567");

        equfixPlaceOnAlert.performAlertPlacementFlow(formData);

        Allure.step("Verify successful alert placement");
        // Add assertion logic here based on expected results
    }

    @Test(description = "TC02 - Place Alert - Invalid SSN")
    @Severity(SeverityLevel.NORMAL)
    @Story("Place Alert with invalid SSN")
    public void testPlaceAlertInvalidSSN() {
        Allure.step("Navigate to Equifax homepage");
        page.navigate("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/");

        Allure.step("Click on 'Place an Alert' button");
        equfixHomepage.clickPlaceAnAlert();

        Allure.step("Switch to new window for alert placement");
        Page alertPage = context.waitForEvent("page", () -> {
            equfixHomepage.switchToNewWindow();
        });

        Allure.step("Fill in alert placement form with invalid SSN");
        Map<String, String> formData = new HashMap<>();
        formData.put("ssn", "123-45-678");
        formData.put("lastName", "test");
        formData.put("phoneNumber", "768-676-****");
        formData.put("dateOfBirthMasked", "04/22/1990");
        formData.put("addressLine1", "test");
        formData.put("cityName", "test");
        formData.put("addressLine2", "test");
        formData.put("state", "Alaska");
        formData.put("zipCode", "67567");

        equfixPlaceOnAlert.performAlertPlacementFlow(formData);

        Allure.step("Verify error message for invalid SSN");
        // Add assertion logic here based on expected results
    }

    @Test(description = "TC08 - Place Alert - Missing State")
    @Severity(SeverityLevel.MINOR)
    @Story("Place Alert with missing state")
    public void testPlaceAlertMissingState() {
        Allure.step("Navigate to Equifax homepage");
        page.navigate("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/");

        Allure.step("Click on 'Place an Alert' button");
        equfixHomepage.clickPlaceAnAlert();

        Allure.step("Switch to new window for alert placement");
        Page alertPage = context.waitForEvent("page", () -> {
            equfixHomepage.switchToNewWindow();
        });

        Allure.step("Fill in alert placement form with missing state");
        Map<String, String> formData = new HashMap<>();
        formData.put("ssn", "***-**-7575");
        formData.put("lastName", "test");
        formData.put("phoneNumber", "768-676-****");
        formData.put("dateOfBirthMasked", "04/22/1990");
        formData.put("addressLine1", "test");
        formData.put("cityName", "test");
        formData.put("addressLine2", "test");
        formData.put("state", ""); // Missing state
        formData.put("zipCode", "67567");

        equfixPlaceOnAlert.performAlertPlacementFlow(formData);

        Allure.step("Verify error message for missing state");
        // Add assertion logic here based on expected results
    }
}
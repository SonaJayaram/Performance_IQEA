import com.microsoft.playwright.*;
import org.testng.annotations.*;
import io.qameta.allure.Allure;
import io.qameta.allure.Step;
import org.testng.Assert;

import java.io.ByteArrayInputStream;

import output.page_file_generator.Equfix_home_page_playwright;
import output.page_file_generator.Equfix_Place_On_Alert_playwright;

public class PlaceAlertTests {

    private Playwright playwright;
    private Browser browser;
    private BrowserContext context;
    private Page page;
    private Equfix_home_page_playwright homePage;
    private Equfix_Place_On_Alert_playwright placeOnAlertPage;

    @BeforeClass
    public void setUp() {
        playwright = Playwright.create();
        browser = playwright.webkit().launch(new BrowserType.LaunchOptions().setHeadless(false));
        context = browser.newContext();
        page = context.newPage();
        homePage = new Equfix_home_page_playwright(page);
        placeOnAlertPage = new Equfix_Place_On_Alert_playwright(page);
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

    @Test
    public void test_TC03_PlaceAlert_MissingLastName() {
        Allure.step("Starting test: TC03 - Place Alert - Missing Last Name");
        page.navigate("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/");
        Allure.addAttachment("screenshot", new ByteArrayInputStream(page.screenshot()));

        homePage.placeAnAlertAction();
        Allure.addAttachment("screenshot", new ByteArrayInputStream(page.screenshot()));

        placeOnAlertPage.enterSsn("***-**-7575");
        placeOnAlertPage.enterPhoneNumber("768-676-****");
        placeOnAlertPage.enterDob("04/22/1990");
        placeOnAlertPage.enterAddress("test");
        placeOnAlertPage.enterCity("test");
        placeOnAlertPage.enterAddressLine2("test");
        placeOnAlertPage.selectState("Alaska");
        placeOnAlertPage.enterZip("67567");
        placeOnAlertPage.clickContinueButton();

        page.waitForSelector("xpath=//div[contains(@class, 'error') and contains(text(), 'Last Name is required')]");
        String errorMessage = page.locator("xpath=//div[contains(@class, 'error') and contains(text(), 'Last Name is required')]").textContent();
        Allure.addAttachment("screenshot", new ByteArrayInputStream(page.screenshot()));
        Assert.assertEquals(errorMessage.trim(), "Last Name is required", "Error message for missing last name is incorrect.");
    }

    @Test
    public void test_TC04_PlaceAlert_InvalidPhoneNumber() {
        Allure.step("Starting test: TC04 - Place Alert - Invalid Phone Number");
        page.navigate("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/");
        Allure.addAttachment("screenshot", new ByteArrayInputStream(page.screenshot()));

        homePage.placeAnAlertAction();
        Allure.addAttachment("screenshot", new ByteArrayInputStream(page.screenshot()));

        placeOnAlertPage.enterSsn("***-**-7575");
        placeOnAlertPage.enterLastName("test");
        placeOnAlertPage.enterPhoneNumber("123");
        placeOnAlertPage.enterDob("04/22/1990");
        placeOnAlertPage.enterAddress("test");
        placeOnAlertPage.enterCity("test");
        placeOnAlertPage.enterAddressLine2("test");
        placeOnAlertPage.selectState("Alaska");
        placeOnAlertPage.enterZip("67567");
        placeOnAlertPage.clickContinueButton();

        page.waitForSelector("xpath=//div[contains(@class, 'error') and contains(text(), 'Invalid phone number')]");
        String errorMessage = page.locator("xpath=//div[contains(@class, 'error') and contains(text(), 'Invalid phone number')]").textContent();
        Allure.addAttachment("screenshot", new ByteArrayInputStream(page.screenshot()));
        Assert.assertEquals(errorMessage.trim(), "Invalid phone number", "Error message for invalid phone number is incorrect.");
    }

    @Test
    public void test_TC02_PlaceAlert_InvalidSSN() {
        Allure.step("Starting test: TC02 - Place Alert - Invalid SSN");
        page.navigate("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/");
        Allure.addAttachment("screenshot", new ByteArrayInputStream(page.screenshot()));

        homePage.placeAnAlertAction();
        Allure.addAttachment("screenshot", new ByteArrayInputStream(page.screenshot()));

        placeOnAlertPage.enterSsn("123-45-678");
        placeOnAlertPage.enterLastName("test");
        placeOnAlertPage.enterPhoneNumber("768-676-****");
        placeOnAlertPage.enterDob("04/22/1990");
        placeOnAlertPage.enterAddress("test");
        placeOnAlertPage.enterCity("test");
        placeOnAlertPage.enterAddressLine2("test");
        placeOnAlertPage.selectState("Alaska");
        placeOnAlertPage.enterZip("67567");
        placeOnAlertPage.clickContinueButton();

        page.waitForSelector("xpath=//div[contains(@class, 'error') and contains(text(), 'Invalid SSN')]");
        String errorMessage = page.locator("xpath=//div[contains(@class, 'error') and contains(text(), 'Invalid SSN')]").textContent();
        Allure.addAttachment("screenshot", new ByteArrayInputStream(page.screenshot()));
        Assert.assertEquals(errorMessage.trim(), "Invalid SSN", "Error message for invalid SSN is incorrect.");
    }

    @Step("Switch to new window")
    public Page switchToNewWindow(Page page) {
        return page.context().pages().get(page.context().pages().size() - 1);
    }
}
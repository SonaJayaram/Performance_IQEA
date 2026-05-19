import com.microsoft.playwright.*;
import io.qameta.allure.*;
import java.util.*;

public class TC01_PlaceAnAlert_SuccessfulFormSubmission {
    private Page page;
    private Equfix_home_page_playwright homePage;
    private Equfix_Place_On_Alert_playwright alertPage;

    public TC01_PlaceAnAlert_SuccessfulFormSubmission(Page page) {
        this.page = page;
        this.homePage = new Equfix_home_page_playwright(page);
        this.alertPage = new Equfix_Place_On_Alert_playwright(page);
    }

    @AllureId("TC01")
    @AllureFeature("Place an Alert")
    @AllureStory("Successful Form Submission")
    public void testPlaceAnAlertSuccessfulFormSubmission() {
        page.navigate("https://www.equifax.com/personal/credit-report-services/credit-fraud-alerts/");
        page.waitForLoadState("networkidle");

        homePage.clickPlaceAnAlert();
        page.waitForLoadState("networkidle");

        alertPage.fillFirstName("test");
        alertPage.fillLastName("test");
        alertPage.fillSSN("***-**-6686");
        alertPage.fillPhoneNumber("786-876-****");
        alertPage.fillDOB("04/22/1990");
        alertPage.fillAddress("test");
        alertPage.fillCity("test");
        alertPage.fillAddressLine2("test");
        alertPage.selectState("Alaska");
        alertPage.fillZip("78686");

        alertPage.clickContinueButton();
        page.waitForLoadState("networkidle");
    }
}
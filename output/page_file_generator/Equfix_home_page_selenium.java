import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.How;
import org.openqa.selenium.support.PageFactory;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.openqa.selenium.support.ui.ExpectedConditions;
import java.time.Duration;
import java.util.List;
import java.util.ArrayList;

public class Equfix_home_page {

    private WebDriver driver;
    private WebDriverWait wait;

    @FindBy(how = How.XPATH, using = "//a[contains(@class, 'btn') and text()='PLACE AN ALERT']")
    private WebElement placeAlertButton;

    @FindBy(how = How.XPATH, using = "//button[@name='close']")
    private WebElement closeButton;

    public Equfix_home_page(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(20));
        PageFactory.initElements(driver, this);
    }

    private void waitForElement(WebElement element) {
        wait.until(ExpectedConditions.visibilityOf(element));
    }

    private void waitForElementToBeClickable(WebElement element) {
        wait.until(ExpectedConditions.elementToBeClickable(element));
    }

    public void switchToNewWindow() {
        List<String> handles = new ArrayList<>(driver.getWindowHandles());
        if (handles.size() > 1) {
            driver.switchTo().window(handles.get(handles.size() - 1));
        }
    }

    public void clickPlaceAlertButton() {
        waitForElementToBeClickable(placeAlertButton);
        placeAlertButton.click();
    }

    public void clickCloseButton() {
        waitForElementToBeClickable(closeButton);
        closeButton.click();
    }
}
public class Equfix_home_page {
    private final Page page;
    private final Locator placeAnAlertButton;
    private final Locator closeButton;

    public Equfix_home_page(Page page) {
        this.page = page;
        // init locators
        this.placeAnAlertButton = page.locator("xpath=//a[contains(@class, 'btn') and text()='PLACE AN ALERT']");
        this.closeButton = page.locator("xpath=//button[@name='close']");
    }

    public Page switchToNewWindow(Page page) {
        return page.context().pages().get(page.context().pages().size() - 1);
    }

    public void waitForElement(Locator locator) {
        if (!locator.isVisible()) {
            throw new RuntimeException("Element not visible: " + locator);
        }
    }

    public void click(Locator locator) {
        waitForElement(locator);
        locator.click();
    }

    public void enterText(Locator locator, String text) {
        waitForElement(locator);
        locator.fill(text);
    }

    public void switchToFraudAlertPage() {
        Page newWindow = switchToNewWindow(this.page);
        this.page = newWindow;
    }

    public void placeAnAlertAction() {
        switchToFraudAlertPage();
        click(this.placeAnAlertButton);
        enterText(this.placeAnAlertButton, "PLACE AN ALERT");
    }

    public void closeAction() {
        click(this.closeButton);
    }
}
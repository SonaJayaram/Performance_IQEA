import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.testng.annotations.*;
import org.testng.Assert;
import io.qameta.allure.Allure;
import io.qameta.allure.Step;
import io.github.bonigarcia.wdm.WebDriverManager;
import java.io.ByteArrayInputStream;
import java.time.Duration;
import java.util.List;
import java.util.ArrayList;

public class TC01_Successful_purchase_standard_user {
    private WebDriver driver;
    private WebDriverWait wait;
    private final String baseUrl = "https://www.saucedemo.com/";

    @BeforeClass
    public void setUp() {
        WebDriverManager.chromedriver().setup();
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--start-maximized");
        // optionally run headless in CI by uncommenting:
        // options.addArguments("--headless=new");
        driver = new ChromeDriver(options);
        wait = new WebDriverWait(driver, Duration.ofSeconds(15));
        Allure.step("Browser started and WebDriver initialized");
    }

    @AfterClass
    public void tearDown() {
        try {
            Allure.step("Closing browser");
        } catch (Exception ignored) {
        }
        if (driver != null) {
            driver.quit();
        }
    }

    @Test(description = "TC01 - Successful purchase (standard_user)")
    public void TC01_Successful_purchase_standard_user() {
        try {
            // 1) Open base URL
            Allure.step("Navigate to base URL: " + baseUrl);
            driver.get(baseUrl);
            attachScreenshot("after_navigate_base");

            // If a new window was expected in recording, attempt to switch to it
            switchToNewWindowIfAny();

            // 2) Login - enter username
            helper_sendKeys_withHealing("user-name", "standard_user", "Enter username (user-name)");
            // 3) Login - enter password
            helper_sendKeys_withHealing("password", "secret_sauce", "Enter password (password)");
            // 4) Click login
            helper_click_withHealing("login-button", "Click login button (login-button)");

            // 5) Add to cart - backpack
            helper_click_withHealing("add-to-cart-sauce-labs-backpack", "Add Sauce Labs Backpack to cart");

            // 6) Click cart
            helper_click_possibleLocators(new String[]{"shopping_cart_container", "cart", "shopping_cart_link"}, "Open cart");

            // 7) Click checkout
            helper_click_withHealing("checkout", "Click checkout");

            // 8) Fill first name, last name, postal code
            helper_sendKeys_withHealing("firstName", "test", "Enter first name");
            helper_sendKeys_withHealing("lastName", "test", "Enter last name");
            helper_sendKeys_withHealing("postalCode", "3242354", "Enter postal code");

            // 9) Continue
            helper_click_withHealing("continue", "Click continue");

            // 10) Finish
            helper_click_withHealing("finish", "Click finish to complete purchase");

            // Primary assertion: verify checkout complete page reached
            Allure.step("Primary assertion: verify checkout-complete page is reached");
            attachScreenshot("before_primary_assertion");
            try {
                wait.until(driver -> driver.getCurrentUrl() != null && driver.getCurrentUrl().contains("checkout-complete.html"));
                String currentUrl = driver.getCurrentUrl();
                Assert.assertTrue(currentUrl != null && currentUrl.contains("checkout-complete.html"),
                        "Expected to be on checkout-complete page but current URL was: " + currentUrl);
            } catch (Exception ae) {
                attachPageSource("assertion_failure_page_source");
                attachScreenshot("assertion_failure_screenshot");
                throw ae;
            }

            // 11) After finish click back-to-products
            helper_click_withHealing("back-to-products", "Click back to products");

            // 12) Open menu and logout
            helper_click_withHealing("react-burger-menu-btn", "Open side menu");
            // Click All Items if present (inventory_sidebar_link), then logout
            helper_click_possibleLocators(new String[]{"inventory_sidebar_link"}, "Click All Items (inventory_sidebar_link)");
            helper_click_withHealing("logout_sidebar_link", "Click logout");

            Allure.step("Test flow completed");
        } catch (Exception e) {
            attachPageSource("error_page_source");
            attachScreenshot("error_screenshot");
            Allure.step("Exception during test execution: " + e.getMessage());
            Assert.fail("Test encountered exception: " + e.getMessage());
        }
    }

    // Helper to click by id with healing algorithm and JS fallback
    @Step("{description}")
    private void helper_click_withHealing(String id, String description) {
        Allure.step("Attempting click for: " + id + " - " + description);
        Exception lastEx = null;

        // Try multiple strategies in order
        By[] primaryLocators = new By[]{
                By.id(id),
                By.name(id),
                By.xpath("//*[text()='" + id + "']"),
                By.xpath("//*[contains(@id, '" + id + "')]"),
                By.xpath("//button[contains(., '" + id + "')] | //a[contains(., '" + id + "')]")
        };

        for (By locator : primaryLocators) {
            try {
                wait.until(ExpectedConditions.presenceOfElementLocated(locator));
                wait.until(ExpectedConditions.visibilityOfElementLocated(locator));
                try {
                    wait.until(ExpectedConditions.elementToBeClickable(locator));
                } catch (Exception ignore) {
                    // element might be visible but not clickable; we'll attempt click regardless
                }
                WebElement el = driver.findElement(locator);
                try {
                    el.click();
                    attachScreenshot("click_success_" + locator.toString());
                    return;
                } catch (Exception clickEx) {
                    lastEx = clickEx;
                    Allure.step("Native click failed for locator " + locator + ": " + clickEx.getMessage());
                    // Try JS click as fallback
                    try {
                        ((JavascriptExecutor) driver).executeScript("arguments[0].click();", el);
                        attachScreenshot("jsclick_success_" + locator.toString());
                        Allure.step("JS click succeeded for locator " + locator);
                        return;
                    } catch (Exception jsEx) {
                        lastEx = jsEx;
                        Allure.step("JS click also failed for locator " + locator + ": " + jsEx.getMessage());
                    }
                }
            } catch (Exception e) {
                lastEx = e;
                Allure.step("Locator attempt failed: " + locator + " -> " + e.getMessage());
                attachScreenshot("locator_attempt_failed_" + locator.toString());
                sleep(300);
            }
        }

        // Final attempt: try clickable by CSS class matching common patterns
        try {
            By fallback = By.cssSelector("button, a, div");
            List<WebElement> els = driver.findElements(fallback);
            for (WebElement el : els) {
                try {
                    String txt = "";
                    try { txt = el.getText(); } catch (Exception ignored) {}
                    String attrId = "";
                    try { attrId = el.getAttribute("id"); } catch (Exception ignored) {}
                    if ((txt != null && txt.contains(id)) || (attrId != null && attrId.contains(id))) {
                        try {
                            el.click();
                            attachScreenshot("click_success_fallback_textmatch");
                            Allure.step("Clicked fallback element matching text/id: " + id);
                            return;
                        } catch (Exception e) {
                            try {
                                ((JavascriptExecutor) driver).executeScript("arguments[0].click();", el);
                                attachScreenshot("jsclick_success_fallback_textmatch");
                                Allure.step("JS clicked fallback element matching text/id: " + id);
                                return;
                            } catch (Exception inner) {
                                lastEx = inner;
                            }
                        }
                    }
                } catch (StaleElementReferenceException sere) {
                    // ignore stale and continue
                }
            }
        } catch (Exception e) {
            lastEx = e;
        }

        Allure.step("All healing attempts failed for '" + id + "'. Throwing exception.");
        if (lastEx != null) {
            throw new RuntimeException("Click action failed for '" + id + "': " + lastEx.getMessage(), lastEx);
        } else {
            throw new RuntimeException("Click action failed for '" + id + "': unknown reason");
        }
    }

    // Helper to send keys by id with healing and JS fallback
    @Step("{description}")
    private void helper_sendKeys_withHealing(String id, String keys, String description) {
        Allure.step("Attempting sendKeys for: " + id + " - " + description);
        Exception lastEx = null;

        By[] locators = new By[]{
                By.id(id),
                By.name(id),
                By.xpath("//input[@placeholder='" + id + "']"),
                By.xpath("//input[contains(@id, '" + id + "')]"),
                By.xpath("//input")
        };

        for (By locator : locators) {
            try {
                wait.until(ExpectedConditions.presenceOfElementLocated(locator));
                wait.until(ExpectedConditions.visibilityOfElementLocated(locator));
                WebElement el = driver.findElement(locator);
                try {
                    el.clear();
                } catch (Exception ignore) {
                }
                try {
                    el.sendKeys(keys);
                    attachScreenshot("sendkeys_success_" + locator.toString());
                    return;
                } catch (Exception sendEx) {
                    lastEx = sendEx;
                    Allure.step("Native sendKeys failed for locator " + locator + ": " + sendEx.getMessage());
                    // Try JS set value
                    try {
                        ((JavascriptExecutor) driver).executeScript("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input'));", el, keys);
                        attachScreenshot("js_sendkeys_success_" + locator.toString());
                        Allure.step("JS set value succeeded for locator " + locator);
                        return;
                    } catch (Exception jsEx) {
                        lastEx = jsEx;
                        Allure.step("JS set value failed for locator " + locator + ": " + jsEx.getMessage());
                    }
                }
            } catch (Exception e) {
                lastEx = e;
                Allure.step("Locator attempt failed for sendKeys: " + locator + " -> " + e.getMessage());
                attachScreenshot("sendkeys_locator_attempt_failed_" + locator.toString());
                sleep(300);
            }
        }

        Allure.step("All healing attempts failed for sendKeys for '" + id + "'. Throwing exception.");
        if (lastEx != null) {
            throw new RuntimeException("sendKeys action failed for '" + id + "': " + lastEx.getMessage(), lastEx);
        } else {
            throw new RuntimeException("sendKeys action failed for '" + id + "': unknown reason");
        }
    }

    // Helper to click using multiple possible ids (useful when element id varies)
    @Step("{description}")
    private void helper_click_possibleLocators(String[] ids, String description) {
        for (String id : ids) {
            try {
                helper_click_withHealing(id, description + " (attempting id: " + id + ")");
                return;
            } catch (Exception e) {
                Allure.step("Attempt for locator '" + id + "' failed: " + e.getMessage());
                // continue to next
            }
        }
        // As final fallback, try a generic cart icon or button
        try {
            By cartBy = By.xpath("//a[contains(@class,'shopping_cart_link')] | //div[@id='shopping_cart_container'] | //a[@id='shopping_cart_container']");
            wait.until(ExpectedConditions.presenceOfElementLocated(cartBy));
            WebElement cartBtn = driver.findElement(cartBy);
            try {
                cartBtn.click();
            } catch (Exception e) {
                ((JavascriptExecutor) driver).executeScript("arguments[0].click();", cartBtn);
            }
            attachScreenshot("click_success_generic_cart");
            Allure.step("Healed by clicking generic cart selector");
            return;
        } catch (Exception e) {
            attachScreenshot("click_generic_cart_failed");
            throw new RuntimeException("All attempts failed for clicking one of possible locators", e);
        }
    }

    @Step("Switch to new window if any")
    private void switchToNewWindowIfAny() {
        Allure.step("Checking for a new window to switch to");
        try {
            String original = driver.getWindowHandle();
            List<String> handles = new ArrayList<>(driver.getWindowHandles());
            if (handles.size() > 1) {
                for (String h : handles) {
                    if (!h.equals(original)) {
                        driver.switchTo().window(h);
                        Allure.step("Switched to new window: " + driver.getCurrentUrl());
                        attachScreenshot("switched_to_new_window");
                        return;
                    }
                }
            } else {
                // Poll for a short time
                long start = System.currentTimeMillis();
                while ((System.currentTimeMillis() - start) < 5000) {
                    handles = new ArrayList<>(driver.getWindowHandles());
                    if (handles.size() > 1) {
                        for (String h : handles) {
                            if (!h.equals(original)) {
                                driver.switchTo().window(h);
                                Allure.step("Switched to new window after wait: " + driver.getCurrentUrl());
                                attachScreenshot("switched_to_new_window");
                                return;
                            }
                        }
                    }
                    sleep(200);
                }
                Allure.step("No additional window found to switch to");
            }
        } catch (Exception e) {
            Allure.step("Exception while switching to new window: " + e.getMessage());
            attachScreenshot("switch_window_exception");
        }
    }

    @Step("Attach screenshot: {name}")
    private void attachScreenshot(String name) {
        try {
            Allure.addAttachment(name, new ByteArrayInputStream(((TakesScreenshot) driver).getScreenshotAs(OutputType.BYTES)));
        } catch (Exception e) {
            // best-effort only
        }
    }

    @Step("Attach page source: {name}")
    private void attachPageSource(String name) {
        try {
            String src = driver.getPageSource();
            Allure.addAttachment(name + ".html", new ByteArrayInputStream(src.getBytes()));
        } catch (Exception e) {
            // best effort
        }
    }

    private void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException ignored) {
        }
    }
}
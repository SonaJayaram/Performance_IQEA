const { webkit } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await webkit.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  const domDetails = [];

  // Utility function to handle cookies and overlays
  const handleCookiesAndOverlays = async () => {
    try {
      // Accept cookies if prompted
      if (await page.locator('text="Accept"').first().isVisible()) {
        await page.locator('text="Accept"').first().click();
        await page.waitForLoadState('networkidle');
      }

      // Dismiss overlays/pop-ups if present
      const overlays = ['.overlay', '.popup', '.modal', '.advertisement'];
      for (const overlay of overlays) {
        if (await page.locator(overlay).isVisible()) {
          await page.locator(overlay).locator('button, .close, .dismiss').first().click();
          await page.waitForLoadState('networkidle');
        }
      }
    } catch (err) {
      // Ignore errors from optional UI elements
    }
  };

  // Navigate to Sauce Demo login page
  await page.goto('https://www.saucedemo.com');
  await page.waitForLoadState('networkidle');

  await handleCookiesAndOverlays();
  domDetails.push({ page_name: "Sauce Demo Login Page", html: await page.content() });

  // Scenario: Successful login with valid credentials
  await page.fill('input[data-test="username"]', 'standard_user');
  await page.fill('input[data-test="password"]', 'secret_sauce');
  await page.click('input[data-test="login-button"]');
  await page.waitForLoadState('networkidle');
  domDetails.push({ page_name: "Inventory Page", html: await page.content() });

  // Scenario: Add a product to the shopping cart
  await page.click('.inventory_item:first-child button[data-test="add-to-cart-sauce-labs-backpack"]');
  await page.waitForSelector('.shopping_cart_badge:text("1")');
  domDetails.push({ page_name: "Shopping Cart After Adding Item", html: await page.content() });

  // Scenario: Checkout process with valid details
  await page.click('.shopping_cart_link');
  await page.waitForLoadState('networkidle');
  domDetails.push({ page_name: "Shopping Cart Page", html: await page.content() });

  await page.click('button[data-test="checkout"]');
  await page.waitForLoadState('networkidle');
  domDetails.push({ page_name: "Checkout Your Information Page", html: await page.content() });

  await page.fill('input[data-test="firstName"]', 'John');
  await page.fill('input[data-test="lastName"]', 'Doe');
  await page.fill('input[data-test="postalCode"]', '12345');
  await page.click('input[data-test="continue"]');
  await page.waitForLoadState('networkidle');
  domDetails.push({ page_name: "Checkout Overview Page", html: await page.content() });

  await page.click('button[data-test="finish"]');
  await page.waitForSelector('.complete-header');
  domDetails.push({ page_name: "Order Confirmation Page", html: await page.content() });

  // Scenario: Logout from the application
  await page.click('#react-burger-menu-btn');
  await page.waitForSelector('.bm-item-list a#logout_sidebar_link');
  await page.click('.bm-item-list a#logout_sidebar_link');
  await page.waitForLoadState('networkidle');
  domDetails.push({ page_name: "Login Page After Logout", html: await page.content() });

  // Save DOM details to JSON file
  const domFilePath = 'output/Dom_details/all_page_dom_details.json';
  fs.mkdirSync('output/Dom_details', { recursive: true });
  fs.writeFileSync(domFilePath, JSON.stringify(domDetails, null, 2));

  console.log('Execution completed. DOM file saved to: output/Dom_details/all_page_dom_details.json');

  // Close the browser
  await browser.close();
})();
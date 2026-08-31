const { webkit } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await webkit.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  const domDetails = [];

  // Helper functions
  async function captureDOM(pageName) {
    try {
      const content = await page.content();
      domDetails.push({ page_name: pageName, html: content });
    } catch (err) {
      console.error(`Failed to capture DOM for ${pageName}:`, err);
    }
  }

  async function waitForAndClick(selector, description) {
    try {
      await page.waitForSelector(selector, { timeout: 5000 });
      await page.click(selector);
    } catch (err) {
      console.warn(`Could not click on ${description}:`, err);
    }
  }

  async function navigate(url) {
    try {
      await page.goto(url);
      await page.waitForLoadState('networkidle'); // For navigation events
    } catch (err) {
      console.warn(`Navigation failed to ${url}:`, err);
    }
  }

  async function acceptCookiesIfPrompted() {
    try {
      await waitForAndClick('#accept-cookies', 'Accept Cookies button');
    } catch (err) {
      console.warn('No Accept Cookies prompt detected:', err);
    }
  }

  async function dismissPopupsIfAny() {
    try {
      await waitForAndClick('.popup-close', 'Popup close button');
    } catch (err) {
      console.warn('No popups detected:', err);
    }
  }

  try {
    // Background: Navigate to Sauce Demo login page and capture its initial DOM
    await navigate('https://www.saucedemo.com/');
    await page.waitForSelector('#login-button'); // Ensure page is stable
    await captureDOM('Login Page');

    // Accept cookies if prompted and dismiss popups
    // await acceptCookiesIfPrompted();
    // await dismissPopupsIfAny();

    // Fill in credentials and log in
    await page.fill('#user-name', 'standard_user');
    await page.fill('#password', 'secret_sauce');
    await waitForAndClick('#login-button', 'Login button');
    await page.waitForSelector('.title'); // Ensures inventory is loaded

    // Capture DOM after login
    await captureDOM('Inventory Page');

    // Scenario: Add items to cart
    await waitForAndClick('#add-to-cart-sauce-labs-backpack', 'Add to cart: Sauce Labs Backpack');
    await waitForAndClick('#add-to-cart-sauce-labs-bolt-t-shirt', 'Add to cart: Bolt T-Shirt');
    await waitForAndClick('#add-to-cart-sauce-labs-bike-light', 'Add to cart: Bike Light');
    await waitForAndClick('#add-to-cart-sauce-labs-fleece-jacket', 'Add to cart: Fleece Jacket');

    // Capture DOM after items added to cart
    await captureDOM('Cart Updated Page');

    // Scenario: Navigate to cart and remove items
    await waitForAndClick('.shopping_cart_link', 'Cart button');
    await captureDOM('Cart Page');

    await waitForAndClick('#remove-sauce-labs-backpack', 'Remove: Sauce Labs Backpack');

    // Capture DOM after an item is removed from the cart
    await captureDOM('Item Removed from Cart Page');
  } catch (err) {
    console.error('An unexpected error occurred:', err);
  } finally {
    // Save DOM details to JSON file
    const domDetailsFile = path.join(__dirname, 'output/Dom_details/all_page_dom_details.json');
    const scriptFilePath = path.join(__dirname, 'output/Dom_script/dom_collector.js');

    try {
      fs.mkdirSync(path.dirname(domDetailsFile), { recursive: true });
      fs.writeFileSync(domDetailsFile, JSON.stringify(domDetails, null, 2), 'utf-8');
    } catch (err) {
      console.error('Failed to save DOM details file:', err);
    }

    try {
      fs.mkdirSync(path.dirname(scriptFilePath), { recursive: true });
      fs.copyFileSync(__filename, scriptFilePath);
    } catch (err) {
      console.error('Failed to save script file:', err);
    }

    console.log('Execution completed. DOM file saved to: output/Dom_details/all_page_dom_details.json');
    await browser.close();
  }
})();
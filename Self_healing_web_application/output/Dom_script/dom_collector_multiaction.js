const fs = require('fs');
const playwright = require('playwright');

(async () => {
  const browser = await playwright.webkit.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  const domData = [];

  async function captureDom(pageName) {
    try {
      await page.waitForLoadState('networkidle');
      const html = await page.content();
      domData.push({ page_name: pageName, html });
    } catch (error) {
      console.warn(`Failed to capture DOM for ${pageName}:`, error.message);
    }
  }

  async function clickSafe(selector) {
    try {
      await page.waitForSelector(selector, { timeout: 5000 });
      await page.click(selector);
    } catch (error) {
      console.warn(`Failed to click on ${selector}:`, error.message);
    }
  }

  async function typeSafe(selector, text) {
    try {
      await page.waitForSelector(selector, { timeout: 5000 });
      await page.fill(selector, text);
    } catch (error) {
      console.warn(`Failed to type in ${selector}:`, error.message);
    }
  }

  async function selectSafe(selector, optionTextOrValue) {
    try {
      await page.waitForSelector(selector, { timeout: 5000 });
      const options = await page.$eval(selector, select => Array.from(select.options).map(option => option.value));
      const valueToSelect = optionTextOrValue || options.find(option => option !== '');
      if (valueToSelect) {
        await page.selectOption(selector, valueToSelect);
      } else {
        console.warn(`No valid option found for ${selector}`);
      }
    } catch (error) {
      console.warn(`Failed to select option in ${selector}:`, error.message);
    }
  }

  try {
    // Scenario: Login
    await page.goto('https://www.saucedemo.com/');
    await captureDom('Login Page');
    await typeSafe('#user-name', 'standard_user');
    await typeSafe('#password', 'secret_sauce');
    await clickSafe('#login-button');
    await captureDom('Inventory Page');

    // Scenario: Add multiple items to the cart
    await clickSafe('#add-to-cart-sauce-labs-backpack');
    await clickSafe('#add-to-cart-sauce-labs-bolt-t-shirt');
    await clickSafe('#add-to-cart-sauce-labs-bike-light');
    await clickSafe('#add-to-cart-sauce-labs-fleece-jacket');
    await captureDom('Cart with Items Added');

    // Scenario: Remove items from the cart
    await page.goto('https://www.saucedemo.com/cart.html');
    await clickSafe('.cart_quantity:nth-child(4)');
    await clickSafe('#remove-sauce-labs-backpack');
    await clickSafe('#remove-sauce-labs-bolt-t-shirt');
    await captureDom('Cart with Items Removed');

    // Scenario: Enter checkout information
    await clickSafe('#checkout');
    await typeSafe('#first-name', 'test');
    await typeSafe('#last-name', 'test');
    await typeSafe('#postal-code', '123456');
    await clickSafe('#continue');
    await captureDom('Checkout Step Two');

    // Scenario: Complete the checkout process
    await clickSafe('#finish');
    await captureDom('Checkout Complete');

    // Scenario: Return to product inventory
    await clickSafe('#back-to-products');
    await clickSafe('#react-burger-menu-btn');
    await captureDom('Return to Inventory Page');

    // Scenario: Logout from the application
    await clickSafe('#logout_sidebar_link');
    await captureDom('Logged Out');
  } catch (error) {
    console.error('Error during execution:', error.message);
  } finally {
    // Save the DOM data
    const outputDirectoryDom = 'output/Dom_details';
    const outputDirectoryScript = 'output/Dom_script';
    const domFilePath = `${outputDirectoryDom}/all_page_dom_details.json`;
    const scriptFilePath = `${outputDirectoryScript}/dom_collector.js`;

    try {
      fs.mkdirSync(outputDirectoryDom, { recursive: true });
      fs.writeFileSync(domFilePath, JSON.stringify(domData, null, 2));
      fs.mkdirSync(outputDirectoryScript, { recursive: true });
      fs.copyFileSync(__filename, scriptFilePath);
      console.log(`Execution completed. DOM file saved to: ${domFilePath}`);
    } catch (fileError) {
      console.error('Error saving files:', fileError.message);
    }

    await browser.close();
  }
})();
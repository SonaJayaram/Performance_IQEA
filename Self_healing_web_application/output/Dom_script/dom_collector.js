const fs = require('fs');
const { webkit } = require('playwright');

(async () => {
  const browser = await webkit.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  let domData = [];

  const captureDom = async (pageName) => {
    try {
      await page.waitForLoadState('networkidle');
      const html = await page.content();
      domData.push({ page_name: pageName, html });
    } catch (e) {
      console.warn(`Failed to capture DOM for ${pageName}: ${e.message}`);
    }
  };

  const clickSafe = async (selector) => {
    try {
      await page.waitForSelector(selector, { timeout: 5000 });
      await page.click(selector);
    } catch (e) {
      console.warn(`Failed to click on ${selector}: ${e.message}`);
    }
  };

  const typeSafe = async (selector, text) => {
    try {
      await page.waitForSelector(selector, { timeout: 5000 });
      await page.fill(selector, text);
    } catch (e) {
      console.warn(`Failed to type in ${selector}: ${e.message}`);
    }
  };

  const selectSafe = async (selector, optionTextOrValue) => {
    try {
      await page.waitForSelector(selector, { timeout: 5000 });
      const options = await page.$$(selector + ' option');
      if (options.length > 1 && !optionTextOrValue) {
        await page.selectOption(selector, { index: 1 });
      } else {
        await page.selectOption(selector, optionTextOrValue);
      }
    } catch (e) {
      console.warn(`Failed to select option in ${selector}: ${e.message}`);
    }
  };

  try {
    // Step 1: Navigate to the URL and capture DOM of login page
    await page.goto('https://www.saucedemo.com/');
    await page.waitForSelector('#login-button'); // Ensure page is fully rendered
    await captureDom('login-page');

    // Step 2: Fill login form and click login
    await typeSafe('#user-name', 'standard_user');
    await typeSafe('#password', 'secret_sauce');
    await clickSafe('#login-button');

    // Step 3: Wait for inventory page and capture its DOM
    await page.waitForSelector('.inventory_list'); // Wait for specific element on inventory page
    await captureDom('inventory-page');

  } catch (e) {
    console.error(`Error occurred: ${e.message}`);
  } finally {
    // Save DOM data to JSON file
    try {
      const domFilePath = 'output/Dom_details/all_page_dom_details.json';
      const scriptFilePath = 'output/Dom_script/dom_collector.js';
      fs.mkdirSync('output/Dom_details', { recursive: true });
      fs.mkdirSync('output/Dom_script', { recursive: true });
      fs.writeFileSync(domFilePath, JSON.stringify(domData, null, 2));
      fs.copyFileSync(__filename, scriptFilePath);
      console.log('Execution completed. DOM file saved to: output/Dom_details/all_page_dom_details.json');
    } catch (e) {
      console.error(`Failed to save DOM data or script: ${e.message}`);
    }

    await browser.close();
  }
})();
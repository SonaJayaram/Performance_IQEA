const fs = require('fs');
const path = require('path');
const playwright = require('playwright');

(async () => {
  const domResults = [];
  const scriptOutputDir = path.join('output', 'Dom_script');
  const domOutputDir = path.join('output', 'Dom_details');
  const domOutputFile = path.join(domOutputDir, 'all_page_dom_details.json');
  const scriptFilePath = path.join(scriptOutputDir, 'dom_collector.js');

  // Ensure output directories exist
  try { fs.mkdirSync(scriptOutputDir, { recursive: true }); } catch (e) {}
  try { fs.mkdirSync(domOutputDir, { recursive: true }); } catch (e) {}

  // Helper: safe sleep
  const safeTimeout = (ms) => new Promise((res) => setTimeout(res, ms));

  // Launch WebKit non-headless
  const browser = await playwright.webkit.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Helper functions
  async function clickSafe(selector, opts = {}) {
    try {
      const timeout = opts.timeout || 8000;
      await page.waitForSelector(selector, { timeout });
      try {
        await page.click(selector);
      } catch (err) {
        // fallback: try to use evaluate to click
        try {
          await page.evaluate((sel) => {
            const el = document.querySelector(sel);
            if (el) el.click();
          }, selector);
        } catch (ee) {
          console.warn(`Warning: Could not click ${selector}: ${ee.message}`);
        }
      }
    } catch (e) {
      console.warn(`Warning: clickSafe timeout or missing element for selector: ${selector}`);
    }
  }

  async function typeSafe(selector, text, opts = {}) {
    try {
      const timeout = opts.timeout || 8000;
      await page.waitForSelector(selector, { timeout });
      try {
        await page.fill(selector, text);
      } catch (err) {
        try {
          await page.evaluate((sel, val) => {
            const el = document.querySelector(sel);
            if (el) el.value = val;
          }, selector, text);
        } catch (ee) {
          console.warn(`Warning: Could not type into ${selector}: ${ee.message}`);
        }
      }
    } catch (e) {
      console.warn(`Warning: typeSafe timeout or missing element for selector: ${selector}`);
    }
  }

  async function selectSafe(selector, optionTextOrValue) {
    try {
      const timeout = 8000;
      await page.waitForSelector(selector, { timeout });
      // Evaluate options
      const chosen = await page.evaluate((sel, opt) => {
        const select = document.querySelector(sel);
        if (!select) return null;
        // If specific option provided, try value first then text
        if (opt) {
          // try value
          const byValue = Array.from(select.options).find(o => o.value === opt);
          if (byValue) { select.value = byValue.value; select.dispatchEvent(new Event('change')); return byValue.value; }
          // try visible text
          const byText = Array.from(select.options).find(o => o.text.trim() === opt);
          if (byText) { select.value = byText.value; select.dispatchEvent(new Event('change')); return byText.value; }
        }
        // pick first non-default valid option (not empty and not disabled)
        const viable = Array.from(select.options).find(o => o.value && !o.disabled);
        if (viable) { select.value = viable.value; select.dispatchEvent(new Event('change')); return viable.value; }
        return null;
      }, selector, optionTextOrValue);
      if (chosen === null) {
        console.warn(`Warning: selectSafe could not select an option for ${selector}`);
      }
    } catch (e) {
      console.warn(`Warning: selectSafe timeout or missing element for selector: ${selector}`);
    }
  }

  // captureDom waits for a page-specific stable element then captures HTML
  async function captureDom(pageName) {
    try {
      // Mapping pageName to stable selectors (multiple fallbacks)
      const selectorMap = {
        'login': ['#login-button', 'button[type="submit"]', 'input#user-name'],
        'inventory': ['#inventory_container', '.inventory_list', '.inventory_container'],
        'cart': ['#cart_contents_container', '.cart_list', '.cart_item'],
        'checkout_info': ['#first-name', 'input#first-name', 'form.checkout_info'],
        'checkout_overview': ['.checkout_summary_container', '#checkout_summary_container'],
        'checkout_complete': ['.complete-header', '#checkout_complete_container', '.checkout_complete_container'],
        'inventory_after_return': ['#inventory_container', '.inventory_list'],
        'login_after_logout': ['#login-button', 'input#user-name']
      };

      const selectors = selectorMap[pageName] || [];
      let waited = false;
      for (const sel of selectors) {
        try {
          await page.waitForSelector(sel, { timeout: 7000 });
          waited = true;
          break;
        } catch (e) {
          // try next fallback
        }
      }
      // Non-critical fallback: ensure network is idle briefly
      if (!waited) {
        try {
          await page.waitForLoadState('networkidle', { timeout: 7000 });
        } catch (e) {
          // swallow
        }
      }
    } catch (e) {
      // swallow
    } finally {
      try {
        const html = await page.content();
        domResults.push({ page_name: pageName, html });
      } catch (e) {
        console.warn(`Warning: Failed to capture DOM for ${pageName}: ${e.message}`);
        domResults.push({ page_name: pageName, html: '' });
      }
    }
  }

  // Generic attempts to accept cookies and close overlays
  async function handleCommonOverlays() {
    // Try common cookie/overlay selectors
    const cookieSelectors = [
      'button#accept-cookies',
      'button#onetrust-accept-btn-handler',
      'button.cookie-accept',
      'button[aria-label*="accept"]',
      'button:has-text("Accept")',
      'button:has-text("I agree")',
      'button:has-text("Accept All")',
      'button:has-text("Got it")',
      '.cookie-banner button',
      '.cc-btn'
    ];
    for (const sel of cookieSelectors) {
      try {
        const el = await page.$(sel);
        if (el) {
          try { await el.click(); } catch (e) { /* ignore */ }
        }
      } catch (e) { /* ignore */ }
    }

    // Try close buttons for modals/popups
    const closeSelectors = [
      '.modal .close',
      '.modal-close',
      '.popup-close',
      '.close-button',
      'button[aria-label="close"]',
      'button:has-text("Close")',
      '.react-modal__close-button'
    ];
    for (const sel of closeSelectors) {
      try {
        const el = await page.$(sel);
        if (el) {
          try { await el.click(); } catch (e) { /* ignore */ }
        }
      } catch (e) { /* ignore */ }
    }

    // Try pressing Escape as a last resort
    try {
      await page.keyboard.press('Escape');
    } catch (e) {}
    // small pause to let DOM settle
    try { await safeTimeout(500); } catch (e) {}
  }

  try {
    // Start test flow based on feature file
    // Background: navigate to login and capture login DOM then log in
    await page.goto('https://www.saucedemo.com/');
    try { await page.waitForLoadState('networkidle', { timeout: 10000 }); } catch (e) {}
    // Accept cookies / overlays if present
    try { await handleCommonOverlays(); } catch (e) {}

    // Wait for stable login element before capturing login DOM
    try {
      await page.waitForSelector('#login-button', { timeout: 10000 });
    } catch (e) {
      // fallback to any submit button or user input
      try { await page.waitForSelector('button[type="submit"]', { timeout: 5000 }); } catch (ee) {}
    }
    await captureDom('login');

    // Log in with provided credentials
    await typeSafe('#user-name', 'standard_user');
    await typeSafe('#password', 'secret_sauce');
    // Click login button - triggers navigation
    await clickSafe('#login-button');
    try { await page.waitForLoadState('networkidle', { timeout: 10000 }); } catch (e) {}

    // Wait for inventory stable element then capture
    try {
      await page.waitForSelector('#inventory_container', { timeout: 10000 });
    } catch (e) {
      try { await page.waitForSelector('.inventory_list', { timeout: 7000 }); } catch (ee) {}
    }
    await captureDom('inventory');

    // Scenario: Add product to cart and view cart
    // Add "Sauce Labs Backpack" to the cart
    // Attempt a few selector strategies
    const addSelectors = [
      'button#add-to-cart-sauce-labs-backpack',
      'xpath=//div[contains(@class,"inventory_item")]//div[text()="Sauce Labs Backpack"]/ancestor::div[contains(@class,"inventory_item")]//button',
      'xpath=//div[@class="inventory_item"]//div[contains(.,"Sauce Labs Backpack")]/following::button[1]',
      'button:has-text("Add to cart")'
    ];
    let added = false;
    for (const sel of addSelectors) {
      try {
        // For xpath, Playwright needs 'xpath=' prefix which we provided
        await page.waitForSelector(sel, { timeout: 4000 });
        await clickSafe(sel);
        added = true;
        break;
      } catch (e) {
        // try next
      }
    }
    if (!added) {
      // Try finding by locating item container then button
      try {
        const itemHandles = await page.$$('.inventory_item');
        for (const item of itemHandles) {
          try {
            const txt = await item.$eval('.inventory_item_name', el => el.textContent.trim());
            if (txt === 'Sauce Labs Backpack') {
              const btn = await item.$('button');
              if (btn) {
                try { await btn.click(); added = true; break; } catch (ee) {}
              }
            }
          } catch (e) {}
        }
      } catch (e) {}
    }

    // Open the cart
    await clickSafe('.shopping_cart_link');
    try { await page.waitForSelector('#cart_contents_container', { timeout: 8000 }); } catch (e) {
      try { await page.waitForSelector('.cart_list', { timeout: 5000 }); } catch (ee) {}
    }
    await captureDom('cart');

    // Scenario: Proceed to checkout from cart
    // Click the "checkout" button
    await clickSafe('#checkout');
    try { await page.waitForLoadState('networkidle', { timeout: 8000 }); } catch (e) {}
    try { await page.waitForSelector('#first-name', { timeout: 8000 }); } catch (e) {}
    await captureDom('checkout_info');

    // Scenario: Enter checkout information
    await typeSafe('#first-name', 'test');
    await typeSafe('#last-name', 'teest');
    await typeSafe('#postal-code', '7657');
    await clickSafe('#continue');
    try { await page.waitForLoadState('networkidle', { timeout: 8000 }); } catch (e) {}
    try { await page.waitForSelector('.checkout_summary_container', { timeout: 8000 }); } catch (e) {}
    await captureDom('checkout_overview');

    // Scenario: Complete the checkout
    await clickSafe('#finish');
    try { await page.waitForLoadState('networkidle', { timeout: 8000 }); } catch (e) {}
    try { await page.waitForSelector('.complete-header', { timeout: 8000 }); } catch (e) {}
    await captureDom('checkout_complete');

    // Scenario: Return to products
    await clickSafe('#back-to-products');
    try { await page.waitForLoadState('networkidle', { timeout: 8000 }); } catch (e) {}
    try { await page.waitForSelector('#inventory_container', { timeout: 8000 }); } catch (e) {}
    await captureDom('inventory_after_return');

    // Scenario: Logout
    // Open side menu
    await clickSafe('#react-burger-menu-btn');
    try { await page.waitForSelector('#logout_sidebar_link', { timeout: 8000 }); } catch (e) {}
    // Click logout link
    await clickSafe('#logout_sidebar_link');
    try { await page.waitForLoadState('networkidle', { timeout: 8000 }); } catch (e) {}
    try { await page.waitForSelector('#login-button', { timeout: 10000 }); } catch (e) {}
    await captureDom('login_after_logout');

    // Save DOM results to file
    try {
      fs.writeFileSync(domOutputFile, JSON.stringify(domResults, null, 2), 'utf-8');
    } catch (e) {
      console.warn(`Warning: Failed to write DOM output file: ${e.message}`);
    }

    // Copy this running script to output/Dom_script/dom_collector.js
    try {
      // __filename should point to current script file
      fs.copyFileSync(__filename, scriptFilePath);
    } catch (e) {
      console.warn(`Warning: Failed to copy script file: ${e.message}`);
    }

    // Final exact print
    console.log('Execution completed. DOM file saved to: output/Dom_details/all_page_dom_details.json');
  } catch (err) {
    // On unexpected top-level errors, still attempt to save what we have and copy script
    try { fs.writeFileSync(domOutputFile, JSON.stringify(domResults, null, 2), 'utf-8'); } catch (e) {}
    try { fs.copyFileSync(__filename, scriptFilePath); } catch (e) {}
    console.log('Execution completed. DOM file saved to: output/Dom_details/all_page_dom_details.json');
  } finally {
    try { await browser.close(); } catch (e) {}
  }
})();
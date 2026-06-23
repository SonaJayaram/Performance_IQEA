const fs = require('fs');
const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    let domDetails = [];

    const captureDom = async (pageName) => {
        try {
            await page.waitForLoadState('networkidle', { timeout: 10000 });
            const content = await page.content();
            domDetails.push({ page_name: pageName, html: content });
        } catch (error) {
            console.warn(`Failed to capture DOM for ${pageName}:`, error);
        }
    };

    const clickSafe = async (selector) => {
        try {
            await page.waitForSelector(selector, { timeout: 5000 });
            await page.click(selector);
        } catch (error) {
            console.warn(`Failed to click on element ${selector}:`, error);
        }
    };

    const typeSafe = async (selector, text) => {
        try {
            await page.waitForSelector(selector, { timeout: 5000 });
            await page.fill(selector, text);
        } catch (error) {
            console.warn(`Failed to type into element ${selector}:`, error);
        }
    };

    const selectSafe = async (selector, optionTextOrValue = null) => {
        try {
            await page.waitForSelector(selector, { timeout: 5000 });
            if (optionTextOrValue) {
                await page.selectOption(selector, { label: optionTextOrValue });
            } else {
                const options = await page.$$(selector + ' option');
                if (options.length > 1) {
                    const firstOption = await options[1].getAttribute('value');
                    await page.selectOption(selector, firstOption);
                }
            }
        } catch (error) {
            console.warn(`Failed to select an option for ${selector}:`, error);
        }
    };

    try {
        // Step 1: Navigate to Login Page
        await page.goto('https://www.saucedemo.com/');
        try {
            const cookieBanner = await page.$('text=Accept Cookies');
            if (cookieBanner) {
                await clickSafe('text=Accept Cookies');
            }
        } catch (error) {
            console.warn('No cookie banner found:', error);
        }
        await page.waitForSelector('#login-button', { timeout: 10000 });
        await captureDom('login_page');

        // Step 2: Perform Login
        await typeSafe('#user-name', 'standard_user');
        await typeSafe('#password', 'secret_sauce');
        await clickSafe('#login-button');
        await page.waitForSelector('.inventory_list', { timeout: 10000 });
        await captureDom('inventory_page');

        // Step 3: Add a product to the cart
        await clickSafe('#add-to-cart-sauce-labs-backpack');
        await captureDom('product_added');

        // Step 4: View the cart
        await clickSafe('.shopping_cart_badge');
        await page.waitForSelector('.cart_list', { timeout: 10000 });
        await captureDom('cart_page');

        // Step 5: Proceed to checkout
        await clickSafe('#checkout');
        await page.waitForSelector('#first-name', { timeout: 10000 });
        await captureDom('checkout_info_page');

        // Step 6: Enter checkout information
        await typeSafe('#first-name', 'test');
        await typeSafe('#last-name', 'test');
        await typeSafe('#postal-code', '67857');
        await clickSafe('#continue');
        await page.waitForSelector('.summary_info', { timeout: 10000 });
        await captureDom('checkout_summary_page');

        // Step 7: Complete the checkout
        await clickSafe('#checkout_summary_container');
        await clickSafe('#finish');
        await page.waitForSelector('.checkout_complete_container', { timeout: 10000 });
        await captureDom('checkout_complete_page');

        // Step 8: Return to the product page
        await clickSafe('#back-to-products');
        await page.waitForSelector('.inventory_list', { timeout: 10000 });
        await captureDom('inventory_page_after_return');

        // Step 9: Logout
        await clickSafe('#react-burger-menu-btn');
        await clickSafe('#logout_sidebar_link');
        await page.waitForSelector('#login-button', { timeout: 10000 });
        await captureDom('logged_out_page');
    } catch (error) {
        console.error('An error occurred during execution:', error);
    } finally {
        // Save DOM details to a JSON file
        try {
            fs.mkdirSync('output/Dom_details', { recursive: true });
            const domFilePath = 'output/Dom_details/all_page_dom_details.json';
            fs.writeFileSync(domFilePath, JSON.stringify(domDetails, null, 2), 'utf-8');

            // Save the script itself
            try {
                fs.mkdirSync('output/Dom_script', { recursive: true });
                const scriptFilePath = 'output/Dom_script/dom_collector.js';
                fs.copyFileSync(__filename, scriptFilePath);
            } catch (copyError) {
                console.error('Failed to save this script file:', copyError);
            }

            console.log('Execution completed. DOM file saved to: output/Dom_details/all_page_dom_details.json');
        } catch (fileError) {
            console.error('Failed to save DOM details:', fileError);
        }

        // Close the browser
        await browser.close();
    }
})();
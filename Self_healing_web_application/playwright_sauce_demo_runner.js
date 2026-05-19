// Playwright automation for Sauce Demo scenarios
// This script executes each scenario from the feature file as a separate test case.
// Snapshots are taken on failure and a self-contained HTML report is generated.

const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://www.saucedemo.com/';

const REPORT_DIR = path.join(__dirname, 'reporting');
const SNAPSHOT_DIR = path.join(REPORT_DIR, 'snapshots');
const DOM_OUTPUT_DIR = path.join(__dirname, 'output', 'sauce_demo');
if (!fs.existsSync(path.join(__dirname, 'output'))) fs.mkdirSync(path.join(__dirname, 'output'));
if (!fs.existsSync(REPORT_DIR)) fs.mkdirSync(REPORT_DIR);
if (!fs.existsSync(SNAPSHOT_DIR)) fs.mkdirSync(SNAPSHOT_DIR);
if (!fs.existsSync(DOM_OUTPUT_DIR)) fs.mkdirSync(DOM_OUTPUT_DIR);

const scenarios = [
  {
    name: 'Successful login with valid credentials',
    steps: async (page, saveDomStep) => {
      await page.goto(BASE_URL);
      if (saveDomStep) await saveDomStep('login_page');
      await page.fill('#user-name', 'standard_user');
      await page.fill('#password', 'secret_sauce');
      await page.click('#login-button');
      await page.waitForSelector('.inventory_list');
      if (saveDomStep) await saveDomStep('inventory_page');
      const items = await page.$$('.inventory_item');
      if (items.length === 0) throw new Error('No inventory items displayed');
    }
  },
  {
    name: 'Add a product to the shopping cart',
    steps: async (page, saveDomStep) => {
      await page.goto(BASE_URL);
      if (saveDomStep) await saveDomStep('login_page');
      await page.fill('#user-name', 'standard_user');
      await page.fill('#password', 'secret_sauce');
      await page.click('#login-button');
      await page.waitForSelector('.inventory_list');
      if (saveDomStep) await saveDomStep('inventory_page');
      await page.click('.inventory_item button');
      if (saveDomStep) await saveDomStep('after_add_to_cart');
      await page.waitForSelector('.shopping_cart_badge');
      const badge = await page.textContent('.shopping_cart_badge');
      if (badge !== '1') throw new Error('Cart badge does not show 1');
    }
  },
  {
    name: 'Checkout process with valid details',
    steps: async (page, saveDomStep) => {
      await page.goto(BASE_URL);
      if (saveDomStep) await saveDomStep('login_page');
      await page.fill('#user-name', 'standard_user');
      await page.fill('#password', 'secret_sauce');
      await page.click('#login-button');
      await page.waitForSelector('.inventory_list');
      if (saveDomStep) await saveDomStep('inventory_page');
      await page.click('.inventory_item button');
      if (saveDomStep) await saveDomStep('after_add_to_cart');
      await page.click('.shopping_cart_link');
      if (saveDomStep) await saveDomStep('cart_page');
      await page.click('#checkout');
      if (saveDomStep) await saveDomStep('checkout_info');
      await page.fill('#first-name', 'John');
      await page.fill('#last-name', 'Doe');
      await page.fill('#postal-code', '12345');
      await page.click('#continue');
      if (saveDomStep) await saveDomStep('checkout_overview');
      await page.click('#finish');
      await page.waitForSelector('.complete-header');
      if (saveDomStep) await saveDomStep('order_confirmation');
      const msg = await page.textContent('.complete-header');
      if (!msg.toLowerCase().includes('thank you')) throw new Error('Order confirmation not displayed');
    }
  },
  {
    name: 'Logout from the application',
    steps: async (page, saveDomStep) => {
      await page.goto(BASE_URL);
      if (saveDomStep) await saveDomStep('login_page');
      await page.fill('#user-name', 'standard_user');
      await page.fill('#password', 'secret_sauce');
      await page.click('#login-button');
      await page.waitForSelector('.inventory_list');
      if (saveDomStep) await saveDomStep('inventory_page');
      await page.click('#react-burger-menu-btn');
      if (saveDomStep) await saveDomStep('menu_open');
      await page.click('#logout_sidebar_link');
      await page.waitForSelector('#login-button');
      if (saveDomStep) await saveDomStep('after_logout');
    }
  }
];


const { chromium } = require('playwright');


async function saveDom(page, scenarioIdx, stepName) {
  const dom = await page.content();
  const safeStep = stepName.replace(/[^a-zA-Z0-9_\-]/g, '_');
  const fileName = `scenario${scenarioIdx + 1}_${safeStep}.html`;
  const filePath = path.join(DOM_OUTPUT_DIR, fileName);
  fs.writeFileSync(filePath, dom, 'utf-8');
  return filePath;
}

async function runScenario(scenario, idx) {
  const browser = await chromium.launch({ channel: 'chrome', headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  let status = 'passed';
  let errorMsg = '';
  let snapshotPath = '';
  let domFiles = [];
  try {
    await scenario.steps(page, async (stepName) => {
      const domPath = await saveDom(page, idx, stepName);
      domFiles.push(domPath);
    });
  } catch (err) {
    status = 'failed';
    errorMsg = err.message;
    const snapFile = `scenario_${idx + 1}.png`;
    snapshotPath = path.join('snapshots', snapFile);
    await page.screenshot({ path: path.join(SNAPSHOT_DIR, snapFile), fullPage: true });
  }
  await browser.close();
  return {
    name: scenario.name,
    status,
    errorMsg,
    snapshot: snapshotPath,
    domFiles
  };
}

(async () => {
  const results = [];
  for (let i = 0; i < scenarios.length; i++) {
    const res = await runScenario(scenarios[i], i);
    results.push(res);
  }

  // Generate HTML report
  let html = `<!DOCTYPE html><html><head><meta charset='utf-8'><title>Sauce Demo Test Report</title>
  <style>body{font-family:sans-serif;} .passed{color:green;} .failed{color:red;} .scenario{margin-bottom:2em;} img{max-width:400px; border:1px solid #ccc;} ul{margin:0 0 1em 0;}</style>
  </head><body><h1>Sauce Demo Test Report</h1>`;
  for (const r of results) {
    html += `<div class='scenario'><h2>${r.name}</h2><p>Status: <span class='${r.status}'>${r.status.toUpperCase()}</span></p>`;
    if (r.domFiles && r.domFiles.length) {
      html += `<ul>`;
      for (const domFile of r.domFiles) {
        html += `<li><a href='${path.relative(REPORT_DIR, domFile).replace(/\\/g, "/")}' target='_blank'>View DOM: ${path.basename(domFile)}</a></li>`;
      }
      html += `</ul>`;
    }
    if (r.status === 'failed') {
      html += `<p>Error: ${r.errorMsg}</p>`;
      if (r.snapshot) html += `<img src='${r.snapshot}' alt='Failure snapshot'>`;
    }
    html += `</div>`;
  }
  html += '</body></html>';
  fs.writeFileSync(path.join(REPORT_DIR, 'sauce_demo_report.html'), html);
  console.log('Test execution complete. Report generated at reporting/sauce_demo_report.html');
})();

const { chromium } = require('../../../frontend/node_modules/@playwright/test');
const path = require('node:path');
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  for (const route of ['', 'connection', 'hair', 'consultation']) {
    await page.goto(`http://127.0.0.1:8081/${route}`, { waitUntil: 'networkidle' });
    await page.screenshot({ path: path.join(__dirname, `before-${route || 'home'}-390.png`), fullPage: true });
  }
  await browser.close();
})().catch(error => { console.error(error); process.exitCode = 1; });

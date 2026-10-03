// PC browser proxy for layout/state/API checks; physical Android is manual.
const { chromium } = require('../../../frontend/node_modules/@playwright/test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.MOBILE_TEST_URL || 'http://127.0.0.1:8081';
const api = process.env.MOBILE_TEST_API_URL || 'http://127.0.0.1:8001';
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const checks = [], calls = [], errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => { if (request.url().startsWith(api)) calls.push({ method: request.method(), url: request.url() }); });
  const button = label => page.getByRole('button', { name: label, exact: true });
  async function snapshot(name) {
    await page.evaluate(() => { for (const element of document.querySelectorAll('*')) if (element.scrollTop > 0) element.scrollTop = 0; });
    await page.screenshot({ path: path.join(__dirname, `after-${name}-390.png`), fullPage: true });
  }
  async function fit(label, action) {
    const sizes = await page.evaluate(() => ({ width: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth }));
    assert.ok(sizes.scroll <= sizes.width + 1, `${label}: horizontal overflow`);
    if (action) {
      const box = await button(action).boundingBox();
      assert.ok(box && box.y >= 0 && box.y + box.height <= page.viewportSize().height + 1, `${label}: bottom action outside viewport`);
    }
  }
  async function widths(label, action) {
    for (const width of [320, 360, 390, 430]) {
      await page.setViewportSize({ width, height: width === 320 ? 640 : 844 }); await fit(`${label}-${width}`, action);
    }
    await page.setViewportSize({ width: 390, height: 844 });
  }
  async function pick(label, file = 'portrait.png') {
    const chooser = page.waitForEvent('filechooser'); await button(label).click();
    await (await chooser).setFiles(path.join(__dirname, `fixture-${file}`));
    await page.getByTestId('photo-preview').waitFor();
  }
  async function cancel(label) {
    const chooser = page.waitForEvent('filechooser'); await button(label).click();
    await (await chooser).setFiles([]);
  }
  try {
    const health = await (await fetch(api + '/health')).json(); assert.equal(health.status, 'ok');
    await page.goto(base, { waitUntil: 'networkidle' });
    await button('Start Consultation ✦').waitFor();
    assert.equal(await button('Check API connection').count(), 0);
    assert.equal(await button('Check connection').count(), 0);
    assert.ok((await button('Start Consultation ✦').boundingBox()).y < (await button('Hair').boundingBox()).y);
    await widths('home'); await snapshot('home'); checks.push('home-hierarchy-settings-entry');
    await button('Settings').click(); await page.getByText('Connected · Your studio is available.', { exact: true }).waitFor();
    await snapshot('settings'); await widths('settings');
    await page.route(api + '/health', route => route.abort('failed'));
    await button('Check connection').click(); await page.getByRole('alert').waitFor();
    await snapshot('settings-error'); await page.unroute(api + '/health');
    await button('Check connection').click(); await page.getByText('Connected · Your studio is available.', { exact: true }).waitFor();
    checks.push('settings-health-error-recheck-recovery');
    await page.goto(base + '/connection', { waitUntil: 'networkidle' }); assert.ok(page.url().endsWith('/settings'));
    checks.push('legacy-diagnostic-deep-link');
    for (const [feature, label, route] of [['hairstyle', 'Hair', 'hair'], ['makeup', 'Makeup', 'makeup'], ['nails', 'Nails', 'nails']]) {
      const styles = await (await fetch(`${api}/features/${feature}/styles`)).json(); assert.ok(styles.length);
      const styleButton = row => button(`${row.name}. ${row.description}`);
      await page.goto(base, { waitUntil: 'networkidle' }); await button(label).click();
      assert.ok(await button('Continue to Style →').isDisabled());
      const pickerLabel = feature === 'nails' ? 'Choose your hand photo' : 'Choose your portrait';
      await cancel(pickerLabel); assert.equal(await page.getByTestId('photo-preview').count(), 0);
      await pick(pickerLabel); await cancel('Replace'); await page.getByText('portrait.png', { exact: true }).waitFor();
      await pick('Replace', 'replacement.png'); await page.getByText('replacement.png', { exact: true }).waitFor();
      await widths(`${route}-photo`, 'Continue to Style →'); if (feature === 'hairstyle') await snapshot('photo');
      await button('Continue to Style →').click(); await styleButton(styles[0]).waitFor();
      assert.ok(await button('Review your look →').isDisabled());
      assert.equal(await page.getByTestId('photo-preview').count(), 0);
      await styleButton(styles[styles.length - 1]).click(); // scroll to last style, fixed action remains visible
      await widths(`${route}-style`, 'Review your look →');
      if (feature === 'hairstyle') await snapshot('style');
      await button('Back').click(); await page.getByText('replacement.png', { exact: true }).waitFor();
      await button('Continue to Style →').click(); assert.match(await styleButton(styles[styles.length - 1]).textContent(), /✓/);
      await button('Review your look →').click(); await widths(`${route}-review`, 'Generate preview ✦');
      if (feature === 'hairstyle') await snapshot('review');
      await button('Change photo').click(); await page.getByText('replacement.png', { exact: true }).waitFor();
      await button('Continue to Style →').click(); await button('Review your look →').click();
      await button('Generate preview ✦').click(); await button('Try Another Style').waitFor();
      await page.getByText('Mock preview · Result', { exact: true }).waitFor();
      assert.ok(await button('Save').isDisabled()); assert.ok(await button('Share').isDisabled());
      await widths(`${route}-result`, 'Try Another Style');
      await button('Original').click(); await page.getByText('Mock preview · Original', { exact: true }).waitFor();
      await button('Result').click(); if (feature === 'hairstyle') await snapshot('result');
      await button('Back').click(); await button('Generate preview ✦').waitFor();
      await button('Generate preview ✦').click(); await button('Try Another Style').click();
      await styleButton(styles[0]).waitFor(); await styleButton(styles[0]).click();
      await button('Review your look →').click(); await button('Generate preview ✦').click();
      await button('Start Over').click(); assert.ok(await button('Continue to Style →').isDisabled());
      assert.equal(await page.getByTestId('photo-preview').count(), 0);
      await pick(pickerLabel); await button('Remove').click(); assert.ok(await button('Continue to Style →').isDisabled());
      await pick(pickerLabel); await button('Continue to Style →').click(); await button('Back').click();
      await page.getByTestId('photo-preview').waitFor(); await button('Back').click(); await button('Start Consultation ✦').waitFor();
      checks.push(`${feature}-real-catalog-${styles.length}-gallery-back-review-result-retry-reset`);
    }
    await button('Start Consultation ✦').click(); await widths('consultation-service', 'Continue to Direction →');
    await snapshot('consultation-service'); assert.ok(await button('Continue to Direction →').isDisabled());
    await button('Hair').click(); await pick('Choose your portrait'); await button('Continue to Direction →').click();
    await button('Occasion or event: Celebration').click(); await button('Desired vibe: Classic').click();
    await button('Maintenance preference: Low').click(); await button('Add optional details +').click();
    await page.getByRole('textbox', { name: 'Optional notes', exact: true }).fill('Local browser test brief');
    await widths('consultation-direction', 'Review your direction →'); await snapshot('consultation-direction');
    await button('Review your direction →').click(); await page.getByText('Occasion: Celebration', { exact: true }).waitFor();
    await widths('consultation-looks', 'Explore Custom Hair →'); await snapshot('consultation-looks');
    await button('Edit direction').click(); assert.equal(await page.getByRole('textbox', { name: 'Optional notes', exact: true }).inputValue(), 'Local browser test brief');
    await button('Back').click(); await button('Makeup').click(); await page.getByTestId('photo-preview').waitFor();
    await button('Nails').click(); assert.equal(await page.getByTestId('photo-preview').count(), 0);
    await pick('Choose your hand photo'); await button('Continue to Direction →').click();
    await button('Nail finish: French').click(); await button('Review your direction →').click();
    await button('Explore Custom Nails →').click(); await button('Review your look →').waitFor();
    await button('Back').click(); await page.getByTestId('photo-preview').waitFor();
    checks.push('consultation-local-three-stages-preferences-photo-compatibility-custom-handoff');
    // Controlled API catalog failure/empty state without touching backend configuration.
    await page.route(api + '/features/nails/styles', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Catalog temporarily unavailable.' }) }));
    await page.reload({ waitUntil: 'networkidle' }); await pick('Choose your hand photo'); await button('Continue to Style →').click();
    await page.getByRole('alert').filter({ hasText: 'Catalog temporarily unavailable.' }).waitFor(); await snapshot('catalog-error');
    await page.unroute(api + '/features/nails/styles'); await button('Retry connection').click();
    const nailStyles = await (await fetch(api + '/features/nails/styles')).json();
    await button(`${nailStyles[0].name}. ${nailStyles[0].description}`).waitFor();
    checks.push('catalog-error-retry-recovery');
    await page.route(api + '/features/nails/styles', route => route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }));
    await page.reload({ waitUntil: 'networkidle' }); await pick('Choose your hand photo'); await button('Continue to Style →').click();
    await page.getByText('No looks are available right now.', { exact: false }).waitFor();
    assert.ok(await button('Review your look →').isDisabled());
    await page.unroute(api + '/features/nails/styles'); await button('Refresh styles').click();
    await button(`${nailStyles[0].name}. ${nailStyles[0].description}`).waitFor(); checks.push('empty-catalog-refresh-recovery');
    await page.goto(base, { waitUntil: 'networkidle' });
    await page.setViewportSize({ width: 320, height: 640 }); await fit('home-small');
    await page.screenshot({ path: path.join(__dirname, 'after-home-320.png'), fullPage: true });
    await button('Nails').click(); await fit('photo-small', 'Continue to Style →');
    await page.screenshot({ path: path.join(__dirname, 'after-photo-320.png'), fullPage: true });
    // Pixel-dimension proxy only, not an Android screenshot or density claim.
    const phoneProxy = await browser.newPage({ viewport: { width: 360, height: 800 }, deviceScaleFactor: 3 });
    await phoneProxy.goto(base, { waitUntil: 'networkidle' });
    await phoneProxy.screenshot({ path: path.join(__dirname, 'after-home-1080x2400-browser-proxy.png'), fullPage: true });
    await phoneProxy.close();
    assert.equal(errors.length, 0, errors.join('\n'));
    assert.ok(calls.length > 0); assert.ok(calls.every(call => call.method === 'GET'));
    assert.ok(calls.every(call => /^\/health$|^\/features\/(hairstyle|makeup|nails)\/styles$/.test(new URL(call.url).pathname)));
    checks.push('zero-page-errors-read-only-api-no-generation');
    fs.writeFileSync(path.join(__dirname, 'checks.json'), JSON.stringify({ checks, calls, errors, widths: [320, 360, 390, 430] }, null, 2));
    console.log(JSON.stringify({ passed: checks.length, checks }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });

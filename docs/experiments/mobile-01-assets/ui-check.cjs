// Reproducible Expo web validation using existing repo Playwright tooling.
// Native Android gallery/runtime acceptance is a separate manual gate.
const { chromium } = require('../../../frontend/node_modules/@playwright/test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../../..');
const output = __dirname;
const base = process.env.MOBILE_TEST_URL || 'http://localhost:8091';
const apiBase = process.env.MOBILE_TEST_API_URL || 'http://127.0.0.1:8001';

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const failures = [], calls = [], checks = [];
  page.on('pageerror', error => failures.push(error.message));
  page.on('request', request => { if (request.url().startsWith(apiBase)) calls.push({ method: request.method(), url: request.url() }); });
  async function overflow(label) {
    const sizes = await page.evaluate(() => ({ width: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth }));
    assert.ok(sizes.scroll <= sizes.width + 1, `${label}: horizontal overflow ${JSON.stringify(sizes)}`);
  }
  async function pick(label, filename) {
    const chooser = page.waitForEvent('filechooser');
    await page.getByRole('button', { name: label, exact: true }).click();
    await (await chooser).setFiles(path.join(root, '.tmp/mobile-01', filename));
    await page.getByTestId('photo-preview').waitFor();
  }
  try {
    const health = await (await fetch(apiBase + '/health')).json();
    assert.equal(health.status, 'ok'); checks.push({ name: 'live_health', response: health });
    await page.goto(base, { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: 'Explore Hairstyle', exact: true }).waitFor();
    await page.screenshot({ path: path.join(output, 'home-390.png'), fullPage: true });
    for (const [route, feature, label] of [['hair', 'hairstyle', 'Hairstyle'], ['makeup', 'makeup', 'Makeup'], ['nails', 'nails', 'Nails']]) {
      const styles = await (await fetch(`${apiBase}/features/${feature}/styles`)).json();
      assert.ok(styles.length > 0);
      await page.getByRole('button', { name: `Explore ${label}`, exact: true }).click();
      await page.getByRole('button', { name: `${styles[0].name}. ${styles[0].description}`, exact: true }).waitFor();
      for (const width of [320, 360, 390, 430]) { await page.setViewportSize({ width, height: 844 }); await overflow(`${route}-${width}`); }
      checks.push({ name: 'live_catalog', feature, count: styles.length, firstId: styles[0].id });
      await page.setViewportSize({ width: 390, height: 844 });
      await pick(feature === 'nails' ? 'Choose your hand photo' : 'Choose your portrait', 'portrait.png');
      await page.getByRole('button', { name: `${styles[0].name}. ${styles[0].description}`, exact: true }).click();
      await page.getByRole('button', { name: 'Preview this look ✦', exact: true }).click();
      await page.getByText('Mock result', { exact: false }).waitFor();
      await page.getByText('This is your unchanged local photo', { exact: false }).waitFor();
      await overflow(`${route}-result`);
      if (feature === 'hairstyle') await page.screenshot({ path: path.join(output, 'result-390.png'), fullPage: true });
      await page.getByRole('button', { name: 'Back to your studio', exact: true }).click();
      await pick('Replace', 'replacement.png');
      await page.getByText('replacement.png', { exact: true }).waitFor();
      await page.getByRole('button', { name: 'Remove', exact: true }).click();
      assert.equal(await page.getByTestId('photo-preview').count(), 0);
      assert.ok(await page.getByRole('button', { name: 'Preview this look ✦', exact: true }).isDisabled());
      await page.getByRole('button', { name: 'Reset photo and style', exact: true }).click();
      await page.getByRole('button', { name: 'View sample failure state', exact: true }).click();
      await page.getByRole('alert').filter({ hasText: 'Sample preview failure' }).waitFor();
      checks.push({ name: 'photo_preview_replace_remove_reset_mock_failure', feature });
      if (feature === 'nails') await page.screenshot({ path: path.join(output, 'nails-390.png'), fullPage: true });
      await page.goto(base, { waitUntil: 'networkidle' });
    }
    await page.getByRole('button', { name: 'Consultation', exact: true }).click();
    await page.getByText('Service → Direction → Your Looks', { exact: true }).waitFor();
    await overflow('consultation'); checks.push({ name: 'consultation_overview_navigation' });
    await page.goto(base, { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: 'Check API connection', exact: true }).click();
    await page.getByText('Connected · ok', { exact: true }).waitFor(); checks.push({ name: 'connectivity_screen' });
    await page.route(apiBase + '/features/nails/styles', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Catalog temporarily unavailable.' }) }));
    await page.goto(base + '/nails', { waitUntil: 'networkidle' });
    await page.getByRole('alert').filter({ hasText: 'Catalog temporarily unavailable.' }).waitFor();
    await page.unroute(apiBase + '/features/nails/styles');
    await page.getByRole('button', { name: 'Retry connection', exact: true }).click();
    const recoveredStyles = await (await fetch(apiBase + '/features/nails/styles')).json();
    await page.getByRole('button', { name: `${recoveredStyles[0].name}. ${recoveredStyles[0].description}`, exact: true }).waitFor(); checks.push({ name: 'api_failure_and_explicit_retry' });
    assert.equal(failures.length, 0, failures.join('\n'));
    assert.ok(calls.length > 0); assert.ok(calls.every(call => call.method === 'GET'));
    assert.ok(calls.every(call => !/generate|consultations|deployment/.test(call.url)));
    checks.push({ name: 'no_upload_generation_or_worker_calls', count: calls.length });
    fs.writeFileSync(path.join(output, 'ui-results.json'), JSON.stringify({ status: 'VERIFIED', environment: 'Expo web in headless Edge, not Android', checks, requests: calls, pageErrors: failures }, null, 2));
    console.log(JSON.stringify({ passed: checks.length, pageErrors: failures.length, nativeAndroid: 'NEEDS VERIFICATION' }));
  } catch (error) {
    await page.screenshot({ path: path.join(output, 'failure.png'), fullPage: true });
    fs.writeFileSync(path.join(output, 'ui-failure.json'), JSON.stringify({ message: error.message, pageErrors: failures, checks }, null, 2));
    throw error;
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });

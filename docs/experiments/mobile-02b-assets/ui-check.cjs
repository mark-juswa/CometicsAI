// PC browser proxy only. Every API response is intercepted; no GPU is used.
// This does not prove native cookies, Android picker or live generation.
const { chromium } = require('../../../frontend/node_modules/@playwright/test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = 'http://127.0.0.1:8081';
const api = 'http://127.0.0.1:3000';
const fixtures = path.join(__dirname, '../mobile-02a-assets');
const user = { id: 'test-client', name: 'Test Client', email: 'test@example.test', role: 'client', avatar: null };
const style = { id: 'test_style', name: 'Test Style', description: 'Browser fixture only', status: 'available' };
const image = fs.readFileSync(path.join(fixtures, 'fixture-replacement.png')).toString('base64');
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const checks = [], errors = []; let signedIn = false, posts = 0, outcome = 'success', unavailable = false;
  let finish;
  page.on('pageerror', error => errors.push(error.message));
  await page.route(api + '/**', async route => {
    const request = route.request(), url = new URL(request.url());
    if (unavailable && url.pathname.endsWith('/session')) { await route.abort('failed'); return; }
    let body, status = 200;
    if (url.pathname.endsWith('/login')) {
      if (request.postDataJSON().password !== 'fixture') { status = 401; body = { error: 'Invalid email or password.' }; }
      else { signedIn = true; body = { user }; }
    } else if (url.pathname.endsWith('/session')) body = { user: signedIn ? user : null };
    else if (url.pathname.endsWith('/logout')) { signedIn = false; body = { success: true }; }
    else if (!signedIn) { status = 401; body = { error: 'Sign in to continue.' }; }
    else if (url.pathname.endsWith('/styles')) body = [style];
    else if (url.pathname.endsWith('/generate')) {
      posts++;
      assert.match(request.postData(), /name="image"/); assert.match(request.postData(), /name="style_id"/);
      await new Promise(resolve => { finish = resolve; });
      if (outcome === 'success') body = { status: 'completed', generator: 'remote_flux', style,
        image: { data_url: `data:image/png;base64,${image}`, content_type: 'image/png', width: 512, height: 512 }, metadata: { fixture: true } };
      else { status = outcome === 'validation' ? 400 : 503; body = { error: outcome === 'validation' ? 'Invalid image.' : 'AI service is unavailable.' }; }
    } else body = ['hairstyle', 'makeup', 'nails'].map(id => ({ id, name: id, description: 'Browser fixture' }));
    await route.fulfill({ status, contentType: 'application/json', headers: { 'Access-Control-Allow-Origin': root, 'Access-Control-Allow-Credentials': 'true' }, body: JSON.stringify(body) });
  });
  const button = label => page.getByRole('button', { name: label, exact: true });
  async function snapshot(name) { await page.screenshot({ path: path.join(__dirname, `${name}.png`), fullPage: true }); }
  async function widths(name, action) {
    for (const width of [320, 360, 390, 430]) {
      await page.setViewportSize({ width, height: width === 320 ? 640 : 844 });
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1), name);
      if (action) {
        const box = await button(action).boundingBox();
        assert.ok(box && box.y >= 0 && box.y + box.height <= page.viewportSize().height + 1, `${name} action`);
      }
    }
    await page.setViewportSize({ width: 390, height: 844 });
  }
  async function pick(label) {
    const chooser = page.waitForEvent('filechooser'); await button(label).click();
    await (await chooser).setFiles(path.join(fixtures, 'fixture-portrait.png'));
    await page.getByTestId('photo-preview').waitFor();
  }
  try {
    await page.goto(root, { waitUntil: 'networkidle' }); await button('Sign in').click();
    await page.getByLabel('Email address').fill(user.email); await page.getByLabel('Password').fill('wrong');
    await button('Sign in to BeautyCore').click(); await page.getByText('Invalid email or password.', { exact: true }).waitFor();
    await widths('login'); await snapshot('login-390');
    await page.getByLabel('Password').fill('fixture'); await button('Sign in to BeautyCore').click();
    await button('Start Consultation ✦').waitFor(); await widths('home');
    checks.push('login-error-client-session-home');
    await button('Settings').click(); await button('Check connection').click();
    await page.getByText('Client studio access confirmed.', { exact: true }).waitFor(); await snapshot('settings-390');
    unavailable = true; await button('Check connection').click(); await page.getByText('Cannot reach the application API. Check your connection and try again.', { exact: true }).waitFor();
    unavailable = false; await button('Check connection').click(); await page.getByText('Client studio access confirmed.', { exact: true }).waitFor();
    checks.push('settings-session-catalog-check');
    for (const [route, label] of [['hair', 'Choose your portrait'], ['makeup', 'Choose your portrait'], ['nails', 'Choose your hand photo']]) {
      await page.goto(root + '/' + route, { waitUntil: 'networkidle' }); await pick(label);
      await button('Continue to Style →').click(); await button('Test Style. Browser fixture only').click();
      await button('Review your look →').click(); await widths(route + '-review', 'Generate this look ✦');
      if (route === 'hair') await snapshot('review-390');
      const before = posts; await button('Generate this look ✦').dblclick();
      // A second physical click can land on the newly shown Keep browsing
      // action at the same coordinates. The POST must still remain singular.
      if (page.url().replace(/\/$/, '') === root) await button('View current generation').click();
      await page.getByText('Your look is processing…', { exact: true }).waitFor();
      assert.equal(posts, before + 1); await widths('generating', 'Keep browsing');
      if (route === 'hair') {
        await snapshot('generating-390'); await button('Keep browsing').click();
        await button('Start Consultation ✦').waitFor(); finish();
        await page.waitForTimeout(150); assert.equal(page.url().replace(/\/$/, ''), root);
        await button('View latest generation').click();
      } else finish();
      await button('Generated Result').waitFor(); await widths('result', 'Try Another Style');
      await button('Original').click(); await button('Generated Result').click();
      if (route === 'hair') await snapshot('result-fixture-390');
      if (route === 'nails') {
        await button('Start Over').click(); await button('Choose your hand photo').waitFor(); assert.ok(await button('Continue to Style →').isDisabled());
      } else {
        await button('Try Another Style').click(); await button('Test Style. Browser fixture only').waitFor();
        await button('Back').click(); await page.getByTestId('photo-preview').waitFor();
        await button('Remove').click(); assert.equal(await page.getByTestId('photo-preview').count(), 0);
      }
      checks.push(route + '-stages-single-post-navigation-result-photo-preserved');
    }
    await page.goto(root + '/hair', { waitUntil: 'networkidle' }); await pick('Choose your portrait');
    await button('Continue to Style →').click(); await button('Test Style. Browser fixture only').click(); await button('Review your look →').click();
    outcome = 'validation'; await button('Generate this look ✦').click(); await page.getByText('Your look is processing…', { exact: true }).waitFor(); finish();
    await button('Retry generation').waitFor(); const failedPosts = posts;
    await page.waitForTimeout(100); assert.equal(posts, failedPosts);
    outcome = 'unavailable'; await button('Retry generation').click(); await page.getByText('Your look is processing…', { exact: true }).waitFor(); finish();
    await button('Operator confirmed processing ended').waitFor();
    assert.equal(posts, failedPosts + 1); assert.equal(await button('Retry generation').count(), 0);
    await widths('uncertain', 'Operator confirmed processing ended'); await snapshot('uncertain-390');
    await button('Settings').click(); assert.ok(await button('Sign out').isDisabled());
    checks.push('validation-explicit-retry-ai-unavailable-uncertainty-lock');
    await page.reload({ waitUntil: 'networkidle' }); await button('Sign out').click();
    await button('Sign in').waitFor(); await page.goto(root + '/hair', { waitUntil: 'networkidle' }); await button('Sign in').waitFor();
    assert.equal(await button('Generate this look ✦').count(), 0);
    checks.push('logout-clears-session-and-protects-studios');
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(__dirname, 'ui-checks.json'), JSON.stringify({ checks, generation_posts: posts, real_gpu_requests: 0, console_errors: errors, widths: [320, 360, 390, 430] }, null, 2));
    console.log(JSON.stringify({ checks, generation_posts: posts, real_gpu_requests: 0 }));
  } catch (error) {
    console.error(JSON.stringify({ url: page.url(), text: await page.locator('body').innerText(), posts, errors }));
    throw error;
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });

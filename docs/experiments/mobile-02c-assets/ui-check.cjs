// All PC API calls are intercepted. This fixture makes zero GPU requests.
const { chromium } = require('../../../frontend/node_modules/@playwright/test');
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path');
const root = 'http://127.0.0.1:8081', api = 'http://127.0.0.1:3000';
const fixture = path.join(__dirname, '../mobile-02a-assets/fixture-portrait.png');
const image = fs.readFileSync(fixture).toString('base64');
const names = ['Crew Cut', 'Bob Cut', 'Bun'], ids = ['crew_cut', 'bob_cut', 'bun'];
const styles = ids.map((id, i) => ({ id, name: names[i], description: 'Browser fixture only', status: 'available' }));
const user = { id: 'fixture-client', name: 'Fixture Client', email: 'fixture@example.test', role: 'client', avatar: null };
function initial(feature = 'hairstyle') { return { primary_service: feature, stage: 'collecting', conversation_status: 'not_started', photo: null, messages: [], recommendations: null, generations: [], selected_recommendation_id: null }; }
function recs(feature) { return { recommendations: styles.map((s, i) => ({ id: `look_${i + 1}`, primary: { feature, style_id: s.id, style_name: s.name, nail_path: feature === 'nails' ? 'renderer' : null,
  service: { name: feature, currency: 'PHP', estimate_kind: 'demo_only', estimated_price: 500, estimated_duration_minutes: 40 } }, reason: 'Fits the direction from your conversation.', complements: [] })) }; }
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  page.setDefaultNavigationTimeout(120000);
  let server = initial(), messages = 0, posts = 0, statusReads = 0, selectedPosts = 0;
  let finish, outcome = 'completed', lost = false, geminiUnavailable = false, expired = false;
  const errors = [], checks = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.route(api + '/**', async route => {
    const request = route.request(), url = new URL(request.url()), p = url.pathname, method = request.method();
    const headers = { 'Access-Control-Allow-Origin': root, 'Access-Control-Allow-Credentials': 'true', 'Access-Control-Allow-Headers': 'content-type,x-ai-consultation-handle', 'Access-Control-Allow-Methods': 'GET,POST,PUT,PATCH' };
    if (method === 'OPTIONS') { await route.fulfill({ status: 204, headers }); return; }
    let body, status = 200;
    if (p.endsWith('/session')) body = { user };
    else if (p.endsWith('/mode')) body = { provider: 'gemini', model: 'server-only-ignored' };
    else if (p.endsWith('/catalog')) body = { styles: Object.fromEntries(['hairstyle', 'makeup', 'nails'].map(f => [f, styles.map(s => ({ ...s, style_id: s.id, feature: f }))])) };
    else if (p.endsWith('/styles')) body = styles;
    else if (p === '/api/ai/consultations') { server = initial(JSON.parse(request.postData()).primary_service); messages = 0; body = { ...server, handle: 'opaque.signed.handle' }; }
    else if (p.startsWith('/api/ai/consultations/')) {
      assert.equal(request.headers()['x-ai-consultation-handle'], 'opaque.signed.handle');
      if (expired) { status = 403; body = { error: 'Consultation access is invalid or expired.' }; }
      else if (p.endsWith('/photo')) { assert.equal(method, 'PUT'); assert.match(request.postData(), /name="image"/); assert.doesNotMatch(request.postData(), /name="style_id"/);
        server.photo = { content_type: 'image/png', width: 512, height: 512 }; body = server; }
      else if (p.endsWith('/state')) { if (method === 'PATCH') assert.ok(JSON.parse(request.postData()).preferences); body = server; }
      else if (p.endsWith('/turn')) {
        if (geminiUnavailable) { status = 503; body = { error: 'AI service could not complete the request.' }; }
        else { const message = JSON.parse(request.postData()).message; messages++;
          if (message) server.messages.push({ role: 'user', content: message });
          server.messages.push({ role: 'assistant', content: messages < 3 ? 'What length or finish feels right for you?' : 'Here are three directions for your look.' });
          server.conversation_status = messages < 3 ? 'more_information' : 'ready_for_recommendation';
          if (messages >= 3) { server.stage = 'recommended'; server.recommendations = recs(server.primary_service); server.generations = server.recommendations.recommendations.map(r => ({ recommendation_id: r.id, status: 'pending', error: null, attempts: 0, result_available: false })); }
          body = { state: server, status: server.conversation_status, recommendations: server.recommendations }; }
      } else if (p.endsWith('/generation')) {
        const id = p.split('/').at(-2), g = server.generations.find(r => r.recommendation_id === id);
        if (method === 'POST') { posts++; g.status = 'generating'; g.attempts++; await new Promise(r => { finish = r; }); g.status = outcome; g.result_available = outcome === 'completed'; g.error = outcome === 'failed' ? 'AI service unavailable.' : null; }
        else statusReads++;
        body = { generation: g, result: g.status === 'completed' ? { status: 'completed', generator: 'remote_flux', style: styles[Number(id.slice(-1)) - 1], image: { data_url: `data:image/png;base64,${image}`, content_type: 'image/png', width: 512, height: 512 }, metadata: { fixture: true } } : null };
        if (method === 'POST' && lost) { await route.abort('failed'); return; }
      } else if (p.endsWith('/select')) { selectedPosts++; const id = p.split('/').at(-2); assert.equal(server.generations.find(r => r.recommendation_id === id).status, 'completed'); server.selected_recommendation_id = id; body = server; }
      else throw new Error('Unrecognized fixture route ' + p);
    } else body = [];
    await route.fulfill({ status, headers, contentType: 'application/json', body: JSON.stringify(body) });
  });
  const button = name => page.getByRole('button', { name, exact: true });
  async function widths(name, action) {
    for (const width of [320, 360, 390, 430]) {
      await page.setViewportSize({ width, height: width === 320 ? 640 : 844 });
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1), name);
      if (action) { const box = await button(action).boundingBox(); assert.ok(box && box.y >= 0 && box.y + box.height <= page.viewportSize().height + 1, name + ' bottom action'); }
    }
    await page.setViewportSize({ width: 390, height: 844 });
  }
  async function screenshot(name) { await page.screenshot({ path: path.join(__dirname, name + '.png'), fullPage: true }); }
  async function start(feature = 'Hair') {
    await page.goto(root + '/consultation', { waitUntil: 'networkidle' }); await button(feature).click();
    const chooser = page.waitForEvent('filechooser'); await button(feature === 'Nails' ? 'Choose your hand photo' : 'Choose your portrait').click(); await (await chooser).setFiles(fixture);
    await button('Continue to Direction →').click(); await button('Occasion or event: Everyday').click(); await button('Desired vibe: Classic').click();
    await button('Begin AI conversation ✦').click();
  }
  async function answer() {
    await page.getByLabel('Your reply', { exact: true }).fill('Short and easy to maintain.'); await button('Send reply →').click();
  }
  try {
    await start(); await page.getByText('What length or finish feels right for you?', { exact: true }).waitFor();
    await widths('direction', 'Send reply →'); await screenshot('direction-fixture-390');
    await answer(); await page.getByText('What length or finish feels right for you?', { exact: true }).nth(1).waitFor();
    assert.equal(await button('See Your Looks →').count(), 0); await answer(); await button('See Your Looks →').click();
    await button('Generate Crew Cut').waitFor(); assert.equal(server.recommendations.recommendations.length, 3); assert.equal(posts, 0);
    await widths('looks', 'Explore Custom Hair →'); await screenshot('looks-fixture-390'); checks.push('real-contract-fixture-turns-readiness-exact-three');
    await button('Back').click(); await button('See Your Looks →').click(); await button('Generate Crew Cut').click();
    await page.getByText('Creating your recommended look', { exact: true }).waitFor(); assert.ok(await button('Generate Bob Cut').isDisabled());
    assert.ok(await button('Start consultation over').isDisabled()); await widths('generating', 'Explore Custom Hair →'); await screenshot('generating-fixture-390');
    await button('Settings').click(); assert.ok(await button('Sign out').isDisabled()); await page.goBack();
    finish(); await button('View Crew Cut').waitFor(); assert.equal(posts, 1); await button('View Crew Cut').click();
    await button('Original').click(); await page.getByLabel('Original consultation photo').waitFor(); await button('Generated Result').click();
    await page.getByLabel('Generated recommended result').waitFor(); await widths('result', 'Select This Look'); await screenshot('result-fixture-390');
    await button('Select This Look').click(); await button('This Look is selected ✓').waitFor(); assert.equal(selectedPosts, 1);
    await screenshot('selected-fixture-390'); await button('Back to Your Looks').click();
    checks.push('serial-generation-real-shaped-image-original-result-select');
    await button('Explore Custom Hair →').click(); await button('Crew Cut. Browser fixture only').waitFor();
    await button('Back').click(); await page.getByTestId('photo-preview').waitFor(); checks.push('custom-photo-retained-style-stage');
    for (const feature of ['Makeup', 'Nails']) { await start(feature); await answer(); await answer(); await button('See Your Looks →').click();
      await button('Generate Crew Cut').waitFor(); assert.equal(server.primary_service, feature === 'Makeup' ? 'makeup' : 'nails'); assert.equal(posts, 1); }
    checks.push('makeup-nails-contract-only-no-generation');
    await start(); await answer(); await answer(); await button('See Your Looks →').click(); outcome = 'failed';
    await button('Generate Crew Cut').click(); await page.getByText('Creating your recommended look', { exact: true }).waitFor(); finish();
    await button('Retry Crew Cut').waitFor(); assert.equal(posts, 2); outcome = 'completed'; lost = true;
    await button('Retry Crew Cut').click(); await page.getByText('Creating your recommended look', { exact: true }).waitFor(); finish();
    await button('View Crew Cut').waitFor(); assert.equal(posts, 3); assert.ok(statusReads >= 1); checks.push('failed-manual-retry-lost-response-get-recovery-no-replay');
    await button('Start consultation over').click(); await button('Hair').click(); const chooser = page.waitForEvent('filechooser');
    await button('Choose your portrait').click(); await (await chooser).setFiles(fixture); await button('Continue to Direction →').click();
    geminiUnavailable = true; await button('Begin AI conversation ✦').click(); await button('Check consultation status').waitFor();
    await page.getByText('AI service could not complete the request.', { exact: true }).waitFor();
    geminiUnavailable = false; await button('Check consultation status').click(); await button('Ask the opening question →').waitFor();
    await button('Ask the opening question →').click(); await button('Send reply →').waitFor(); expired = true;
    await answer(); await page.getByText(/Consultation access has expired/).waitFor(); await widths('expired'); await screenshot('expired-fixture-390');
    checks.push('gemini-unavailable-state-read-expired-handle-controlled');
    assert.deepEqual(errors, []);
    const report = { checks, widths: [320, 360, 390, 430], intercepted_generation_posts: posts, status_reads: statusReads, select_posts: selectedPosts, real_gpu_requests: 0, console_errors: errors };
    fs.writeFileSync(path.join(__dirname, 'ui-checks.json'), JSON.stringify(report, null, 2)); console.log(JSON.stringify(report));
  } catch (e) { await screenshot('failure'); console.error(JSON.stringify({ url: page.url(), text: await page.locator('body').innerText(), posts, errors })); throw e; }
  finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });

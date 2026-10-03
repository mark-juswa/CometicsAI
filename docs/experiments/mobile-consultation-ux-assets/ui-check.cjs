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
  let server = initial(), messages = 0, posts = 0, statusReads = 0, selectedPosts = 0, emptyTurns = 0;
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
        else if (!JSON.parse(request.postData()).message) { emptyTurns++; status = 502; body = { error: 'At least one user answer is required.' }; }
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
  async function widths(stage, action) {
    for (const width of [320, 360, 390, 430]) {
      await page.setViewportSize({ width, height: width === 320 ? 640 : 844 });
      const measure = await page.evaluate(() => ({ page: document.documentElement.scrollWidth, view: document.documentElement.clientWidth }));
      assert.ok(measure.page <= measure.view + 1, `${stage} overflow at ${width}: ${JSON.stringify(measure)}`);
      if (width === 320 && ['service', 'direction-empty', 'looks'].includes(stage))
        await page.screenshot({ path: path.join(__dirname, `${stage}-after-320.png`), fullPage: true });
      if (action) {
        const box = await button(action).boundingBox();
        assert.ok(box && box.y >= 0 && box.y + box.height <= page.viewportSize().height + 1, `${stage} action outside ${width}`);
      }
    }
    await page.setViewportSize({ width: 390, height: 844 });
  }
  async function shot(name) { await page.screenshot({ path: path.join(__dirname, name + '.png'), fullPage: true }); }
  try {
    await page.goto(root + '/consultation', { waitUntil: 'networkidle' });
    await button('Hairstyle').waitFor();
    assert.equal(await button('Choose your portrait').count(), 0);
    assert.equal(await button('Continue →').isDisabled(), true);
    await button('Makeup').click(); await button('Nails').click();
    await button('Hairstyle').click();
    await widths('service', 'Continue →'); await shot('service-after-390');
    await button('Continue →').click();
    await button('Choose your portrait').waitFor();
    assert.equal(await button('Occasion or event: Everyday').count(), 0);
    await button('Add a few preferences (optional) +').click();
    await button('Occasion or event: Everyday').waitFor();
    await button('Hide optional preferences −').click();
    assert.equal(await button('Start AI consultation ✦').isDisabled(), true);
    await widths('direction-empty', 'Start AI consultation ✦'); await shot('direction-empty-after-390');
    const cancel = page.waitForEvent('filechooser'); await button('Choose your portrait').click(); await (await cancel).setFiles([]);
    assert.equal(await button('Start AI consultation ✦').isDisabled(), true);
    const choose = page.waitForEvent('filechooser'); await button('Choose your portrait').click(); await (await choose).setFiles(fixture);
    await page.getByTestId('photo-preview').waitFor();
    const replace = page.waitForEvent('filechooser'); await button('Change photo').click(); await (await replace).setFiles([]);
    await page.getByTestId('photo-preview').waitFor();
    await button('Remove photo').click(); await button('Choose your portrait').waitFor();
    const again = page.waitForEvent('filechooser'); await button('Choose your portrait').click(); await (await again).setFiles(fixture);
    await page.getByLabel('Describe your look', { exact: true }).fill('A classic low maintenance haircut.');
    await widths('direction-ready', 'Start AI consultation ✦'); await shot('direction-ready-after-390');
    await button('Start AI consultation ✦').click();
    await page.getByText('What length or finish feels right for you?', { exact: true }).waitFor();
    assert.equal(messages, 1); assert.equal(emptyTurns, 0);
    await widths('conversation', 'Send reply →'); await shot('conversation-after-390');
    await page.getByLabel('Your reply', { exact: true }).fill('Short and easy to maintain.'); await button('Send reply →').click();
    await page.getByLabel('Your reply', { exact: true }).fill('Natural finish.'); await button('Send reply →').click();
    await button('Explore My Looks →').waitFor(); await button('Explore My Looks →').click();
    assert.equal(server.recommendations.recommendations.length, 3);
    assert.equal(await button('Generate this look ✦').count(), 1);
    await widths('looks', 'Generate this look ✦'); await shot('looks-after-390');
    await button('View look 2: Bob Cut').click();
    await page.getByText('Bob Cut', { exact: true }).last().waitFor();
    assert.equal(await button('Generate this look ✦').count(), 1);
    await shot('look-two-after-390');
    await button('Back').click(); await page.getByText('We’ve got your direction.').waitFor();
    await button('Explore My Looks →').click(); await page.getByRole('link', { name: 'Custom Hairstyle' }).click();
    await button('Crew Cut. Browser fixture only').waitFor();
    await button('Back').click(); await page.getByTestId('photo-preview').waitFor();
    assert.equal(posts, 0);
    assert.deepEqual(errors, []);
    const report = { checks: ['service-choice-only', 'direction-gallery-cancel-replace-remove', 'first-text-turn-once', 'three-recommendations', 'one-featured-look-at-a-time', 'custom-photo-handoff'], widths: [320,360,390,430], generation_posts: posts, empty_turns: emptyTurns, console_errors: errors };
    fs.writeFileSync(path.join(__dirname, 'ui-checks.json'), JSON.stringify(report, null, 2)); console.log(JSON.stringify(report));
  } catch (e) { await shot('failure'); console.error(JSON.stringify({ url: page.url(), text: await page.locator('body').innerText(), posts, errors })); throw e; }
  finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });

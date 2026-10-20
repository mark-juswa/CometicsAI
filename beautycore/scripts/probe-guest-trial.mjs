import { writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
const origin = 'https://beautycore-demo.onrender.com';

/** Read-only ingress verification. No auth, guest creation or inference request. */
export async function probeGuestTrial(upstreamFetch = fetch) {
  const results = [];
  for (const [index, address] of [null, '203.0.113.7', '198.51.100.9', '1.1.1.1', '8.8.8.8'].entries()) {
    const headers = { 'x-beautycore-proxy-probe': 'v1' };
    if (address) headers['cf-connecting-ip'] = address;
    try {
      const response = await upstreamFetch(origin + '/api/ai-trial/availability', {
        headers, cache: 'no-store', redirect: 'error', signal: AbortSignal.timeout(20000),
      });
      const cloudflare = !!response.headers.get('cf-ray') && response.headers.get('server')?.toLowerCase() === 'cloudflare';
      const html = response.headers.get('content-type')?.toLowerCase().includes('text/html') === true;
      const value = html ? null : await response.json().catch(() => null);
      if (html) await response.body?.cancel();
      results.push({
        test: index === 0 ? 'baseline' : index <= 2 ? 'reserved-address-' + index : 'public-address-' + index,
        status: response.status, enabled: value?.enabled === true,
        addressPresent: value?.proxy_probe?.cloudflare_address_present === true,
        reservedTestAddressSeen: value?.proxy_probe?.reserved_test_address_seen === true,
        probeAvailable: typeof value?.proxy_probe?.reserved_test_address_seen === 'boolean',
        edgeDenied: response.status === 403 && cloudflare && html,
      });
    } catch {
      results.push({ test: index, status: 'unavailable', probeAvailable: false, edgeDenied: false });
    }
  }
  const baseline = results[0];
  const ready = baseline.status === 200 && baseline.probeAvailable && baseline.addressPresent &&
    !baseline.reservedTestAddressSeen &&
    results.slice(1, 3).every(r => r.edgeDenied || r.status === 200 && r.probeAvailable &&
      r.addressPresent && !r.reservedTestAddressSeen) &&
    // The endpoint's echo detector covers reserved addresses only. Public test
    // values must be rejected at the edge; a200 here needs additional investigation.
    results.slice(3).every(r => r.edgeDenied);
  return { website: origin, requests: results,
    readyForCfConnectingIpConfiguration: ready };
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const result = await probeGuestTrial();
  console.log(JSON.stringify(result, null, 2));
  if (process.argv[2]) writeFileSync(process.argv[2], JSON.stringify(result, null, 2) + '\n');
}

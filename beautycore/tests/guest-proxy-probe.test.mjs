import test from 'node:test';
import assert from 'node:assert/strict';
import { probeGuestTrial } from '../scripts/probe-guest-trial.mjs';
const probe = (present = true, seen = false) => Response.json({enabled:false,proxy_probe:{
 cloudflare_address_present:present,reserved_test_address_seen:seen}});
const denied = (cf = true) => new Response('<html>Denied</html>',{status:403,headers:{
 'content-type':'text/html',...(cf?{'server':'cloudflare','cf-ray':'test-ray'}:{})}});
async function fixture(replies) {
 let index=0;const calls=[];
 const result=await probeGuestTrial(async(url,init)=>{
  calls.push({url,init});return replies[index++]();
 });
 assert.equal(calls.length,5);
 assert.ok(calls.every(c=>c.url==='https://beautycore-demo.onrender.com/api/ai-trial/availability'
  &&c.init.redirect==='error'&&!c.init.body&&!c.init.method));
 assert.ok(!JSON.stringify(result).includes('203.0.113.7'));
 return result;
}
test('valid baseline plus Cloudflare edge denial of all four spoofed values passes',async()=>{
 const r=await fixture([()=>probe(),()=>denied(),()=>denied(),()=>denied(),()=>denied()]);
 assert.equal(r.readyForCfConnectingIpConfiguration,true);
});
test('reserved header overwrite with denied public header values also passes',async()=>{
 const r=await fixture([()=>probe(),()=>probe(),()=>probe(),()=>denied(),()=>denied()]);
 assert.equal(r.readyForCfConnectingIpConfiguration,true);
});
test('non-Cloudflare403 and missing or stale route cannot count as a successful check',async()=>{
 for(const first of [()=>Response.json({}, {status:404}),()=>probe(false),()=>probe()])
  assert.equal((await fixture([first,()=>denied(false),()=>denied(),()=>denied(),()=>denied()])).readyForCfConnectingIpConfiguration,false);
});
test('reflected reserved test address or unverifiable public200 fails closed',async()=>{
 for(const responses of [
  [()=>probe(),()=>probe(true,true),()=>denied(),()=>denied(),()=>denied()],
  [()=>probe(),()=>denied(),()=>denied(),()=>probe(),()=>denied()],
 ]) assert.equal((await fixture(responses)).readyForCfConnectingIpConfiguration,false);
});
test('network failure cannot pass the ingress gate',async()=>{
 const r=await fixture([()=>probe(),()=>{throw new Error('network');},()=>denied(),()=>denied(),()=>denied()]);
 assert.equal(r.readyForCfConnectingIpConfiguration,false);
});

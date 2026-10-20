import { writeFileSync } from 'node:fs';
const origin='https://beautycore-demo.onrender.com';
const results=[];
for (const testAddress of [null,'203.0.113.7','198.51.100.9']) {
 const headers={'x-beautycore-proxy-probe':'v1'};
 if(testAddress) { headers['cf-connecting-ip']=testAddress;headers['x-forwarded-for']=testAddress; }
 try {
  const response=await fetch(origin+'/api/ai-trial/availability',{
   headers,cache:'no-store',redirect:'error',signal:AbortSignal.timeout(20000)});
  const value=await response.json().catch(()=>null);
  results.push({test: testAddress ? 'reserved-address-'+results.length : 'baseline',
   status:response.status,enabled:value?.enabled===true,
   addressPresent:value?.proxy_probe?.cloudflare_address_present===true,
   reservedTestAddressSeen:value?.proxy_probe?.reserved_test_address_seen===true,
   probeAvailable:typeof value?.proxy_probe?.reserved_test_address_seen==='boolean'});
 } catch {results.push({test:results.length,status:'unavailable',probeAvailable:false});}
}
const result={website:origin,requests:results,
 readyForCfConnectingIpConfiguration:results.every(r=>r.status===200&&r.probeAvailable&&r.addressPresent&&!r.reservedTestAddressSeen)};
console.log(JSON.stringify(result,null,2));
if(process.argv[2]) writeFileSync(process.argv[2],JSON.stringify(result,null,2)+'\n');

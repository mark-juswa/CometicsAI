import test from 'node:test';
import assert from 'node:assert/strict';
let calls=[],ready=true,fail=false,release,blocked=false;
test.mock.module('@neondatabase/serverless',{namedExports:{neon:()=>({query:async sql=>{calls.push(sql);if(fail)throw new Error('fixture unavailable');if(sql.includes('to_regprocedure'))return[{ready}];if(blocked)await new Promise(r=>release=r);return[{processed:0}];}})}});
const original=process.env.DATABASE_URL;
process.env.DATABASE_URL='postgresql://fixture.invalid/test';
const {startNoShowWorker}=await import('../scripts/no-show-worker.mjs');
const settle=async()=>{for(let i=0;i<8;i++)await Promise.resolve();};
test.after(()=>{if(original===undefined)delete process.env.DATABASE_URL;else process.env.DATABASE_URL=original;});
test('worker checks immediately and every ten seconds, does not overlap sweeps, and stops cleanly',async t=>{
 calls=[];ready=true;fail=false;blocked=false;t.mock.timers.enable({apis:['setInterval']});
 const stop=startNoShowWorker();await settle();assert.equal(calls.length,2);
 blocked=true;t.mock.timers.tick(10000);await settle();const pending=calls.length;t.mock.timers.tick(20000);await settle();assert.equal(calls.length,pending);
 blocked=false;release();await settle();t.mock.timers.tick(10000);await settle();assert.equal(calls.length,pending+2);
 stop();t.mock.timers.tick(10000);await settle();assert.equal(calls.length,pending+2);
});
test('worker waits for installation and retries database failures without exposing details',async t=>{
 calls=[];ready=false;fail=false;t.mock.timers.enable({apis:['setInterval']});const errors=[];t.mock.method(console,'error',s=>errors.push(s));
 const stop=startNoShowWorker();await settle();assert.equal(calls.length,1);
 ready=true;fail=true;t.mock.timers.tick(10000);await settle();assert.equal(errors.length,1);
 fail=false;t.mock.timers.tick(10000);await settle();assert.ok(calls.at(-1).includes('beautycore_process_no_shows()'));assert.ok(!errors[0].includes('postgresql'));
 stop();
});

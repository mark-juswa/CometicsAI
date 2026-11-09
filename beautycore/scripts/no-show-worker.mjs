import { neon } from '@neondatabase/serverless';
import { createRequire } from 'node:module';
const require=createRequire(import.meta.url);
const {loadEnvConfig}=require('@next/env');
loadEnvConfig(process.cwd());
export function startNoShowWorker() {
  let busy=false, warned=false, stopped=false;
  const tick=async()=>{
    if(busy||stopped)return;
    busy=true;
    try {
      if(!process.env.DATABASE_URL)throw new Error('missing configuration');
      const sql=neon(process.env.DATABASE_URL);
      const ready=await sql.query("SELECT to_regprocedure('beautycore_process_no_shows(timestamp with time zone)') IS NOT NULL AS ready");
      if(ready[0]?.ready)await sql.query('SELECT beautycore_process_no_shows()');
      warned=false;
    }catch{
      if(!warned)console.error('No-show worker could not reach the scheduling database; it will retry.');
      warned=true;
    }finally{busy=false;}
  };
  void tick();
  const timer=setInterval(tick,10000);timer.unref();
  return ()=>{stopped=true;clearInterval(timer);};
}
if(process.argv[1]?.endsWith('no-show-worker.mjs')) {
  const stop=startNoShowWorker();
  // Standalone worker intentionally keeps running even without the web server.
  const keepAlive=setInterval(()=>{},60000);
  const end=()=>{stop();clearInterval(keepAlive);};
  process.once('SIGINT',end);process.once('SIGTERM',end);
}

"""Real CPU API/gateway + loopback GPU comparison; no browser, Gemini or Render."""
import argparse
import asyncio
import base64
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))


def decoded(payload):
    from PIL import Image
    raw=base64.b64decode(payload['image']['data_url'].split(',',1)[1],validate=True)
    with Image.open(BytesIO(raw)) as opened:
        if opened.format!='PNG': raise RuntimeError('Expected PNG result')
        rgb=opened.convert('RGB');rgb.load()
    return raw,rgb


def preservation(source, final, mask, fingers):
    import numpy as np
    if final.size!=source.size or mask.size!=source.size or len(fingers)!=5:
        raise RuntimeError('Expected the same full-hand frame and five refined finger masks')
    changed=np.any(np.asarray(final)!=np.asarray(source),axis=2)
    outside=int(changed[np.asarray(mask)<=127].sum())
    edits={name:int(changed[np.asarray(value)>127].sum()) for name,value in fingers.items()}
    if outside or not all(edits.values()):
        raise RuntimeError('Outside-mask change or an expected fingernail was not edited')
    return {'changed_outside_mask_pixels':outside,'changed_pixels_per_finger':edits}


def compare_records(records):
    grouped={}
    for row in records:
        pair=grouped.setdefault(row['case'],{})
        if row['mode'] not in ('baseline','candidate') or row['mode'] in pair:
            raise RuntimeError('Duplicate/invalid comparison mode')
        pair[row['mode']]=row
    result=[]
    for name,pair in grouped.items():
        if set(pair)!= {'baseline','candidate'}: raise RuntimeError('Incomplete comparison: '+name)
        a,b=pair['baseline'],pair['candidate']
        same=a['rgb_sha256']==b['rgb_sha256']
        masks=a.get('mask_pixels_sha256')==b.get('mask_pixels_sha256')
        result.append({'case':name,'baseline_seconds':a['wall_seconds'],'candidate_seconds':b['wall_seconds'],
            'observed_saving_percent':100*(a['wall_seconds']-b['wall_seconds'])/a['wall_seconds'] if a['wall_seconds']>0 else None,
            'pixels_equal':same,'mask_pixels_equal':masks,'png_bytes_equal':a['png_sha256']==b['png_sha256'],
            'note':'One paired application observation; no median/percentile/generalization claim.'})
    return result


async def rehearse(output):
    import httpx
    from PIL import Image
    from app import main
    from app.demo_gateway import create_gateway
    key=os.environ['AI_BACKEND_API_KEY']
    gpu_key=os.environ['AI_REMOTE_API_KEY']
    if output.exists(): raise RuntimeError('Choose a fresh output directory')
    output.mkdir(parents=True)
    fixture=ROOT.parent/'fixtures/hand.png'
    hand=Image.open(fixture).convert('RGB')
    inputs={'hairstyle':ROOT.parent/'gpu-src/gate1/inputs/hairstyle.png',
            'makeup':ROOT.parent/'gpu-src/gate1/inputs/makeup.jpg','nails':fixture}
    captures={}
    # Observe the actual refined masks without replacing segmentation/refinement/compositing.
    pipeline=main.nails_pipeline()
    original=pipeline.segmenter.segment_fingertips
    def observed(*args,**kwargs):
        mask,fingers=original(*args,**kwargs)
        captures.update(mask=mask.copy(),fingers={k:v.copy() for k,v in fingers.items()})
        return mask,fingers
    pipeline.segmenter.segment_fingertips=observed
    report={'status':'IN_PROGRESS','scope':'Actual CPU API/gateway + loopback GPU, one approved full hand',
        'gemini_called':False,'browser_or_render_tested':False,'modes':{},'requests':[],
        'source_sha256':{feature:sha256(path.read_bytes()).hexdigest() for feature,path in inputs.items()},
        'source_files':{'hand':'hand.png'},'limits':['Deterministic built-in recommendation provider for reproducible generation; no Gemini conversation test',
        'One paired observation per application case; no universal speed claim',
        'In-process ASGI gateway and real loopback HTTP worker, no Next.js/browser/network/device acceptance',
        'Mask observer copies are included equally in measured requests; no segmentation reuse optimization',
        'Baseline runs first; first-request warm-up/order effects may affect single-pair timings',
        'Consultation first/all timings include local result checks between sequential calls, not browser-visible completion']}
    (output/'hand.png').write_bytes(fixture.read_bytes())
    def save(): (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8765',headers={'X-API-Key':gpu_key},timeout=30,follow_redirects=False) as worker:
      try:
        for mode in ('baseline','candidate'):
            control=await worker.post('/rehearsal/mode',json={'mode':mode});control.raise_for_status()
            gateway=create_gateway(main.app,key)
            headers={'x-ai-backend-key':key,'x-ai-user-id':'rehearsal-client'}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=gateway),base_url='http://private-rehearsal',headers=headers,timeout=None) as client:
                assert (await client.get('/features',headers={'x-ai-backend-key':''})).status_code==401
                async def generation(path,case,feature,style,**kwargs):
                    captures.clear()
                    before=(await worker.get('/status')).json()
                    start=time.perf_counter()
                    print('REHEARSAL START',mode,case,'request',len(report['requests'])+1,'of 20',flush=True)
                    response=await client.post(path,**kwargs)
                    if response.status_code!=202: raise RuntimeError(case+': admission HTTP '+str(response.status_code))
                    job=response.json()['job_id']
                    assert (await client.get('/jobs/'+job,headers={**headers,'x-ai-user-id':'other-client'})).status_code==404
                    assert (await client.post('/features/makeup/generate')).status_code==429
                    last_update=start
                    while True:
                        status=await client.get('/jobs/'+job)
                        if status.status_code!=200: raise RuntimeError('Job status failed; no automatic retry')
                        if status.json()['status']!='generating': break
                        if time.perf_counter()-start>1200: raise RuntimeError('Request exceeded 20 minutes; no automatic retry')
                        if time.perf_counter()-last_update>=15:
                            audit=(await worker.get('/status')).json()['requests']
                            completed=len(audit)-len(before['requests'])
                            print('REHEARSAL WAIT',mode,case,round(time.perf_counter()-start),'seconds; worker calls finished',completed,flush=True)
                            last_update=time.perf_counter()
                        await asyncio.sleep(2)
                    result=await client.get('/jobs/'+job+'/result')
                    if result.status_code!=200: raise RuntimeError(case+': result HTTP '+str(result.status_code)+' '+result.text[:200])
                    body=result.json()
                    if 'generation' in body:
                        assert body['generation']['status']=='completed'
                        body=body['result']
                    if body['status']!='completed' or body['style']['id']!=style: raise RuntimeError('Incorrect generation result')
                    elapsed=time.perf_counter()-start
                    raw,rgb=decoded(body)
                    name=mode+'-'+case+'.png';(output/name).write_bytes(raw)
                    after=(await worker.get('/status')).json()
                    if after['foundation_load_count']!=1 or not after['gpu_runtime_ready']: raise RuntimeError('Worker lost one-foundation readiness')
                    audit=after['requests'][len(before['requests']):]
                    expected=5 if feature=='nails' and style in ('classic_red','glossy_black') else 0 if feature=='nails' else 1
                    if len(audit)!=expected: raise RuntimeError('Unexpected worker request count')
                    row={'case':case,'mode':mode,'style_id':style,'feature':feature,'wall_seconds':elapsed,
                         'png_sha256':sha256(raw).hexdigest(),'rgb_sha256':sha256(rgb.tobytes()).hexdigest(),
                         'result':name,'metadata':body['metadata'],'worker_requests':audit}
                    if feature=='nails':
                        if body['metadata']['nails_edited']!=5: raise RuntimeError('Expected all five nails')
                        row.update(preservation(hand,rgb,captures['mask'],captures['fingers']))
                        mask=captures['mask'];name=mode+'-'+case+'-mask.png';mask.save(output/name)
                        row.update(mask_file=name,mask_pixels_sha256=sha256(mask.tobytes()).hexdigest())
                        if style in ('classic_red','glossy_black') and body['metadata']['inference_steps']!=8: raise RuntimeError('Nails inference steps changed')
                    report['requests'].append(row);save()
                    print('REHEARSAL DONE',mode,case,round(elapsed,2),'seconds;',expected,'worker calls',flush=True)
                    return row
                async def manual(feature,style,case):
                    p=inputs[feature]
                    return await generation('/features/'+feature+'/generate',case,feature,style,
                        data={'style_id':style},files={'image':(p.name,p.read_bytes(),'image/jpeg' if p.suffix=='.jpg' else 'image/png')})
                async def consultation(feature,expected):
                    created=await client.post('/consultations',json={'primary_service':feature});assert created.status_code==201
                    identity=created.json()['id'];p=inputs[feature]
                    photo=await client.put('/consultations/'+identity+'/photo',files={'image':(p.name,p.read_bytes(),'image/png')});assert photo.status_code==200
                    recommendations=await client.post('/consultations/'+identity+'/recommendations');assert recommendations.status_code==200
                    rows=recommendations.json()['recommendations']
                    styles=[r['primary']['style_id'] for r in rows]
                    if styles!=expected: raise RuntimeError('Recommendation catalog changed: '+repr(styles))
                    times=[];start=time.perf_counter()
                    for item in rows:
                        style=item['primary']['style_id'];path=f"/consultations/{identity}/recommendations/{item['id']}/generation"
                        await generation(path,feature+'-'+style,feature,style)
                        detail=await client.get(path);assert detail.status_code==200 and detail.json()['generation']['status']=='completed'
                        times.append(time.perf_counter()-start)
                    selected=await client.post(f"/consultations/{identity}/recommendations/{rows[0]['id']}/select")
                    assert selected.status_code==200 and selected.json()['selected_recommendation_id']==rows[0]['id']
                    return {'styles':styles,'first_result_seconds':times[0],'all_three_seconds':times[-1],'selected_completed_look':True}
                report['modes'][mode]={}
                report['modes'][mode]['hair_consultation']=await consultation('hairstyle',['bob_hair','bun','crew_cut'])
                await manual('makeup','natural_makeup','makeup-natural_makeup')
                restored=await manual('hairstyle','crew_cut','hair-restored-crew_cut')
                crew=next(r for r in report['requests'] if r['mode']==mode and r['case']=='hairstyle-crew_cut')
                if restored['rgb_sha256']!=crew['rgb_sha256']: raise RuntimeError('Hair restoration changed the output')
                report['modes'][mode]['nails_consultation']=await consultation('nails',['classic_red','french_tip','glossy_black'])
                for style in ('nude_pink','pink_ombre'): await manual('nails',style,'nails-'+style)
                report['modes'][mode]['final_health']=(await worker.get('/health')).json()
                save()
        report['comparisons']=compare_records(report['requests'])
        if not all(r['pixels_equal'] and r['mask_pixels_equal'] for r in report['comparisons']):
            raise RuntimeError('Output/mask differences require review; candidate not accepted')
        report['status']='APPLICATION_COMPARISON_COMPLETE_VISUAL_REVIEW_REQUIRED'
        print('REHEARSAL COMPLETE: compare full-hand outputs; no live system changed.',flush=True)
      except BaseException as exc:
        report['status']='FAILED';report['error_type']=type(exc).__name__
        raise
      finally:
        pipeline.segmenter.segment_fingertips=original
        save()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    asyncio.run(rehearse(parser.parse_args().output.resolve()))

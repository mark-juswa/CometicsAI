"""Private matched GPU benchmark. No HTTP server, tunnel or deployment.

Uses the approved Gate inputs. Nails cases are one localized crop, not a
full-hand performance/quality claim. End-to-end app acceptance is separate.
"""
import argparse
import asyncio
import base64
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import statistics
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'backend'))
CASES=(('hairstyle','crew_cut','hairstyle.png',3),('hairstyle','bun','hairstyle.png',1),
       ('makeup','natural_makeup','makeup.jpg',3),('nails','classic_red','nails.png',3),
       ('nails','glossy_black','nails.png',1))


def summarize(runs):
    baseline=[r for r in runs if r['mode']=='baseline']
    candidate=[r for r in runs if r['mode']=='candidate']
    old=statistics.median(r['wall_seconds'] for r in baseline)
    new=statistics.median(r['wall_seconds'] for r in candidate)
    stable=len({r['rgb_sha256'] for r in baseline})==1 if len(baseline)>1 else None
    return {'baseline_n':len(baseline),'candidate_n':len(candidate),
        'baseline_median_seconds':old,'candidate_median_seconds':new,
        'baseline_range_seconds':[min(r['wall_seconds'] for r in baseline),max(r['wall_seconds'] for r in baseline)],
        'candidate_range_seconds':[min(r['wall_seconds'] for r in candidate),max(r['wall_seconds'] for r in candidate)],
        'observed_median_saving_percent':100*(old-new)/old,
        'baseline_repeatable':stable,
        'candidate_matches_baseline_pixels':all(r['rgb_sha256']==baseline[0]['rgb_sha256'] for r in candidate),
        'note':'Single observations are coverage only, not a statistically established speed gain.' if len(baseline)==1 else 'Three matched samples; no percentile or generalization claim.'}


async def benchmark(output):
    import torch
    from PIL import Image
    from scripts import unified_gate3_server as server
    from scripts.inference_performance import InferencePerformance
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA GPU required; do not benchmark diffusion on CPU')
    if os.environ.get('AI_INFERENCE_PROFILE')=='1' or os.environ.get('AI_PROMPT_CACHE')=='1':
        raise RuntimeError('Benchmark controls its own profile/cache modes')
    if output.exists():
        raise RuntimeError('Use a new output directory to preserve earlier evidence')
    output.mkdir(parents=True)
    report={'status':'IN_PROGRESS','scope':'worker-only fixed approved inputs; Nails is a single crop',
        'production_service_changed':False,'cases':[],
        'gpu':torch.cuda.get_device_name(0),'torch':torch.__version__,'cuda':torch.version.cuda}
    try:
        runtime=server.UnifiedRuntime()
        start=time.monotonic();runtime.load()
        report['startup_seconds']=time.monotonic()-start
        report['base_revision']=server.gate.REVISION
        report['foundation_load_count']=runtime.foundation_load_count
        owner=runtime.owner
        for feature,style,name,repeats in CASES:
            source=ROOT/'gate1/inputs'/name
            with Image.open(source) as opened:
                image=opened.convert('RGB')
            case={'feature':feature,'style_id':style,'input_sha256':sha256(source.read_bytes()).hexdigest(),
                  'steps':8 if feature=='nails' else 20,'runs':[]}
            report['cases'].append(case)
            adapter=server.selected_adapter(feature,style)
            # Warm adapter/model work and separately sample synchronized subphases.
            owner.performance=InferencePerformance(owner.synchronize,phase_timing=True)
            await owner.generate(adapter,'benchmark-warmup',image=image,style_id=style,inference_steps=case['steps'])
            case['diagnostic_phases']=owner.performance.last
            modes={mode:InferencePerformance(owner.synchronize,cache_enabled=mode=='candidate',phase_timing=False) for mode in ('baseline','candidate')}
            for number in range(repeats):
                # Alternate order to reduce one-direction warmup/order bias.
                for mode in (('baseline','candidate') if number%2==0 else ('candidate','baseline')):
                    owner.performance=modes[mode]
                    torch.cuda.synchronize(0);torch.cuda.reset_peak_memory_stats(0)
                    start=time.monotonic()
                    payload=await owner.generate(adapter,'benchmark-'+mode,image=image,style_id=style,inference_steps=case['steps'])
                    torch.cuda.synchronize(0)
                    elapsed=time.monotonic()-start
                    raw=base64.b64decode(payload['image']['data_url'].split(',',1)[1],validate=True)
                    with Image.open(BytesIO(raw)) as generated:
                        rgb=generated.convert('RGB')
                        rgb_hash=sha256(rgb.tobytes()).hexdigest()
                    filename=f'{feature}-{style}-{number}-{mode}.png'
                    (output/filename).write_bytes(raw)
                    case['runs'].append({'mode':mode,'repeat':number,'wall_seconds':elapsed,
                        'rgb_sha256':rgb_hash,'png_sha256':sha256(raw).hexdigest(),
                        'peak_gpu_allocated_mib':torch.cuda.max_memory_allocated(0)/1024**2,
                        'performance':owner.performance.last,
                        'adapter_sha256':payload['metadata']['adapter_sha256'],
                        'seed':payload['metadata']['seed'],'steps':payload['metadata']['steps'],
                        'guidance':payload['metadata']['guidance']})
                    print('BENCHMARK',feature,style,mode,number+1,round(elapsed,3),'seconds',flush=True)
                    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            case['summary']=summarize(case['runs'])
            print('CASE_RESULT',feature,style,json.dumps(case['summary']),flush=True)
        owner.performance=None
        report['status']='MEASURED_REQUIRES_QUALITY_REVIEW'
        report['limits']=['No Render/browser/full-hand CPU timing in this worker benchmark',
            'No renderer or full-hand mask quality claim; existing geometry/renderer regressions are separate',
            'No automatic enablement; inspect all images and compare first-cold versus reused prompt timings',
            'TRAIΝ-002 Bun and Glossy Black have single paired coverage observations']
    except BaseException as exc:
        report['status']='FAILED'
        report['error_type']=type(exc).__name__
        raise
    finally:
        (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'.tmp/generation-performance')
    args=parser.parse_args()
    asyncio.run(benchmark(args.output.resolve()))

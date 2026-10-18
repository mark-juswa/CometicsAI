"""Real CPU tensors validate work reuse; not a GPU speed/quality claim."""
from types import SimpleNamespace
from pathlib import Path
import sys
import pytest
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.inference_performance import InferencePerformance, configured_performance


class Pipe:
    dtype=torch.float32
    def __init__(self):
        self.encodes=0
        self.text_encoder=SimpleNamespace(dtype=torch.float32)
        self.transformer=SimpleNamespace(forward=lambda x:x+1)
        self.vae=SimpleNamespace(decode=lambda x:x)
    def encode_prompt(self,prompt,device=None,num_images_per_prompt=1,prompt_embeds=None,max_sequence_length=512,text_encoder_out_layers=(9,18,27)):
        self.encodes+=1
        value=torch.arange(12,dtype=self.dtype).reshape(1,3,4)+len(prompt)
        return (value.repeat(num_images_per_prompt,1,1),torch.arange(3).reshape(1,3))
    def prepare_image_latents(self,x):
        return x
    def run(self,prompt='fixed'):
        positive=self.encode_prompt(prompt)
        negative=self.encode_prompt('')
        return self.vae.decode(self.transformer.forward(self.prepare_image_latents(positive[0]+negative[0])))


def scope(perf,pipe,identity=('nails','approved-hash','base')):
    return perf.measure(pipe,identity=identity,allowed_prompts={'fixed',''})


def test_default_serving_has_no_profiler_or_cache():
    assert configured_performance(lambda:None,{}) is None
    cache=configured_performance(lambda:None,{'AI_PROMPT_CACHE':'1'})
    assert cache.cache_enabled and not cache.phase_timing


def test_five_sequential_crops_reuse_both_prompt_encodings_without_changing_outputs():
    pipe=Pipe()
    baseline=[pipe.run().clone() for _ in range(5)]
    assert pipe.encodes==10
    pipe=Pipe()
    perf=InferencePerformance(lambda:None,cache_enabled=True,phase_timing=False)
    for expected in baseline:
        with scope(perf,pipe):
            actual=pipe.run()
        assert torch.equal(actual,expected)
    assert pipe.encodes==2
    assert perf.last['prompt_cache']['hits']==2
    assert perf.cache_bytes <= 64*1024*1024
    assert all(value.device.type=='cpu' for item in perf.cache.values() for value in item[0])
    assert 'encode_prompt' not in vars(pipe)
    assert 'phase_seconds' in perf.last and not perf.last['phase_seconds']


def test_cache_clones_protect_first_result_and_later_hits_from_mutation():
    pipe=Pipe();perf=InferencePerformance(lambda:None,cache_enabled=True)
    with scope(perf,pipe):
        first=pipe.encode_prompt('fixed')
        expected=first[0].clone();first[0].add_(100)
        second=pipe.encode_prompt('fixed');assert torch.equal(second[0],expected)
        second[0].add_(100)
        assert torch.equal(pipe.encode_prompt('fixed')[0],expected)


def test_adapter_hash_dtype_encoder_options_and_encoder_identity_cannot_reuse_stale_values():
    pipe=Pipe();perf=InferencePerformance(lambda:None,cache_enabled=True)
    for identity in [('nails','a','base'),('nails','b','base')]:
        with scope(perf,pipe,identity):pipe.encode_prompt('fixed')
    assert pipe.encodes==2
    with scope(perf,pipe,('nails','b','base')):pipe.encode_prompt('fixed',max_sequence_length=256)
    assert pipe.encodes==3
    pipe.dtype=torch.float64
    with scope(perf,pipe,('nails','b','base')):assert pipe.encode_prompt('fixed')[0].dtype==torch.float64
    assert pipe.encodes==4
    pipe.text_encoder=SimpleNamespace(dtype=torch.float64)
    with scope(perf,pipe,('nails','b','base')):pipe.encode_prompt('fixed')
    assert pipe.encodes==5


def test_non_public_prompts_and_supplied_embeddings_are_never_cached():
    pipe=Pipe();perf=InferencePerformance(lambda:None,cache_enabled=True)
    with scope(perf,pipe):
        pipe.encode_prompt('private-user-text');pipe.encode_prompt('private-user-text')
        pipe.encode_prompt('fixed',prompt_embeds=torch.ones(1));pipe.encode_prompt('fixed',prompt_embeds=torch.ones(1))
    assert pipe.encodes==4 and not perf.cache
    assert perf.last['prompt_cache']['bypasses']==4
    assert 'private-user-text' not in str(perf.last)


def test_eviction_and_oversize_values_keep_cache_bounded():
    pipe=Pipe();perf=InferencePerformance(lambda:None,cache_enabled=True,max_entries=1)
    with scope(perf,pipe):pipe.run()
    assert len(perf.cache)==1
    tiny=InferencePerformance(lambda:None,cache_enabled=True,max_bytes=1)
    with scope(tiny,pipe):pipe.run()
    assert not tiny.cache and tiny.cache_bytes==0


def test_failure_clears_cached_values_and_restores_every_method():
    pipe=Pipe();perf=InferencePerformance(lambda:None,cache_enabled=True)
    original=pipe.encode_prompt
    with pytest.raises(RuntimeError):
        with scope(perf,pipe):
            pipe.run()
            raise RuntimeError('controlled failure')
    assert not perf.cache and perf.last is None and pipe.encode_prompt==original
    assert 'forward' in vars(pipe.transformer)  # pre-existing callable restored exactly
    with scope(perf,pipe):pipe.run()
    assert perf.last['phase_calls']=={'prompt_encoding':2,'image_encoding':1,'denoising':1,'image_decoding':1}


def test_nested_measurement_refused_and_original_owner_scope_remains_usable():
    pipe=Pipe();perf=InferencePerformance(lambda:None)
    with scope(perf,pipe):
        with pytest.raises(RuntimeError,match='Concurrent'):
            with scope(perf,pipe):pass
        pipe.run()
    assert perf.last is not None


def test_initial_gpu_sync_failure_does_not_leave_the_probe_locked():
    pipe=Pipe()
    def fail():raise RuntimeError('controlled device failure')
    perf=InferencePerformance(fail,cache_enabled=True)
    with pytest.raises(RuntimeError):
        with scope(perf,pipe):pipe.run()
    perf.synchronize=lambda:None
    with scope(perf,pipe):pipe.run()
    assert perf.last is not None

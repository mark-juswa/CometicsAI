"""Opt-in phase timing and bounded fixed-prompt reuse; no image/result cache.

Default serving does not install wrappers. A candidate must pass matched GPU
quality/timing review before enabling AI_PROMPT_CACHE in a deployment.
"""
from collections import OrderedDict
from contextlib import contextmanager
from hashlib import sha256
import inspect
import json
import time


class InferencePerformance:
    def __init__(self, synchronize, *, cache_enabled=False, max_entries=4, max_bytes=64*1024*1024, phase_timing=True, clock=time.monotonic):
        if not 1 <= max_entries <= 16 or not 1 <= max_bytes <= 128*1024*1024:
            raise ValueError('Invalid prompt cache bounds')
        self.synchronize, self.clock = synchronize, clock
        self.cache_enabled, self.max_entries, self.max_bytes = cache_enabled, max_entries, max_bytes
        self.cache = OrderedDict()
        self.cache_bytes = 0
        self.phase_timing = phase_timing
        self.last = None
        self._measuring = False

    def clear(self):
        self.cache.clear()
        self.cache_bytes = 0

    @staticmethod
    def _bytes(tensors):
        return sum(value.numel()*value.element_size() for value in tensors)

    def _key(self, signature, args, kwargs, identity, allowed):
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        values = bound.arguments
        prompt = values.get('prompt')
        if values.get('prompt_embeds') is not None or not isinstance(prompt, str) or prompt not in allowed:
            return None
        # Only declared public prompts can be cached; image/user arguments never enter a key.
        if set(values) - {'prompt','device','num_images_per_prompt','prompt_embeds','max_sequence_length','text_encoder_out_layers'}:
            return None
        options = {key:str(value) for key,value in values.items() if key not in ('prompt','prompt_embeds')}
        return (identity,sha256(prompt.encode()).hexdigest(),json.dumps(options,sort_keys=True))

    @contextmanager
    def measure(self, pipe, *, identity, allowed_prompts):
        if self._measuring:
            raise RuntimeError('Concurrent performance scope refused')
        self._measuring = True
        phase_seconds, counts = {}, {}
        stats = {'hits':0,'misses':0,'bypasses':0}
        restore = []
        marker = object()
        self.last = None

        def wrapped(target, name, phase, prompt=False):
            if (not self.phase_timing and not prompt) or not hasattr(target,name):
                return
            original = getattr(target,name)
            previous = vars(target).get(name,marker)
            signature = inspect.signature(original) if prompt else None
            def invoke(*args,**kwargs):
                if self.phase_timing:
                    self.synchronize()
                started = self.clock()
                try:
                    if not prompt or not self.cache_enabled:
                        return original(*args,**kwargs)
                    key = self._key(signature,args,kwargs,(identity,str(getattr(pipe,'dtype',None)),str(getattr(getattr(pipe,'text_encoder',None),'dtype',None)),id(getattr(pipe,'text_encoder',pipe)),str(getattr(pipe,'_execution_device',None))),allowed_prompts)
                    if key is None:
                        stats['bypasses'] += 1
                        return original(*args,**kwargs)
                    if key in self.cache:
                        cpu,devices,size = self.cache.pop(key)
                        self.cache[key] = (cpu,devices,size)
                        stats['hits'] += 1
                        return tuple(value.to(device=device).clone() for value,device in zip(cpu,devices))
                    stats['misses'] += 1
                    value = original(*args,**kwargs)
                    # encode_prompt returns the two tensors (embeddings, text IDs).
                    if not isinstance(value,tuple) or len(value)!=2 or not all(hasattr(v,'detach') for v in value):
                        raise RuntimeError('Unsupported prompt encoder return contract')
                    size = self._bytes(value)
                    if size <= self.max_bytes:
                        cpu = tuple(v.detach().to(device='cpu').clone() for v in value)
                        while self.cache and (len(self.cache)>=self.max_entries or self.cache_bytes+size>self.max_bytes):
                            _,(_,_,removed)=self.cache.popitem(last=False)
                            self.cache_bytes -= removed
                        self.cache[key]=(cpu,tuple(v.device for v in value),size)
                        self.cache_bytes += size
                    return value
                finally:
                    if self.phase_timing:
                        self.synchronize()
                        phase_seconds[phase] = phase_seconds.get(phase,0)+(self.clock()-started)
                        counts[phase] = counts.get(phase,0)+1
            setattr(target,name,invoke)
            restore.append((target,name,previous))

        try:
            self.synchronize()
            started = self.clock()
            wrapped(pipe,'encode_prompt','prompt_encoding',True)
            wrapped(pipe,'prepare_image_latents','image_encoding')
            wrapped(pipe.transformer,'forward','denoising')
            wrapped(pipe.vae,'decode','image_decoding')
            yield
            self.synchronize()
            self.last = {'phase_seconds':{key:round(value,6) for key,value in phase_seconds.items()},
                         'phase_calls':counts,'runtime_seconds':round(self.clock()-started,6),
                         'prompt_cache':{**stats,'enabled':self.cache_enabled,'entries':len(self.cache),'cpu_bytes':self.cache_bytes},
                         'timing_kind':'synchronized_phase_diagnostic' if self.phase_timing else 'whole_runtime_synchronized_no_phase_barriers'}
        except BaseException:
            self.clear()
            raise
        finally:
            for target,name,previous in reversed(restore):
                if previous is marker:
                    delattr(target,name)
                else:
                    setattr(target,name,previous)
            self._measuring=False


def configured_performance(synchronize, env):
    if env.get('AI_INFERENCE_PROFILE')!='1' and env.get('AI_PROMPT_CACHE')!='1':
        return None
    return InferencePerformance(synchronize,cache_enabled=env.get('AI_PROMPT_CACHE')=='1',phase_timing=env.get('AI_INFERENCE_PROFILE')=='1')

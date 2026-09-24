# DATA-002 Base load stall

Status: **root surface localized; output change not yet verified on Kaggle**.

The Supervisor ran `notebooks/data002_generate_kaggle.py --all` against frozen manifest SHA-256 `25a3200c9a79be85ce19f690ba81f564d57d55d86d36e6383b0cacd1188ec5ab` on a Kaggle Tesla T4 with PyTorch `2.10.0+cu128`. The source archive was available. The runner reported `Loading pinned Base for 120 remaining generation jobs`, then remained there for more than 16 minutes. The last visible Transformers progress item was approximately 155/398 weight tensors. There were zero completed generated images. Earlier DATA-001 runs loaded the same pinned FLUX.2 Klein Base revision successfully, so this is not evidence of a model incompatibility.

The Supervisor supplied the tail of `/kaggle/working/data002/base_load_trace.log`. Two consecutive 180-second samples show the same location:

```text
main thread: tqdm/utils.py:196 inner
  -> tqdm/std.py:452 fp_write
  -> tqdm/std.py:459 print_status
  -> tqdm/std.py:1495 display
  -> tqdm/std.py:1347 refresh
  -> transformers/core_model_loading.py:1215 convert_and_load_state_dict_in_model
  -> transformers/modeling_utils.py:4231 _load_pretrained_model
  -> diffusers/pipelines/pipeline_utils.py:1064 from_pretrained
  -> notebooks/data002_generate_kaggle.py:215 main

tqdm monitor thread: tqdm/utils.py:196 inner
  -> tqdm/std.py:452 fp_write
  -> tqdm/std.py:459 print_status
  -> tqdm/std.py:1495 display
  -> tqdm/std.py:1347 refresh
  -> tqdm/_monitor.py:84 run
```

This localizes the pause to progress output during weight materialization. The trace does not establish whether the ultimate cause is notebook output backpressure or an internal tqdm lock cycle. The runner now calls Transformers `logging.disable_progress_bar()` before `from_pretrained`, which is the documented API for suppressing its loading progress display. The runner's own 60-second heartbeat and per-image completion lines remain, as do the pinned model, cache, FP16, CPU offload, and all generation settings. Kaggle must verify this single change before considering further remedies.

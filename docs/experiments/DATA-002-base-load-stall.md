# DATA-002 Base load stall

Status: **not resolved; notebook output backpressure is the current testable hypothesis**.

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

This localized the first pause to progress output during weight materialization. The runner then called Transformers `logging.disable_progress_bar()` before `from_pretrained`, leaving the pinned model, cache, FP16, CPU offload, and all generation settings unchanged.

The Supervisor's next trace file was append-only. Its earlier tqdm frames belong to the previous process. The new process began at `2026-09-24T08:39:28Z`, PID 313. Two consecutive 180-second samples from that process place its main thread at `warnings.py:_showwarnmsg_impl`, called by Diffusers deprecation handling at `pipeline_utils.py:793` during `from_pretrained`. No generated image was reported. Suppressing the Transformers progress bar did not resolve the stall; the blocked point moved to a different stderr writer.

```text
main thread: warnings.py:30 _showwarnmsg_impl
  -> warnings.py:115 _showwarnmsg
  -> diffusers/utils/deprecation_utils.py:98 deprecate
  -> diffusers/utils/deprecation_utils.py:23 _resolve_dtype
  -> diffusers/pipelines/pipeline_utils.py:793 from_pretrained
  -> notebooks/data002_generate_kaggle.py:220 main
```

The shared factor is live child-process output inherited by the Kaggle notebook. This supports, but does not prove, notebook output backpressure. The next single-variable test is to launch the same runner with stdout and stderr redirected to a file. Do not change the model, dtype, dependencies, or generation settings for this test. Inspect the log and generated-image count after a bounded wait. If a fresh trace still shows a stationary stack after output redirection, preserve it and stop rather than repeating the bulk run.

# GPU hosting alternatives for BeautyCore

Research date: 8 November 2026, Asia/Manila. Status: PROPOSED recommendation, public pricing and documentation inspected. No provider account, paid instance, deployment or model validation was started. Listed prices are USD snapshots, not a reserved capacity quote.

Recommend Runpod Pods for the first migration. Keep the existing Render website and Neon database, and move the combined AI facade and shared GPU worker onto one GPU Pod. This most closely preserves the existing long running notebook workflow and application contracts. Modal is a stronger candidate for a later automatic on demand service, but its lifecycle needs more adaptation. Lightning is a credible notebook alternative. Vast is worth comparing for a lower live offer, with more host selection and storage/network diligence.

The ease and fit rankings below are engineering assessments based on the inspected code and provider documentation, not completed migration results.

## Requirements derived from this project

The shared worker uses `black-forest-labs/FLUX.2-klein-base-4B`, revision `a3b4f4849157f664bdbc776fd7453c2783562f4d`, one persistent foundation and one active adapter. All custom Hair, Makeup and Nails adapters can remain on one GPU. Nails also needs its CPU geometry, isolated segmentation and rendering stages. The deployed catalog is 18 Hair, 13 Makeup and 8 Nails styles. Renting three independent GPUs is unnecessary for this current serialized design.

The verified Gate 2 environment is Python 3.12.13, Torch 2.10.0+cu128, CUDA 12.8 and Tesla T4. Diffusers is pinned to commit `c943837899b16cbae2f619b8dd4f7bb6f07dd81a`. GPU memory was about 8.5 GiB at the sampled whole device peak with CPU offload. Host process high water was 22.887 GiB. These are historical bounded observations, not a guaranteed maximum for every image or current combined facade workload. The current combined startup explicitly requires at least 30 GiB host RAM. A cheap GPU alone is insufficient.

For the first migration, provision at least 32 GiB of usable allocated system RAM, preferably a listing with 48 GB or more advertised RAM, and 16 GB or more GPU memory. A 24 GB RTX 3090 or L4 offers headroom but needs new hardware validation. Confirm the container memory limit as well as physical host memory. The current check reads `/proc/meminfo`, which need not describe a container's actual allocation.

The recorded Base snapshot occupies 15,980,131,711 bytes. The two private serving inputs add about 247 MB. A 50 GB persistent model/cache volume is a reasonable initial allocation, not a measured complete installation footprint. Budget separate container space for CUDA libraries, Python environments and temporary files. The full Base is not included in the small input packages.

The actual corrective Makeup application requests took 70.252 to 82.262 seconds, median 80.257 seconds, on the reviewed Kaggle environment. No speed or output equality has been measured on another provider. Keep the existing asynchronous job/status flow and single inference owner.

Local evidence: `docs/experiments/unified-kaggle-gate2-review.json`, `docs/experiments/unified-kaggle-gate2.md`, `docs/experiments/makeup-corrective-application-results-20261106.md`, `scripts/render_kaggle_bootstrap.py`, `scripts/unified_gate3_bootstrap.py`, `backend/app/demo_gateway.py` and `beautycore/lib/ai/adapter-core.ts`.

## Provider comparison

| Provider | Setup fit | Public price snapshot | Project assessment |
| --- | --- | --- | --- |
| Runpod Pods | Browser JupyterLab through supported templates, plus custom containers and persistent volumes | RTX 3090 24 GB: $0.50/h; L4 24 GB: $0.59/h; RTX 4090 24 GB: $0.89/h | Best first migration. Pick sufficient allocated RAM and a compatible storage/location offer. A stock latest PyTorch template does not establish our pinned environment. |
| Lightning Studios | Browser JupyterLab/VS Code and persistent workspace | Current primary page lists T4 from $0.55/h and L4 from $0.79/h, with other configurations higher | Closest managed notebook experience. Verify host RAM, country/account eligibility and exact final configuration. Promotional credits are not recurring free production compute. |
| Vast instances | Notebook/container templates and host search | No fixed trustworthy rate; hosts set live GPU prices, with storage and bandwidth additional | Potentially competitive, but cannot substantiate a cheapest usable offer without a live qualified listing. Avoid interruptible capacity for an active client request. |
| Modal Functions | Python deployment, hosted HTTP applications and automatic scaling | T4 $0.000164/s and L4 $0.000222/s, plus CPU and RAM; Starter lists $30/month compute credits | Useful for low traffic automatic serving after lifecycle work. Not a direct import of the present notebook. Load time and warm idle time are billable. |

Sources: [Runpod rates](https://www.runpod.io/pricing), [Runpod notebook access](https://docs.runpod.io/pods/connect-to-a-pod), [Lightning rates](https://lightning.ai/pricing), [Lightning Studio overview](https://platform.lightning.ai/studio), [Vast pricing model](https://docs.vast.ai/guides/instances/pricing), [Vast quickstart](https://docs.vast.ai/guides/get-started/quickstart), [Modal rates](https://modal.com/pricing), [Modal HTTP functions](https://modal.com/docs/guide/webhooks).

The Lightning root pricing page is used over older indexed subdomains. Those older pages show different T4 rates and promotional hour counts. The root page currently lists up to 30 starting credits and describes four hour restarts for the free Studio. Its extracted page includes multiple machine configurations; the lowest GPU headline is not confirmation of sufficient host RAM or an available regional offer. The Studio overview also states country availability restrictions. No client account eligibility was tested.

Runpod's $0.27/h RTX A5000 headline is not the proposed choice. The displayed configuration has only 25 GB system RAM, below the existing combined startup threshold, despite 24 GB VRAM. This is an example of why selecting by GPU price alone would repeat the compatibility problem.

## Cost examples and storage behavior

Runpod publishes standard network volume storage at $0.07/GB/month below 1 TB. Fifty GB costs $3.50/month if an appropriate Pod/location supports that volume. The alternate attached volume disk is $0.10/GB/month while running and $0.20 while stopped. Container disk is temporary and cleared on stop, so placing the only model cache there causes repeated downloads. These are different products and must not be combined as if both were the same persistent disk. See [storage behavior](https://docs.runpod.io/pods/storage/types) and [billing](https://docs.runpod.io/pods/pricing).

Illustration using the listed $0.50/h Pod and a retained 50 GB standard network volume:

| Usage in a month | GPU compute | With that persistent volume |
| --- | ---: | ---: |
| 10 GPU hours | $5.00 | $8.50 |
| 40 GPU hours, for example 2 hours on 20 days | $20.00 | $23.50 |
| 730 GPU hours, continuously allocated | $365.00 | $368.50 |

These calculations exclude extra container disk, tax, payment conversion, Render/Neon costs, Gemini and any final offer differences. GPU hours include model load, waiting and every hour the instance runs, not just completed images. Attached stopped volume storage can raise the 40 hour scenario closer to $30 before other costs. A practical initial demonstration budget is $25 to $35 for 40 GPU hours plus storage, conditional on obtaining a suitable $0.50/h configuration. Capacity and restart availability are not reserved by these calculations.

Modal's listed base rates imply approximately $0.8933/h for a T4, one CPU core and 32 GiB RAM while allocated; the corresponding L4 example is $1.1021/h. These are arithmetic illustrations, not equivalent performance benchmarks. Model load and configured idle retention add cost. Thirty dollars of listed monthly Starter compute credit can offset eligible usage but does not make an always warm instance free. Region and nonpreemptible configuration can increase rates. The pricing page currently describes a volume allowance as well; verify the chosen plan before projecting storage charges.

Vast storage continues charging while an instance is stopped; local volumes are tied to their physical host. Destroying an instance can delete its container data. See [Vast storage](https://docs.vast.ai/guides/instances/storage/types). A low GPU quote must be compared with the complete storage/bandwidth bill and the host's RAM/network/reliability, not treated as the full price.

## Why not simply use a free Space or import our notebook elsewhere

Hugging Face's T4 small is $0.40/h but has only 15 GB system RAM. T4 medium is $0.60/h with 30 GB advertised RAM, which must not be assumed to satisfy our 30 GiB check. An A10G large lists 46 GB system RAM at $1.50/h. Thus its inexpensive headline does not establish a drop in fit for our current combined CPU offload runtime. Paid Spaces support configurable sleeping, but that still needs our state/readiness behavior addressed. See [hardware and billing](https://huggingface.co/docs/hub/spaces-gpus).

The present notebook contains `/kaggle/input` and `/kaggle/working` assumptions, `kaggle_secrets`, the exact T4 host check and a fresh work directory policy. The GPU bootstrap explicitly puts Hugging Face cache in `/tmp/gate3-hf-cache`. Those are deployment assumptions, not a portable template. On another provider we need explicit input/work/cache paths, environment based secrets, a pinned runtime profile and persistent cache placement. Keep the exact model, caption and artifact hashes. Do not delete guards or change the expected GPU name without validating the new profile.

Render's current remote URL validator accepts only HTTPS `*.trycloudflare.com` roots. A native Runpod proxy, Lightning or Modal URL will be rejected today. We can reuse the current tunnel for a bounded migration proof, or add narrowly scoped endpoint support and verify it with the provider's authenticated facade. Do not make the URL policy accept arbitrary destinations. [Runpod exposes HTTP services through its proxy](https://docs.runpod.io/pods/configuration/expose-ports), but this is not automatically compatible with the existing application allowlist.

The existing API process retains photos, consultation state and generation jobs in memory, and the website uses heartbeat leases. Scaling a serverless process to zero loses that memory. Independent containers do not automatically share it. Modal or Runpod Serverless therefore needs deliberate state ownership, readiness/lease and request routing work before claiming automatic production readiness. Starting with one long running Pod avoids that immediate redesign. Modal can host web functions and persistent model volumes, but model storage alone does not persist Python job objects. See [Modal volumes](https://modal.com/docs/guide/volumes).

## Proposed bounded next step

Prepare one Runpod deployment template with the reviewed Python/Torch/CUDA/Diffusers versions, the existing separated CPU vision environments, a persistent model cache and a single start command. Keep the private packages and all four adapter hashes unchanged. Keep the existing Render website, booking, save, auth and generation APIs.

The intended operator flow after one time preparation is: open the template, choose the validated GPU/RAM profile, attach persistent storage, configure the same three secrets privately, start, and wait for the existing readiness/website connection acknowledgement. Stop compute after a scheduled demo; retained storage remains billable. This ease is a target for the template, not a ready deployed feature.

Before switching the client, validate the pinned environment, real Hair and Makeup adapters and complete Nails path, serialization and restoration across features, all catalog coverage, one fresh portrait and a full hand, registration and a stop/start rehearsal. Use existing accepted outputs to assess identity, complexion and style fidelity, allowing for documented cross GPU numerical differences without lowering visual criteria. No retraining is intrinsically required for changing providers, but successful weight loading alone is not enough evidence.

No major architecture choice has been approved by this research. Do not start paid resources or modify the existing deployment based on this report alone. A runtime migration is a separate implementation milestone, and a later serverless conversion is another. Kaggle and all existing artifacts remain fallback.

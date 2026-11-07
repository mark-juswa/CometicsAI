# Replacement Makeup data investigation — 25 October 2026

**Research DONE; dataset acceptance NEEDS VERIFICATION; corrective model IN PROGRESS.**
Supervisor explicitly chose investigation of replacement datasets. Primary project pages, creator repositories and dataset cards below were inspected. Counts describe publisher claims, not downloaded/independently counted images. No replacement images or weights were acquired; no access request was sent.

## Recommendation

Do not retrain on the unchanged 60 targets. The [separate corrective audit](../experiments/makeup-corrective-review-20261025.md) found zero unchanged targets passing its stricter qualitative screen. More pictures are useful only if their targets teach the desired behavior.

**No investigated source is currently verified as ready for this correction trial.** This means that pairing, image quality and applicable permissions have not all passed our intake gates; it does not mean that no suitable dataset exists.

Priority for further investigation:

1. Request clarification and a reviewable subset from **BMS** and the **2026 curated dataset** authors. These are paired-data leads, not accepted replacements. Ask for original unretouched sources, exact pair correspondence, relevant permissions, and diverse complexion examples before a large download.
2. Use **YMU** only as a possible supplementary real-photo evaluation source after permissions/access are established. Its documented subject range cannot establish preservation on the darker complexions central to this defect.
3. Do not turn unpaired BeautyFace, MT, LADN or MF2K references into same-person targets by matching file positions. Do not generate automatic pseudo-targets with another model and call them corrected ground truth.
4. If those access/quality checks fail, a permissioned controlled same-person capture remains a separate practical option. It has not been selected by the user or started here.

A dataset-only fix is not guaranteed: the previous foundation-only diagnostic also over-edited faces. One bounded corrected-data trial is justified only after suitable targets exist. A different model or transfer architecture would require a separate proposal addressing the prior failed methods, runtime costs and serving compatibility.

## Source comparison

| Source | Verified pairing / access facts | Permission evidence and unresolved points | Suitability for this project |
|---|---|---|---|
| [FFHQ-Makeup, current source](https://huggingface.co/datasets/cyberagent/FFHQ-Makeup) | Creator card describes 18,000 source identities, five synthetic targets each, 512-square JPEGs. This is the source of our existing 60 pairs. It also acknowledges unrelated-region artifacts. | Card specifies CC BY-NC-SA 4.0 and retention of original FFHQ image metadata. | Not a replacement by name alone. Our 60-target screen fails; other identities remain unreviewed. Do not infer all 18,000 fail. |
| [BeautyBank / BMS](https://github.com/CyberAgentAILab/BeautyBank), [officially linked dataset card](https://huggingface.co/datasets/lulululululululululu/Bare-Makeup-Synthesis-Dataset) | A different dataset from FFHQ-Makeup. Card lists 319,516 synthetic makeup PNGs at 512 square, corresponding FFHQ originals by filename, and 125 GB in split archives. Bare photos are not included. | Card states CC BY 4.0; original FFHQ photo rights still need to be checked. Repo MIT license concerns code. Do not interpret either as clearing all underlying photos or deployed salon use. | Conditional paired lead. Need actual correspondence, sample quality and rights clarification before downloading the full archive. Synthetic construction can repeat the current problem; no images independently reviewed here. |
| [YouTube Makeup Dataset — creator lab](https://iprobe.cse.msu.edu/dataset_detail.php??title=YouTube_Makeup_Dataset_(YMU)&id=3) | Real tutorial before/after images. Lab describes 151 white female subjects, at least two before/two after, some six-image subjects. Pose, expression, foundation and even hairstyle change. Lab's outbound download page could not be retrieved in this investigation. | No explicit image-use grant verified on the accessible lab page. Original internet/tutorial origin does not establish consent or unrestricted reuse. Confirm terms with creators. | Supplementary evaluation/intake candidate; not aligned pixel targets and not sufficient complexion coverage for the current failure. Must inspect individual pairs. |
| [BeautyFace / BeautyREC](https://li-chongyi.github.io/BeautyREC_files/), [code and dataset instructions](https://github.com/learningyan/BeautyREC) | 3,000 faces with parsing maps. Training uses separate makeup/non-makeup image lists; same-person before/after targets are not established. | [Repository license](https://raw.githubusercontent.com/learningyan/BeautyREC/main/License) permits noncommercial software use and directs commercial users to contributors. A software license is not a verified license for every internet photo. | Potential reference/mask source after rights checks; not a drop-in replacement for our supervised paired edit training. Adopting BeautyREC itself is a separate architecture decision. |
| [Curated supervised Makeup dataset paper, 2026](https://arxiv.org/html/2602.00729v1), [authors' examples page](https://makeup-adapter.github.io/) | Paper describes a 50K curated paired collection with synthetic/filtered data and a different transfer framework. Linked project page exposes two example PDFs, not a verified dataset download. | No dataset license or access grant verified. The paper's CC BY notice does not grant rights to its training images. | Relevant access-request lead. Reported skin-preservation claims are not BeautyCore validation. Cannot train from a paper's result figures. |
| [MF2K / ART, 2026](https://github.com/csbowei/ART) | Creator describes 8,573 portraits, makeup-intensity labels and source/reference evaluation pairs. Release is metadata plus reconstruction scripts because original-image redistribution is constrained. Not established as matching bare/after ground truth for the same person. | Metadata includes original URL/license fields. Check each original and training/redistribution rights; repository/model terms alone are insufficient. | Useful reference/evaluation lead, not paired correction targets. ART uses FLUX.1-Kontext, whereas our serving foundation is FLUX.2 Klein; its LoRAs cannot be dropped into the current worker. No architecture change selected. |
| [PairedCycleGAN implementation](https://github.com/zeligism/PairedCycleGAN) | Author describes roughly 1,000 same-person pairs and a web-search/Pinterest download-and-split pipeline. Accessible instructions do not establish a vetted, licensed paired release. | Image permissions and subject consent not verified. Code availability does not establish photo reuse rights. | Do not run the scraper or count the stated pairs as available approved data. |
| [Facial Region-Aware Makeup, 2026](https://github.com/zaczgao/Facial_Region-Aware_Makeup) | Creator describes synthesis of annotated/edit pairs from FFHQ using external editing technology, rather than a verified controlled real-photo replacement release. | Repository states CC BY-NC-SA 4.0; original FFHQ and upstream terms still apply. | Not a simple data replacement. Running its synthesis/training is a new experimental pipeline and could introduce different artifacts; not selected. |

### Original FFHQ rights matter

[NVIDIA's original FFHQ documentation](https://github.com/NVlabs/ffhq-dataset#licenses) distinguishes dataset distribution terms from individual photo credits/licenses. Preserve the photographer, source URL and license metadata of each included photo. A public dataset URL or public Kaggle copy does not establish that all images or resulting artifacts can be used for an operational salon service. Intended capstone research and later client operation must be stated when asking the provider about permissions. These are source-verification gaps, not a legal determination about the current system.

## Minimum intake gates before a new GPU run

Use the [empty intake sheet](../../data/makeup/MAKEUP-CORRECTION-001/replacement-intake.csv). No row is a training pair until all gates pass.

1. **Provenance:** provider URL, exact release/revision, source and target original IDs, per-file hashes, author/license/permission evidence. Clarify whether training, client operation, and sharing a notebook/dataset are permitted; do not silently assume one includes the others.
2. **Pairing:** verified same person; comparable pose, expression, framing and lighting. Alignment may align geometry but cannot invent missing correspondence or undo skin retouching. Exclude ambiguous pairs.
3. **Appearance:** target preserves complexion/undertone and plausible texture outside requested cosmetics; no identity, smile/teeth, hair, clothing or background changes. Intended foundation should match the source, not replace the person's complexion.
4. **Cosmetics:** visible, localized requested changes, with captions describing what is actually present. Natural, Soft Glam and Red Lip are initial evaluation directions, not fabricated classes assigned to arbitrary variant numbers.
5. **Coverage and split:** record actual subject counts and cosmetic coverage. Split by person, deduplicate against existing sources and reserve new people for final acceptance. Do not infer ethnicity or measured skin tone from filenames. The two repeatedly tested people are development controls, not an untouched test set.
6. **Approval:** Codex can screen and report; salon/human visual acceptance must be recorded explicitly. No automatic ACCEPT flags. Publish actual usable counts before choosing batch size, training steps or a new model filename.

Do not request another full Kaggle installation while data is unresolved. Do not weaken the original finalized-dataset packaging guards. A later corrected dataset requires its own reviewed manifest/version and bounded training proposal.

## Draft provider inquiry — not sent

Suggested subject: **Paired Makeup data access and permissions for a capstone correction study**

We are developing BeautyCore, a capstone virtual Makeup preview system. Our current paired synthetic training targets visibly alter the source complexion and facial texture. We are seeking a small, representative sample of same-person before/after Makeup pairs that preserves identity, complexion and natural texture.

Could you confirm:
- Whether the paired files, correspondence metadata and a sample are available, and how to obtain a specific release.
- Whether sources and targets are real captures or generated/retouched images, and what quality filtering was used.
- Whether the sample includes varied complexions and natural/light Makeup as well as visible lip/eye cosmetics.
- Which terms apply to original photos, training a derivative adapter, demonstration, subsequent salon website operation, and sharing datasets or notebook outputs.
- Required attribution, redistribution restrictions and any consent/usage limitations.

We will not treat permission to read the paper or download code as permission to reuse its image data.

Send only to the provider's verified official contact channel after the project owner authorizes the message. No message or agreement has been submitted by this investigation.


## BMS sample-access follow-up, 25 October 2026

Supervisor authorizes proceeding. Public BMS metadata and exact partial downloads were checked at revision 47f245b2d1181eab71f76ef0b829d94fd4edf760. The host honored a 128-byte tail range and 64 KiB index probe. Publisher labels include theatrical styles and pale-foundation instructions; labels are not proof of actual image quality. Full central-directory acquisition timed out; a smaller-range retry and final DNS check failed. No image samples were obtained, matched or approved. No full dataset archive was downloaded.

The BMS first author's published email and a concrete [access request](makeup-data-access-request-20261025.md) are now available. No message was sent; this session has no connected email sender. The newer curated project's page still provides examples rather than a verified paired-data release/contact. [Exact intake receipt](../experiments/makeup-replacement-intake-20261025.json). Continue sample acquisition when connectivity returns and/or after the owner obtains provider access; do not claim replacement data or a trained fix.

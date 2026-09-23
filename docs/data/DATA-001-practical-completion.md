# DATA-001 practical V1 completion handoff

The Supervisor's received archive passed a read-only audit: 30 selected originals, 30 generated counterparts, 30 matching generation sidecars, RGB 512×512 image decoding, source/output hashes, and the approved eight-train/two-validation identities per class. No final pairs exist yet. The practical Dataset V1 review standard accepts minor hair-color, lighting, clothing-detail, or accessory drift. Only a wrong hairstyle, major identity drift, severe artifact, or major scene/pose change warrants a retry.

The contact sheet suggests 28 attempt-1 outputs are usable under that standard. `LayeredHair_4` and `LayeredHair_9` show substantial facial/scene reconstruction and are proposed for the one allowed seed-only retry. This is a review recommendation, not an automatic acceptance. The Supervisor must inspect the full-resolution results and choose the statuses before running the decision cell.

Run the following in the existing Kaggle GPU session, where `/kaggle/working/data001` and `/kaggle/working/CometicsAI` remain available. Pull the updated repository first:

```python
from pathlib import Path
import json, subprocess, sys
repo = Path("/kaggle/working/CometicsAI")
out = Path("/kaggle/working/data001")
subprocess.run(["git", "-C", str(repo), "pull", "--ff-only"], check=True)
assert len(list((out / "generated").glob("*.png"))) == 30
assert len(list((out / "generated").glob("*.json"))) == 30
```

After personally confirming the 28 practical accepts and the two retry decisions, record them explicitly. Stop and edit any proposed decision you disagree with before executing:

```python
reviews_path = out / "reviews.json"
reviews = json.loads(reviews_path.read_text(encoding="utf-8"))
assert len(reviews) == 30 and all(r["status"] == "PENDING" for r in reviews.values())
retry_ids = {"LayeredHair_4", "LayeredHair_9"}
for sample_id, review in reviews.items():
    review["attempt"] = 1
    if sample_id in retry_ids:
        review["status"] = "REGENERATE"
        review["notes"] = "Practical V1 review: major identity or scene reconstruction in attempt 1; one seed-only retry requested."
    else:
        review["status"] = "ACCEPT"
        review["notes"] = "Practical V1 review: requested hairstyle clear, identity recognizable, no major artifact or scene/pose change."
assert sum(r["status"] == "ACCEPT" for r in reviews.values()) == 28
reviews_path.write_text(json.dumps(reviews, indent=2) + "\n", encoding="utf-8")
```

Run exactly one retry per flagged identity. Redirect output to a file because the current Kaggle notebook stalled while writing model-import logs to its live output. Each retry uses the existing global edit method, same model/prompt/settings, and changes only seed 1977 to 1978. Preserve both attempt-1 outputs.

```python
for sample_id, source_name in (("LayeredHair_4", "LayeredHair/4.jpg"),
                               ("LayeredHair_9", "LayeredHair/9.jpg")):
    log_path = out / f"retry_{sample_id}.log"
    with log_path.open("w", encoding="utf-8") as log:
        result = subprocess.run(
            [sys.executable, "-u", str(repo / "notebooks/data001_generate_kaggle.py"),
             "--retry", source_name, "--reviews", str(reviews_path)],
            stdout=log, stderr=subprocess.STDOUT,
        )
    print(sample_id, "exit code:", result.returncode, "log:", log_path)
    if result.returncode != 0:
        print(log_path.read_text(errors="replace")[-4000:])
        raise RuntimeError(f"STOP: retry failed for {sample_id}")
```

Inspect `generated/LayeredHair_4_r2.png` and `generated/LayeredHair_9_r2.png` beside their originals at full size. If either remains unacceptable, leave its review as REGENERATE and stop; the fixed 30-identity dataset cannot be finalized without an accepted counterpart. If both pass, record the actual accepted attempts:

```python
reviews = json.loads(reviews_path.read_text(encoding="utf-8"))
for sample_id in ("LayeredHair_4", "LayeredHair_9"):
    assert (out / "generated" / f"{sample_id}_r2.png").is_file()
    assert (out / "generated" / f"{sample_id}_r2.json").is_file()
    reviews[sample_id] = {
        "status": "ACCEPT", "attempt": 2,
        "notes": "Supervisor reviewed attempt 2 at full size: target hairstyle clear, identity recognizable, no major artifact or scene/pose change."
    }
assert len(reviews) == 30 and all(r["status"] == "ACCEPT" and r["notes"] for r in reviews.values())
reviews_path.write_text(json.dumps(reviews, indent=2) + "\n", encoding="utf-8")
```

Finalize and inspect the calculated QA report. The finalizer refuses missing reviews, mismatched metadata/hashes, corrupt images, duplicates, split leakage, broken captions/pairing, and wrong counts:

```python
import shutil
final = out / "final"
subprocess.run(
    [sys.executable, str(repo / "scripts/data001_finalize.py"),
     "--generation-format", "v1", "--generation-dir", str(out),
     "--reviews", str(reviews_path), "--output", str(final)],
    check=True,
)
qa = json.loads((final / "reports" / "qa.json").read_text(encoding="utf-8"))
pairs = json.loads((final / "manifests" / "pairs.json").read_text(encoding="utf-8"))
assert qa["identity_groups"] == {"train": 24, "val": 6}
assert qa["directional_pairs"] == 60 and len(pairs) == 60
assert sum(p["split"] == "train" for p in pairs) == 48
assert sum(p["split"] == "val" for p in pairs) == 12
assert qa["split_leakage"] == "NONE"
assert qa["caption_reference_target_alignment"] == "PASS"
assert qa["image_open_rgb_dimensions"] == "PASS"
print("DATA-001 final QA:", qa)
print("Final archive:", shutil.make_archive(
    "/kaggle/working/data001_final", "zip", root_dir=str(final), base_dir="."))
```

Preserve the review manifest, both retry logs/results/sidecars, final archive, QA report, manifests, and both final contact sheets. TRAIN-001 may start only after the final assertions pass and the Supervisor has viewed the final sheets.

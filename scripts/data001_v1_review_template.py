"""Create a 30-key PENDING review manifest from completed V1 generation outputs.

This never marks an image ACCEPT; the Supervisor edits every decision and note.
"""

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELECTION = json.loads((ROOT / "docs/data/DATA-001-selection.json").read_text(encoding="utf-8"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--generation-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise RuntimeError(f"STOP: review manifest already exists: {args.output}")
    reviews = {}
    for style, config in SELECTION["styles"].items():
        for split in ("train", "val"):
            for filename in config[split]:
                sample = f"{style}_{Path(filename).stem}"
                source = args.generation_dir / "original" / f"{sample}.png"
                result = args.generation_dir / "generated" / f"{sample}.png"
                sidecar = result.with_suffix(".json")
                if not source.is_file() or not result.is_file() or not sidecar.is_file():
                    raise RuntimeError(f"STOP: incomplete V1 generation evidence for {sample}")
                meta = json.loads(sidecar.read_text(encoding="utf-8"))
                if (meta.get("sample_id") != sample or meta.get("split") != split
                        or meta.get("source_class") != style or meta.get("requested_class") != config["alternate_style"]
                        or meta.get("attempt") != 1
                        or meta.get("source_sha256") != hashlib.sha256(source.read_bytes()).hexdigest()
                        or meta.get("output_sha256") != hashlib.sha256(result.read_bytes()).hexdigest()):
                    raise RuntimeError(f"STOP: V1 metadata/hash mismatch for {sample}")
                reviews[sample] = {"status": "PENDING", "attempt": 1, "notes": ""}
    if len(reviews) != 30:
        raise RuntimeError("STOP: expected 30 selected identities")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(reviews, indent=2) + "\n", encoding="utf-8")
    print(f"Created {args.output} with 30 PENDING decisions; inspect images and edit each entry")


if __name__ == "__main__":
    main()

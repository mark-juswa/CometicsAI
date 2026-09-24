"""Create/check explicit human review decisions for generated DATA-002 images.

This never marks a generated counterpart ACCEPT automatically.
"""

import argparse
from collections import Counter
import json
from pathlib import Path

from paired_dataset import load_manifest


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docs/data/DATA-002-manifest.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("init", "summary"))
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--reviews", type=Path, required=True)
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    ids = [sample["sample_id"] for sample in manifest["samples"]]
    if args.mode == "init":
        if args.reviews.exists():
            raise RuntimeError("Review file already exists; refusing to replace human decisions")
        args.reviews.parent.mkdir(parents=True, exist_ok=True)
        args.reviews.write_text(json.dumps({key: {"status": "PENDING", "attempt": 1,
                                                   "notes": ""} for key in ids}, indent=2) + "\n",
                                encoding="utf-8")
        print(f"Created {len(ids)} PENDING entries: {args.reviews}")
        return
    reviews = json.loads(args.reviews.read_text(encoding="utf-8"))
    if set(reviews) != set(ids):
        raise ValueError("Review IDs do not exactly match the frozen selection manifest")
    allowed = {"PENDING", "ACCEPT", "REGENERATE", "REJECT"}
    for key, review in reviews.items():
        if (not isinstance(review, dict) or review.get("status") not in allowed
                or review.get("attempt") not in (1, 2)):
            raise ValueError(f"Invalid decision for {key}")
        if review["status"] != "PENDING" and not str(review.get("notes", "")).strip():
            raise ValueError(f"A human review note is required for {key}")
        if review["status"] == "REGENERATE" and review["attempt"] != 1:
            raise ValueError(f"Only one controlled retry is allowed for {key}")
    counts = dict(sorted(Counter(value["status"] for value in reviews.values()).items()))
    print(json.dumps({"counts": counts,
                      "retry_ids": [key for key, value in reviews.items()
                                    if value["status"] == "REGENERATE"],
                      "ready_for_finalization": counts.get("ACCEPT", 0) == len(ids)}, indent=2))


if __name__ == "__main__":
    main()

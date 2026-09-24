"""Small structural fixture for DATA-002 automated acceptance, no model or GPU."""

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from paired_dataset import audit_generations, finalize, instruction, load_manifest, sha256  # noqa: E402


class Data002FastPathTest(unittest.TestCase):
    def test_audit_then_automated_finalization_records_no_human_review(self):
        frozen = load_manifest(ROOT / "docs/data/DATA-002-manifest.json")
        train = next(s for s in frozen["samples"] if s["split"] == "train")
        val = next(s for s in frozen["samples"] if s["split"] == "val")
        manifest = {**frozen, "samples": [train, val]}
        with TemporaryDirectory() as directory:
            root = Path(directory)
            generated = root / "generated"
            generated.mkdir()
            (root / "manifest.sha256").write_text("fixture-hash\n", encoding="utf-8")
            for index, sample in enumerate(manifest["samples"]):
                folder = generated / sample["sample_id"]
                folder.mkdir()
                original = folder / "original.png"
                output = folder / "generated.png"
                Image.new("RGB", (512, 512), (30 + index * 50, 40, 50)).save(original)
                Image.new("RGB", (512, 512), (60 + index * 50, 70, 80)).save(output)
                metadata = {
                    "sample_id": sample["sample_id"], "identity_group_id": sample["identity_group_id"],
                    "source_path": sample["source_path"], "source_member": sample["source_member"],
                    "source_member_sha256": sample["source_sha256"],
                    "source_style": sample["source_style"], "target_style": sample["target_style"],
                    "split": sample["split"], "attempt": 1, "method": manifest["generation"]["method"],
                    "prompt": instruction(manifest["styles"], sample["target_style"]),
                    "seed": manifest["generation"]["seed"], "steps": manifest["generation"]["steps"],
                    "guidance": manifest["generation"]["guidance"], "width": 512, "height": 512,
                    "source_revision": manifest["source_revision"],
                    "base_model_id": manifest["base_model_id"],
                    "base_model_revision": manifest["base_model_revision"],
                    "original_sha256": sha256(original), "generated_sha256": sha256(output),
                    "runtime_seconds": 1.0, "generated_utc": "2026-09-24T00:00:00Z",
                }
                (folder / "generated.json").write_text(json.dumps(metadata), encoding="utf-8")
            audit = audit_generations(manifest, generated, "fixture-hash")
            self.assertEqual(audit["valid_generation_count"], 2)
            self.assertEqual(audit["actual_pair_counts"], {"train": 2, "val": 2})
            self.assertFalse(audit["issues"])
            with self.assertRaisesRegex(ValueError, "Human-reviewed"):
                finalize(manifest, generated, None, root / "human")
            qa = finalize(manifest, generated, None, root / "final", "automated_unreviewed", "fixture-hash")
            self.assertEqual(qa["review_mode"], "automated_unreviewed")
            self.assertEqual(qa["explicit_accepts"], 0)
            self.assertEqual(qa["automated_accepts"], 2)
            self.assertEqual(qa["pair_counts"], {"train": 2, "val": 2})
            self.assertEqual(len(list((root / "final" / "train" / "target").glob("*.txt"))), 2)
            (generated / val["sample_id"] / "generated.png").write_bytes(b"broken")
            bad = audit_generations(manifest, generated, "fixture-hash")
            self.assertEqual(bad["valid_generation_count"], 1)
            self.assertIn(val["sample_id"], [item["sample_id"] for item in bad["issues"]])


if __name__ == "__main__":
    unittest.main()

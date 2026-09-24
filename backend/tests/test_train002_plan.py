"""Check TRAIN-002 stays isolated and packages a step-verified adapter."""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "notebooks"))
from train002_kaggle import config_text, package_adapter, resume_status  # noqa: E402


class Train002PlanTest(unittest.TestCase):
    def test_config_and_package_isolate_train002(self):
        import torch
        from safetensors.torch import save_file

        with TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / "data002_final"
            out = root / "train002_500"
            out.mkdir()
            config = config_text(dataset, out)
            self.assertIn('name: "train002_500step"', config)
            self.assertIn('dtype: "bf16"', config)
            self.assertIn('noise_scheduler: "flowmatch"', config)
            self.assertIn("save_every: 250", config)
            self.assertIn("steps: 500", config)
            self.assertNotIn("train001_250", config)
            (out / "train_config.yaml").write_text(config, encoding="utf-8")
            folder = out / "checkpoints" / "train002_500step"
            folder.mkdir(parents=True)
            checkpoint = folder / "train002_500step.safetensors"
            save_file({"lora_test.weight": torch.ones(2)}, str(checkpoint),
                      metadata={"training_info": '{"step": 500}'})
            evidence = {"pairs_sha256": "pair-hash", "qa_sha256": "qa-hash",
                        "style_ids": ["curtain_hair", "perm_curls"],
                        "identity_counts": {"train": 2, "val": 1},
                        "pair_counts": {"train": 4, "val": 2},
                        "target_distribution": {"train/curtain_hair": 2}}
            metadata = package_adapter(out, evidence, {"success": True, "highest_loss_step": 500},
                                       {"ai_toolkit_commit": "pinned-toolkit"})
            self.assertEqual(metadata["experiment"], "TRAIN-002")
            self.assertEqual(metadata["review_mode"], "automated_unreviewed")
            self.assertTrue((out / "adapter" / "adapter.safetensors").is_file())
            self.assertEqual(resume_status(out)["checkpoints"][0]["step"], 500)


if __name__ == "__main__":
    unittest.main()

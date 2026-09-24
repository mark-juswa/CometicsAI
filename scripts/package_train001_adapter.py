"""Make a small, verifiable Kaggle Dataset upload from the TRAIN-001 backup."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
from zipfile import ZipFile


CHECKPOINT = "train001_250/checkpoints/train001_250step/train001_250step.safetensors"
SUMMARY = "train001_250/training_summary.json"
RUNTIME = "train001_250/runtime.json"
MODEL = "black-forest-labs/FLUX.2-klein-base-4B"
STYLES = ["crew_cut", "bob_hair", "layered_hair"]


def verify_safetensors(data: bytes) -> None:
    if len(data) < 16:
        raise ValueError("Checkpoint is too small to be safetensors")
    header_length = struct.unpack("<Q", data[:8])[0]
    if not 0 < header_length < 8 * 1024 * 1024:
        raise ValueError("Invalid safetensors header length")
    header = json.loads(data[8:8 + header_length])
    if not isinstance(header, dict) or not any("lora" in key.lower() for key in header):
        raise ValueError("Checkpoint contains no recognizable LoRA tensors")


def package(archive: Path, output: Path) -> dict:
    with ZipFile(archive) as source:
        if source.testzip() is not None:
            raise ValueError("Training archive failed ZIP integrity check")
        summary = json.loads(source.read(SUMMARY))
        runtime = json.loads(source.read(RUNTIME))
        if not (summary.get("success") is True and summary.get("highest_loss_step") == 250
                and summary.get("exit_code") == 0):
            raise ValueError("TRAIN-001 backup does not prove a successful 250-step run")
        if runtime.get("base_model_revision") is None:
            raise ValueError("Base model revision is absent from TRAIN-001 backup")
        data = source.read(CHECKPOINT)
    verify_safetensors(data)
    digest = hashlib.sha256(data).hexdigest()
    metadata = {
        "schema_version": 1,
        "artifact_type": "project_trained_lora",
        "experiment": "TRAIN-001",
        "training_steps": 250,
        "base_model_id": MODEL,
        "base_model_revision": runtime["base_model_revision"],
        "supported_style_ids": STYLES,
        "checkpoint_file": "adapter.safetensors",
        "checkpoint_bytes": len(data),
        "checkpoint_sha256": digest,
        "source_archive": archive.name,
        "inference": {"width": 512, "height": 512, "steps": 20, "guidance": 4.0, "seed": 1977},
    }
    output.mkdir(parents=True, exist_ok=True)
    checkpoint = output / "adapter.safetensors"
    metadata_path = output / "metadata.json"
    if checkpoint.exists() or metadata_path.exists():
        if not (checkpoint.is_file() and metadata_path.is_file()
                and hashlib.sha256(checkpoint.read_bytes()).hexdigest() == digest
                and json.loads(metadata_path.read_text(encoding="utf-8")) == metadata):
            raise ValueError("Existing adapter bundle differs; choose a new output directory")
    else:
        checkpoint.write_bytes(data)
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True, help="TRAIN-001 archive downloaded from Kaggle")
    parser.add_argument("--output", type=Path, default=Path("artifacts/train001_adapter_bundle"))
    args = parser.parse_args()
    metadata = package(args.archive, args.output)
    print(json.dumps({"bundle_directory": str(args.output.resolve()), **metadata}, indent=2))


if __name__ == "__main__":
    main()

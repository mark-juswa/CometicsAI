"""Prepare anatomy for all frozen source identities using existing CPU assets."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.makeup_corrective_data import read, write, owned, digest
from scripts.prepare_makeup_teacher import analyze_images


def prepare(workspace, output, *, reuse_anatomy=None):
    import numpy as np
    from PIL import Image
    workspace, output = Path(workspace).resolve(), Path(output).resolve()
    if output.exists() or not output.is_relative_to(ROOT):
        raise ValueError("Use a fresh project anatomy directory")
    old = read(ROOT / "artifacts/makeup-refinement-20261105/catalog-review/plan.json")
    selection = read(workspace / "manifests/selection.json")
    cached = read(reuse_anatomy) if reuse_anatomy else old
    if cached["parser"] != old["parser"]:
        raise ValueError("Cached anatomy parser differs")
    previous = {s["id"]: s for s in cached["sources"]}
    for identity, source in previous.items():
        for key, hash_key in (("labels", "labels_sha256"), ("points478", "points478_sha256")):
            if digest(ROOT / source[key]) != source[hash_key]:
                raise ValueError("Cached source anatomy differs")
    pending = [s for s in selection["sources"] if s["identity_id"] not in previous]
    images = []
    for source in pending:
        path = owned(workspace, source["path"])
        if digest(path) != source["sha256"]:
            raise ValueError("Frozen original differs")
        images.append(np.array(Image.open(path).convert("RGB")))
    analyzed = analyze_images(images, old, allow_small_secondary=True) if images else []
    output.mkdir(parents=True)
    extra = {}
    for source, (labels, points) in zip(pending, analyzed):
        identity = source["identity_id"]
        labels_path = output / (identity + "-labels.png")
        points_path = output / (identity + "-points.json")
        Image.fromarray(labels).save(labels_path)
        write(points_path, {"points": points.tolist()})
        extra[identity] = {"labels": labels_path.relative_to(ROOT).as_posix(), "labels_sha256": digest(labels_path),
            "points478": points_path.relative_to(ROOT).as_posix(), "points478_sha256": digest(points_path)}
    sources = []
    for source in selection["sources"]:
        identity = source["identity_id"]
        anatomy = previous[identity] if identity in previous else extra[identity]
        sources.append({"id": identity, "source": (workspace / source["path"]).relative_to(ROOT).as_posix(),
            "sha256": source["sha256"], "source_photo": source["source_photo"],
            **{k: anatomy[k] for k in ("labels", "labels_sha256", "points478", "points478_sha256")}})
    plan = {"schema": "makeup-corrective-source-anatomy-v1", "parser": old["parser"], "sources": sources,
        "source_selection_sha256": digest(workspace / "manifests/selection.json"),
        "production_enabled": False, "new_cpu_analyses": len(pending), "reused_anatomy": len(sources) - len(pending)}
    write(output / "source-plan.json", plan)
    print(json.dumps({"sources": len(sources), "new_cpu_analyses": len(pending),
        "reused_anatomy": len(sources) - len(pending), "source_plan": str(output / "source-plan.json")}, indent=2))
    return plan


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("workspace", type=Path); cli.add_argument("output", type=Path)
    cli.add_argument("--reuse-anatomy", type=Path)
    args = cli.parse_args(); prepare(args.workspace, args.output, reuse_anatomy=args.reuse_anatomy)

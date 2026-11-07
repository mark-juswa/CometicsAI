"""Prepare an immutable paired-Makeup review; no training or image correction."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def verified_pairs(dataset):
    from PIL import Image
    dataset = Path(dataset).resolve()
    manifest = dataset / "manifests/pairs.json"
    rows = json.loads(manifest.read_text(encoding="utf-8"))
    if len(rows) != 60 or len({r["pair_id"] for r in rows}) != 60:
        raise ValueError("Expected frozen 60 unique pairs")
    split_ids = {}
    for row in rows:
        split_ids.setdefault(row["identity_id"], set()).add(row["split"])
        for key, hashkey in (("reference", "source_sha256"), ("target", "target_sha256")):
            path = (dataset / row[key]).resolve()
            if not path.is_relative_to(dataset) or digest(path) != row[hashkey]:
                raise ValueError("Pair path or image hash differs")
            with Image.open(path) as im:
                if im.format != "JPEG" or im.size != (512, 512):
                    raise ValueError("Expected original 512 JPEG")
        caption = (dataset / row["caption_path"]).resolve()
        if not caption.is_relative_to(dataset) or caption.read_text(encoding="utf-8").strip() != row["caption"]:
            raise ValueError("Caption differs")
    if any(len(v) != 1 for v in split_ids.values()) or Counter(r["split"] for r in rows) != {"train": 50, "validation": 10}:
        raise ValueError("Frozen split differs or leaks")
    if len(split_ids) != 12 or any(sum(r["identity_id"] == sid for r in rows) != 5 for sid in split_ids):
        raise ValueError("Expected 12 people with 5 variants")
    return rows, digest(manifest)


def prepare(dataset, output):
    from PIL import Image, ImageDraw, ImageOps
    dataset, output = Path(dataset).resolve(), Path(output)
    rows, manifest_hash = verified_pairs(dataset)
    if output.exists():
        raise ValueError("New review folder required; original evidence preserved")
    output.mkdir(parents=True)
    sheets = []
    for sid in dict.fromkeys(r["identity_id"] for r in rows):
        selected = [r for r in rows if r["identity_id"] == sid]
        sheet = Image.new("RGB", (1152, 840), "white")
        draw = ImageDraw.Draw(sheet)
        images = [("SOURCE " + sid + " / " + selected[0]["split"], dataset / selected[0]["reference"])]
        images += [(r["pair_id"], dataset / r["target"]) for r in selected]
        for index, (label, path) in enumerate(images):
            x, y = index % 3 * 384, index // 3 * 420
            with Image.open(path) as image:
                sheet.paste(ImageOps.contain(image.convert("RGB"), (384,384)), (x,y+30))
            draw.text((x+5,y+8),label,fill="black")
        path=output/(sid+"-review.jpg")
        sheet.save(path,quality=97)
        sheets.append({"subject_id":sid,"sheet":path.name,"sha256":digest(path)})
    report={"schema":"beautycore-makeup-target-review-v1","source_manifest_sha256":manifest_hash,
            "source_dataset":str(dataset),"status":"PREPARED_FOR_QUALITATIVE_REVIEW",
            "originals_modified":False,"training_allowed":False,"pairs":rows,"sheets":sheets}
    (output/"inventory.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report


def validate_review(review, dataset):
    rows, manifest_hash = verified_pairs(dataset)
    if review.get("source_manifest_sha256") != manifest_hash or review.get("training_allowed") is not False:
        raise ValueError("Review provenance differs or attempts training approval")
    decisions = review.get("pairs", [])
    if len(decisions) != 60 or [r["pair_id"] for r in decisions] != [r["pair_id"] for r in rows]:
        raise ValueError("Review must cover all 60 pairs in frozen order")
    for actual, original in zip(decisions, rows):
        if any(actual.get(k) != value for k, value in original.items()):
            raise ValueError("Review original metadata, image or split provenance differs")
        if (actual.get("decision") not in ("KEEP","REJECT","NEEDS_REPLACEMENT")
                or not actual.get("reason") or not actual.get("reviewer")
                or actual.get("human_approval") != "PENDING"
                or actual.get("eligible_for_training") is not False):
            raise ValueError("Incomplete review or fabricated training approval")
    return {"decisions":dict(Counter(r["decision"] for r in decisions)),
            "by_split":{split:dict(Counter(r["decision"] for r in decisions if r["split"]==split))
                        for split in ("train","validation")},
            "training_allowed":False}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=prepare(args.dataset,args.output)
    print(json.dumps({"pairs":len(report["pairs"]),"sheets":len(report["sheets"]),
                     "manifest_sha256":report["source_manifest_sha256"],"training_allowed":False},indent=2))


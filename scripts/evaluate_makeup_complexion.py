"""Reproduce the bounded ten-image complexion review; no models, network or deployment."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.makeup_complexion_field import complexion, CONFIG
from scripts.makeup_boundary_blend import gallery


def owned(name):
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Input escapes project")
    return path


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return np.asarray(Image.open(path).convert("RGB")).copy()


def load(path):
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    if (plan.get("schema") != "beautycore-makeup-complexion-review-v1"
            or plan.get("experiment") != "MAKEUP-COMPLEXION-001"
            or any(plan.get(k) is not False for k in ("production_enabled", "training", "automatic_promotion"))
            or plan.get("new_diffusion_calls") != 0 or plan.get("configuration") != CONFIG
            or plan.get("algorithm_sha256") != digest(ROOT/"scripts/makeup_complexion_field.py")
            or len(plan.get("sources", [])) != 2 or len(plan.get("cases", [])) != 10):
        raise ValueError("Offline complexion review scope differs")
    if len({r["id"] for r in plan["cases"]}) != 10:
        raise ValueError("Duplicate case")
    if sorted(r["guidance"] for r in plan["cases"]) != [2.5]*6 + [4.0]*4:
        raise ValueError("Saved inference-setting matrix differs")
    subjects = {r["id"] for r in plan["sources"]}
    if len(subjects) != 2 or any(r["subject_id"] not in subjects for r in plan["cases"]):
        raise ValueError("Source identities differ")
    for row in plan["sources"]:
        for name, key in (("source","source_sha256"),("source_labels","source_labels_sha256")):
            if digest(owned(row[name])) != row[key]:
                raise ValueError("Source/label differs")
    for row in plan["cases"]:
        for name, key in (("raw","raw_sha256"),("raw_labels","raw_labels_sha256")):
            if digest(owned(row[name])) != row[key]:
                raise ValueError("Raw/label differs")
    return plan


def run(plan_path, output):
    plan = load(plan_path)
    output = Path(output)
    if output.exists():
        raise ValueError("New evidence directory required; preserve previous results")
    output.mkdir(parents=True)
    (output/"plan.json").write_bytes(Path(plan_path).read_bytes())
    (output/"algorithm-source.py").write_bytes((ROOT/"scripts/makeup_complexion_field.py").read_bytes())
    sources = {r["id"]:r for r in plan["sources"]}
    report = {"experiment":plan["experiment"],"variant":"continuous-head-neck-field-v2",
              "status":"IN_PROGRESS","production_enabled":False,"new_diffusion_calls":0,
              "plan_sha256":digest(plan_path),"algorithm_sha256":plan["algorithm_sha256"],
              "configuration":CONFIG,"environment":{"numpy":np.__version__,"opencv":cv2.__version__,"scipy":scipy.__version__},
              "limits":plan["limits"],"cases":[]}
    def save():
        (output/"report.json").write_bytes((json.dumps(report,indent=2)+"\n").encode())
    try:
        for row in plan["cases"]:
            subject = sources[row["subject_id"]]
            source, raw = read(owned(subject["source"])), read(owned(row["raw"]))
            sl = np.asarray(Image.open(owned(subject["source_labels"]))).copy()
            rl = np.asarray(Image.open(owned(row["raw_labels"]))).copy()
            result, allowed, metrics, reference, field, neutral = complexion(source,raw,sl,rl)
            if sha256(result.tobytes()).hexdigest() != row["expected_rgb_sha256"]:
                raise RuntimeError("Saved result no longer reproduces")
            names = {key:row["id"]+"-"+suffix+".png" for key,suffix in
                     (("source_output","source"),("raw_output","raw"),("output","corrected"))}
            for key, image in (("source_output",source),("raw_output",raw),("output",result)):
                Image.fromarray(image).save(output/names[key])
            np.savez_compressed(output/(row["id"]+"-diagnostics.npz"),allowed=allowed,field=field,neutral=neutral)
            sheet = Image.new("RGB",(1536,542),"white")
            draw = ImageDraw.Draw(sheet)
            for i,(label,array) in enumerate((("Original",source),("AI result - saved guidance"+str(row["guidance"]),raw),
                                             ("Complexion correction - EXPERIMENTAL",result))):
                draw.text((i*512+6,8),label,fill="black")
                sheet.paste(Image.fromarray(array),(i*512,30))
            sheet.save(output/(row["id"]+"-comparison.png"))
            changed = np.any(result!=raw,axis=2)
            by_label = {str(int(label)):int((changed & (rl==label)).sum()) for label in np.unique(rl)}
            report["cases"].append({**row,**names,**metrics,"output_sha256":digest(output/names["output"]),
                                    "rgb_sha256":sha256(result.tobytes()).hexdigest(),"changed_pixels_by_parser_label":by_label,
                                    "visual_verdict":"NEEDS_HUMAN_REVIEW"})
            save()
        report["status"]="COMPLETE_REQUIRES_VISUAL_REVIEW"
    except BaseException as exc:
        report.update(status="FAILED",error_type=type(exc).__name__,error=str(exc))
        raise
    finally:
        save()
        gallery(output,report["cases"])
        path=output/"review-self-contained.html"
        text=path.read_text(encoding="utf-8")
        text=text.replace("Makeup boundary blend","Source-referenced Makeup complexion")
        text=text.replace("Boundary blend","Complexion correction")
        text=text.replace("One fixed method on six saved images.","One fixed method on ten saved outputs from two reused people. First four use deployed guidance4.0; six use experimental2.5.")
        text=text.replace("Outside the blend, the original photo is restored.",
                          "Continuous correction can alter lip/brow/head-edge and neck colors; narrow inner-eye/neutral-teeth protection is used. Only pixels outside the actual edit influence are guaranteed raw-identical.")
        path.write_bytes(text.encode())
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan",type=Path,default=ROOT/"data/makeup/MAKEUP-COMPLEXION-001/review-plan.json")
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    run(args.plan,args.output)

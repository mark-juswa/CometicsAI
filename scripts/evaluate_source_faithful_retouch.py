"""Guarded two-photo source-faithful review; no network/model/serving operations."""
import argparse
import base64
from hashlib import sha256
import html
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.makeup_source_faithful_retouch import retouch, CONFIG


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def owned(name):
    path=(ROOT/name).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Input escapes project")
    return path


def load_plan(path):
    plan=json.loads(Path(path).read_text(encoding="utf-8"))
    if (plan.get("schema")!="beautycore-source-faithful-retouch-v1"
            or plan.get("experiment")!="MAKEUP-FAITHFUL-001"
            or any(plan.get(k) is not False for k in ("production_enabled","automatic_promotion","training"))
            or plan.get("new_diffusion_calls")!=0 or plan.get("configuration")!=CONFIG
            or plan.get("algorithm_sha256")!=digest(ROOT/"scripts/makeup_source_faithful_retouch.py")
            or [row.get("id") for row in plan.get("cases",[])]!=["054109","056266"]):
        raise ValueError("Bounded subtle-retouch scope differs")
    for row in plan["cases"]:
        for name,key in (("source","source_sha256"),("source_labels","source_labels_sha256"),
                         ("reference","reference_sha256"),("reference_labels","reference_labels_sha256")):
            if digest(owned(row[name]))!=row[key]:
                raise ValueError("Frozen original/reference evidence differs")
    return plan


def gallery(output,rows):
    cards=[]
    for row in rows:
        def uri(suffix):
            return "data:image/png;base64,"+base64.b64encode((output/(row["id"]+"-"+suffix+".png")).read_bytes()).decode()
        original,previous,result=uri("original"),uri("previous"),uri("retouch")
        cards.append("<section><h2>Portrait "+html.escape(row["id"])+"</h2><div class=grid>")
        for label,url in (("Original photo",original),("Previous corrected AI face",previous),("New: subtle original-photo retouch",result)):
            cards.append("<figure><figcaption>"+label+"</figcaption><button onclick='enlarge(this)'><img alt='"+
                         html.escape(label,quote=True)+"' src='"+url+"'></button></figure>")
        cards.append("</div><details><summary>Toggle original / subtle retouch at full size</summary><p>Changes are intentionally small. No smoothing, new makeup details or facial reshaping.</p>"+
                     "<button onclick='toggle(this)' data-original='"+original+"' data-result='"+result+"' data-current='result'>"+
                     "<img alt='Subtle retouch; click to toggle original' src='"+result+"'></button></details></section>")
    page="""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Subtle original-photo retouch — NOT DEPLOYED</title><style>
body{font:16px system-ui;max-width:1500px;margin:24px auto;padding:0 16px;background:#f5f5f8;color:#191925}
section{margin:24px 0;padding:16px;background:white;border-radius:12px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
figure{margin:0;min-width:0}figcaption{min-height:48px;overflow-wrap:anywhere}img{display:block;max-width:100%}button{padding:0;border:0;background:none;cursor:zoom-in}
details{margin-top:18px}details>button{width:100%;max-width:512px;cursor:pointer}summary{cursor:pointer}dialog{max-width:95vw;max-height:95vh}
dialog img{max-height:85vh;object-fit:contain}dialog button{padding:8px;cursor:pointer}@media(max-width:700px){.grid{grid-template-columns:1fr}}
</style><h1>Subtle original-photo retouch — NOT DEPLOYED</h1>
<p>The original photo supplies the face, expression, lighting and texture. Only tiny low-frequency skin-color changes are allowed.
Original eye/lip/teeth/brow/nose/hair/background pixels remain unchanged under the checked parser regions.
This is one subtle complexion prototype, not a full makeup makeover or evidence that every Makeup preset is solved.</p>
<p>Left: original. Middle: previous regenerated face after color correction. Right: the new source-photo result. Click any image to enlarge.</p>"""+ "".join(cards)+"""
<dialog id=viewer><button onclick="this.parentElement.close()">Close</button><img alt="Original-size preview"></dialog>
<script>function enlarge(b){let d=document.getElementById('viewer');d.querySelector('img').src=b.querySelector('img').src;d.showModal();}
function toggle(b){let original=b.dataset.current!=='original';b.dataset.current=original?'original':'result';b.querySelector('img').src=original?b.dataset.original:b.dataset.result;b.querySelector('img').alt=original?'Original photo; click for subtle retouch':'Subtle retouch; click for original';}</script>"""
    (output/"review-self-contained.html").write_bytes(page.encode())


def run(plan_path,output):
    plan=load_plan(plan_path);output=Path(output)
    if output.exists():
        raise ValueError("Preserve existing evidence; new output required")
    output.mkdir(parents=True)
    (output/"plan.json").write_bytes(Path(plan_path).read_bytes())
    (output/"algorithm-source.py").write_bytes((ROOT/"scripts/makeup_source_faithful_retouch.py").read_bytes())
    read=lambda p:np.asarray(Image.open(p).convert("RGB")).copy()
    report={"experiment":plan["experiment"],"status":"IN_PROGRESS","production_enabled":False,
            "new_diffusion_calls":0,"plan_sha256":digest(plan_path),"algorithm_sha256":plan["algorithm_sha256"],"cases":[]}
    try:
        for row in plan["cases"]:
            original,reference=read(owned(row["source"])),read(owned(row["reference"]))
            labels=np.asarray(Image.open(owned(row["source_labels"]))).copy()
            reference_labels=np.asarray(Image.open(owned(row["reference_labels"]))).copy()
            result,allowed,metrics=retouch(original,reference,labels,reference_labels)
            for name,image in (("original",original),("previous",reference),("retouch",result)):
                Image.fromarray(image).save(output/(row["id"]+"-"+name+".png"))
            Image.fromarray(allowed.astype(np.uint8)*255).save(output/(row["id"]+"-allowed.png"))
            sheet=Image.new("RGB",(1536,542),"white");draw=ImageDraw.Draw(sheet)
            for i,(label,image) in enumerate((("Original photo",original),("Previous color-corrected AI face",reference),
                                             ("Subtle retouch - ORIGINAL PHOTO BASE",result))):
                draw.text((i*512+6,8),label,fill="black");sheet.paste(Image.fromarray(image),(i*512,30))
            sheet.save(output/(row["id"]+"-comparison.png"))
            report["cases"].append({**row,**metrics,"output":row["id"]+"-retouch.png",
                "output_sha256":digest(output/(row["id"]+"-retouch.png")),"rgb_sha256":sha256(result.tobytes()).hexdigest(),
                "visual_verdict":"NEEDS_HUMAN_REVIEW"})
        report["status"]="COMPLETE_REQUIRES_VISUAL_REVIEW"
    finally:
        (output/"report.json").write_bytes((json.dumps(report,indent=2)+"\n").encode())
        gallery(output,report["cases"])
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan",type=Path,default=ROOT/"data/makeup/MAKEUP-FAITHFUL-001/plan-v2.json")
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();run(args.plan,args.output)

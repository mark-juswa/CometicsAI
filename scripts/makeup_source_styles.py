"""Offline extension to seven existing Makeup looks; source-only rendering."""
import argparse
import json
from pathlib import Path
import shutil
import time
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import makeup_source_render as base
STYLES=("no_makeup_makeup","smoky_glam","dewy_peach","rosy_pink",
        "bronze_golden_glam","matte_nude","bold_evening_glam")
EXTRA_KEYS={"pigment","eye_shape","lower_eye_opacity","cheek_highlight",
            "lip_gloss","lip_matte","gold_sheen","description","unsupported_features"}


def check_profile(profile):
    if set(profile)!=EXTRA_KEYS or profile["eye_shape"] not in ("soft","smoky","evening"):
        raise ValueError("Invalid extended profile shape/fields")
    base.profile_check(profile["pigment"])
    for key,maximum in (("lower_eye_opacity",.35),("cheek_highlight",.8),
                        ("lip_gloss",.8),("lip_matte",.8),("gold_sheen",.65)):
        value=profile[key]
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not np.isfinite(value) or not 0<=value<=maximum:
            raise ValueError("Unbounded localized finish")
    if not isinstance(profile["description"],str) or not isinstance(profile["unsupported_features"],list):
        raise ValueError("Missing truthful feature descriptions")


def owned(relative):
    path=(ROOT/relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Input path escapes project")
    return path


def load_plan(path):
    plan=json.loads(Path(path).read_text(encoding="utf-8"))
    if (plan.get("experiment")!="MAKEUP-RENDER-002" or plan.get("generator")!="beautycore_makeup_render_styles_pilot_v1"
            or any(plan.get(key) is not False for key in ("production_enabled","training","lora_active","project_trained_generator_used"))
            or plan.get("case_count")!=28 or set(plan["profiles"])!=set(STYLES)
            or len(plan["subjects"])!=4 or len({r["id"] for r in plan["subjects"]})!=4):
        raise ValueError("Frozen 7style/4person offline scope differs")
    for profile in plan["profiles"].values():
        check_profile(profile)
    for relative,expected in ((plan["baseline_plan"],plan["baseline_plan_sha256"]),
                              (plan["baseline_report"],plan["baseline_report_sha256"]),
                              (plan["baseline_renderer"],plan["baseline_renderer_sha256"])):
        if base.digest(owned(relative))!=expected:
            raise ValueError("Baseline reference changed")
    baseline=json.loads(owned(plan["baseline_plan"]).read_text(encoding="utf-8"))
    if plan["subjects"]!=baseline["subjects"] or plan["parser"]!=baseline["parser"]:
        raise ValueError("Original subjects/parser provenance differs")
    if len(plan["cached_maps"])!=4 or {r["id"] for r in plan["cached_maps"]}!={r["id"] for r in plan["subjects"]}:
        raise ValueError("Cached maps differ")
    for subject in plan["subjects"]:
        if Path(subject["id"]).name!=subject["id"] or base.digest(owned(subject["source"]))!=subject["sha256"]:
            raise ValueError("Source hash/path differs")
        row=next(r for r in plan["cached_maps"] if r["id"]==subject["id"])
        if base.digest(owned(row["labels"]))!=row["labels_sha256"]:
            raise ValueError("Cached source map changed")
    return plan


def fields_for(labels,profile):
    check_profile(profile)
    fields,protected,_,placements=base.geometry(labels)
    skin=(labels==1)
    skin_soft=base.inside(skin,3)
    fields={key:value.copy() for key,value in fields.items()}
    shape=profile["eye_shape"]
    if shape!="soft":
        spread=cv2.GaussianBlur(fields["shadow"],(0,0),1.6)
        fields["shadow"]=np.maximum(fields["shadow"],spread)**(.72 if shape=="smoky" else .78)
        fields["shadow"]*=skin_soft
    lower=np.zeros((512,512),np.float32)
    high=np.zeros_like(lower)
    gold=np.zeros_like(lower)
    yy,xx=np.mgrid[:512,:512]
    face_x=np.where(np.isin(labels,(1,2)))[1].mean()
    mouth_top=float(np.where(np.isin(labels,(10,11,12)))[0].min())
    for item in placements:
        eye=base.largest(labels==item["eye_label"],20)
        ey,ex=np.where(eye)
        columns=np.unique(ex)
        bottom=np.array([np.where(eye[:,x])[0].max() for x in columns],np.float32)
        curve=np.interp(np.arange(512),columns,bottom)[None,:]
        cx,cy=item["eye_center"];width=item["eye_width"]
        horizontal=np.clip(1-((xx-cx)/(width*.67))**2,0,1)**1.4
        distance=yy-curve
        band=np.exp(-.5*((distance-1.4)/2.1)**2)*(distance>0)*(distance<7)
        lower=np.maximum(lower,(band*horizontal*skin_soft).astype(np.float32))
        outward=-1 if cx<face_x else 1
        center_x=cx+outward*width*.32
        gap=max(15,mouth_top-float(ey.max()))
        center_y=float(ey.max())+.28*gap
        patch=np.exp(-.5*(((xx-center_x)/(width*.43))**2+
                         ((yy-center_y)/max(7,gap*.12))**2))
        patch[patch<.025]=0
        high=np.maximum(high,(patch*skin_soft).astype(np.float32))
        inner_center=cx-outward*width*.12
        sheen=np.exp(-.5*((xx-inner_center)/(width*.28))**2)
        gold=np.maximum(gold,(fields["shadow"]*sheen).astype(np.float32))
    fields["lower_eye"]=lower
    fields["cheek_highlight"]=high
    fields["gold"]=gold
    for key,field in fields.items():
        field[protected]=0
        field[field<.002]=0
        if not np.isfinite(field).all():
            raise ValueError("Invalid source-coordinate cosmetic field")
    return fields,protected,placements


def support(fields,profile):
    pigment=profile["pigment"]
    active=[fields[key]*pigment[key+"_opacity"] for key in ("lip","shadow","liner","blush")]
    active += [fields["lower_eye"]*profile["lower_eye_opacity"],
               fields["cheek_highlight"]*profile["cheek_highlight"],
               fields["gold"]*profile["gold_sheen"],
               fields["lip"]*max(profile["lip_gloss"],profile["lip_matte"])]
    return np.logical_or.reduce([r>0 for r in active])


def render(source,labels,profile):
    if source.shape!=(512,512,3) or source.dtype!=np.uint8:
        raise ValueError("Expected original 512 RGB")
    fields,protected,placements=fields_for(labels,profile)
    allowed=support(fields,profile)
    pigment=profile["pigment"]
    original=base.lab(source);out=original.copy()
    stats={}
    stats["lip"]=base.tint(out,original,fields["lip"],pigment["lip_rgb"],pigment["lip_opacity"],
                           pigment["lip_chroma_cap"],("target",pigment["lip_lightness_cap"]))
    stats["shadow"]=base.tint(out,original,fields["shadow"],pigment["shadow_rgb"],pigment["shadow_opacity"],
                              28.0,-pigment["shadow_darkening"])
    stats["blush"]=base.tint(out,original,fields["blush"],pigment["blush_rgb"],pigment["blush_opacity"],18.0,0.0)
    out[:,:,0]-=fields["liner"]*pigment["liner_opacity"]*pigment["liner_darkening"]
    out[:,:,0]-=fields["lower_eye"]*profile["lower_eye_opacity"]*12.0
    # Small highlights stay in localized source cheek/lip fields; no global base change.
    out[:,:,0]+=fields["cheek_highlight"]*profile["cheek_highlight"]*2.5
    core=fields["lip"]>.45
    if core.sum()<50:
        raise ValueError("Insufficient lip region for finishes")
    low=cv2.GaussianBlur(original[:,:,0],(0,0),2.0)
    q65,q95=np.quantile(low[core],(.65,.95))
    gloss=np.clip((low-q65)/max(1.0,q95-q65),0,1)
    matte=np.clip(low-q65,0,5.0)
    out[:,:,0]+=fields["lip"]*gloss*profile["lip_gloss"]*1.8
    out[:,:,0]-=fields["lip"]*matte*profile["lip_matte"]
    if profile["gold_sheen"]:
        stats["gold"]=base.tint(out,original,fields["gold"],[206,167,77],profile["gold_sheen"],20.0,2.0)
    out,gamut_count=base.gamut_safe(out,allowed)
    converted=np.rint(np.clip(cv2.cvtColor(out,cv2.COLOR_LAB2RGB),0,1)*255).astype(np.uint8)
    result=source.copy()
    result[allowed]=converted[allowed]
    changed=np.any(result!=source,axis=2)
    if np.any(changed&(~allowed|protected)):
        raise RuntimeError("Changed protected/noncosmetic source")
    return result,fields,{
        "changed_pixels":int(changed.sum()),
        "outside_cosmetic_changed_pixels":int((changed&~allowed).sum()),
        "protected_changed_pixels":int((changed&protected).sum()),
        "gamut_compressed_pixels":gamut_count,"placements":placements,"pigments":stats,
        "region_changed_pixels":{key:int((changed&(field>0)).sum()) for key,field in fields.items()},
        "supported_description":profile["description"],"unsupported_features":profile["unsupported_features"],
        "limit":"Color/finish fields are experimental proposals, not validated cosmetic realism."
    }



def overlay(source,fields,profile):
    preview=base.overlay(source,fields).astype(np.float32)
    for key,strength,color in (
        ("lower_eye",profile["lower_eye_opacity"],[50,220,230]),
        ("cheek_highlight",profile["cheek_highlight"],[220,90,220]),
        ("gold",profile["gold_sheen"],[245,195,40])):
        if strength:
            alpha=fields[key][:,:,None]*.55
            preview=preview*(1-alpha)+np.array(color)*alpha
    return np.rint(preview).clip(0,255).astype(np.uint8)


def baseline_controls(plan):
    old=json.loads(owned(plan["baseline_plan"]).read_text())
    report=json.loads(owned(plan["baseline_report"]).read_text())
    proof=[]
    for subject in plan["subjects"]:
        source=base.read_rgb(owned(subject["source"]))
        maprow=next(r for r in plan["cached_maps"] if r["id"]==subject["id"])
        labels=np.asarray(Image.open(owned(maprow["labels"]))).copy()
        for style in base.STYLES:
            row=next(r for r in report["cases"] if r["subject_id"]==subject["id"] and r["style_id"]==style)
            path=owned(plan["baseline_report"]).parent/row["output"]
            if base.digest(path)!=row["sha256"]:
                raise ValueError("Baseline saved image changed")
            result,_,_=base.render(source,labels,old["profiles"][style])
            if not np.array_equal(result,base.read_rgb(path)):
                raise ValueError("Existing profile output changed")
            proof.append({"subject_id":subject["id"],"style_id":style,"png_sha256":row["sha256"],"pixels_identical":True})
    return proof


def prepare(plan_path,output):
    plan=load_plan(plan_path);output=Path(output)
    if output.exists():
        raise ValueError("New extension directory required")
    controls=baseline_controls(plan)
    output.mkdir(parents=True)
    shutil.copyfile(plan_path,output/"plan.json")
    maps=[]
    for subject in plan["subjects"]:
        row=next(r for r in plan["cached_maps"] if r["id"]==subject["id"])
        path=output/(subject["id"]+"-labels.png")
        shutil.copyfile(owned(row["labels"]),path)
        maps.append({"id":subject["id"],"labels":path.name,"sha256":base.digest(path)})
        source=base.read_rgb(owned(subject["source"]))
        labels=np.asarray(Image.open(path))
        sheet=Image.new("RGB",(2048,1100),"white");draw=ImageDraw.Draw(sheet)
        sheet.paste(Image.fromarray(source),(0,28));draw.text((8,8),"ORIGINAL "+subject["id"],fill="black")
        for i,style in enumerate(STYLES,1):
            fields,_,_=fields_for(labels,plan["profiles"][style])
            preview=overlay(source,fields,plan["profiles"][style])
            x,y=i%4*512,i//4*550
            sheet.paste(Image.fromarray(preview),(x,y+28))
            draw.text((x+6,y+8),style+" / SOURCE REGIONS",fill="black")
        sheet.save(output/(subject["id"]+"-region-review.png"))
    base.write_json(output/"prepared.json",{
        "plan_sha256":base.digest(plan_path),"cached_maps":maps,"baseline_controls":controls,
        "region_review":"PENDING","production_enabled":False})
    print("PREPARED:4cached source maps;12baseline controls reproduced; no model download/inference.",flush=True)


def apply(plan_path,output):
    plan=load_plan(plan_path);output=Path(output)
    if (output/"report.json").exists() or list(output.glob("*-rendered.png")):
        raise ValueError("Do not overwrite extension evidence")
    prepared=json.loads((output/"prepared.json").read_text())
    if base.digest(plan_path)!=prepared["plan_sha256"] or base.digest(output/"plan.json")!=prepared["plan_sha256"]:
        raise ValueError("Prepared extension plan differs")
    records=[]
    style_sheets={style:Image.new("RGB",(2048,1100),"white") for style in STYLES}
    for person_index,subject in enumerate(plan["subjects"]):
        source=base.read_rgb(owned(subject["source"]))
        cached=next(r for r in prepared["cached_maps"] if r["id"]==subject["id"])
        path=(output/cached["labels"]).resolve()
        if not path.is_relative_to(output.resolve()) or base.digest(path)!=cached["sha256"]:
            raise ValueError("Prepared source map differs")
        labels=np.asarray(Image.open(path)).copy()
        sheet=Image.new("RGB",(2048,1100),"white");draw=ImageDraw.Draw(sheet)
        sheet.paste(Image.fromarray(source),(0,28));draw.text((7,8),"ORIGINAL "+subject["id"],fill="black")
        for i,style in enumerate(STYLES,1):
            started=time.perf_counter()
            result,_,metrics=render(source,labels,plan["profiles"][style])
            seconds=time.perf_counter()-started
            name=subject["id"]+"-"+style+"-rendered.png"
            Image.fromarray(result).save(output/name)
            x,y=i%4*512,i//4*550
            sheet.paste(Image.fromarray(result),(x,y+28))
            draw.text((x+6,y+8),plan["profiles"][style]["pigment"]["name"]+" / PILOT",fill="black")
            other=style_sheets[style];d=ImageDraw.Draw(other);column=person_index*512
            other.paste(Image.fromarray(source),(column,28));d.text((column+6,8),"ORIGINAL "+subject["id"],fill="black")
            other.paste(Image.fromarray(result),(column,578));d.text((column+6,558),plan["profiles"][style]["pigment"]["name"],fill="black")
            records.append({"subject_id":subject["id"],"style_id":style,"output":name,"sha256":base.digest(output/name),
                            "source_sha256":subject["sha256"],"metrics":metrics,"render_seconds_excluding_io":seconds,
                            "generator":plan["generator"],"lora_active":False,"project_trained_generator_used":False,
                            "human_approval":"PENDING"})
            print("STYLE",len(records),"/28",subject["id"],style,flush=True)
        sheet.save(output/(subject["id"]+"-seven-styles.png"))
    for style,sheet in style_sheets.items():sheet.save(output/(style+"-four-people.png"))
    base.write_json(output/"report.json",{"experiment":plan["experiment"],"generator":plan["generator"],
                    "plan_sha256":base.digest(plan_path),"runner_sha256":base.digest(Path(__file__)),
                    "baseline_renderer_sha256":plan["baseline_renderer_sha256"],
                    "production_enabled":False,"training":False,"lora_active":False,
                    "project_trained_generator_used":False,"new_model_inference_calls":0,"new_gpu_calls":0,
                    "cases":records,"retained_baseline_count":len(prepared["baseline_controls"]),
                    "status":"COMPLETE_REQUIRES_VISUAL_REVIEW","limits":plan["limits"]})
    return records


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--stage",choices=("prepare","apply"),required=True)
    args=parser.parse_args()
    (prepare if args.stage=="prepare" else apply)(args.plan,args.output)

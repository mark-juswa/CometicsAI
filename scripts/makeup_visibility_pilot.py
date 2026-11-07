"""Focused non-lip visibility experiment; prior lipstick remains pixel-identical."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import time

import cv2
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import makeup_source_render as base

STYLES=("soft_glam","smoky_glam","rosy_pink")
RULES={"maximum_nonlip_lightness_reduction":16.0,"maximum_nonlip_lightness_increase":2.0,
       "maximum_nonlip_chroma_shift":40.0,"lip_pixels":"EXACT_PREVIOUS"}


def owned(relative):
    p=(ROOT/relative).resolve()
    if not p.is_relative_to(ROOT):raise ValueError("Path escapes project")
    return p


def check_profile(profile):
    expected={"name","shadow_rgb","shadow_opacity","shadow_darkening","crease_rgb",
              "crease_opacity","crease_darkening","liner_opacity","liner_darkening",
              "lower_opacity","blush_rgb","blush_opacity"}
    if set(profile)!=expected:raise ValueError("Unexpected visibility profile fields")
    colors=("shadow_rgb","crease_rgb","blush_rgb")
    for key in colors:
        if len(profile[key])!=3 or any(type(v) is not int or not 0<=v<=255 for v in profile[key]):
            raise ValueError("Invalid pigment color")
    for key in ("shadow_opacity","crease_opacity","liner_opacity"):
        if not np.isfinite(profile[key]) or not 0<=profile[key]<=1:
            raise ValueError("Invalid layer opacity")
    if not 0<=profile["blush_opacity"]<=.25 or not 0<=profile["lower_opacity"]<=.3:
        raise ValueError("Unbounded blush/lower-eye layer")
    for key in ("shadow_darkening","crease_darkening","liner_darkening"):
        if not np.isfinite(profile[key]) or not 0<=profile[key]<=25:
            raise ValueError("Unbounded local darkening")


def load_plan(path):
    plan=json.loads(Path(path).read_text())
    if (plan.get("experiment")!="MAKEUP-VISIBILITY-001" or plan.get("case_count")!=12
            or set(plan["profiles"])!=set(STYLES) or len(plan["subjects"])!=4 or len(plan["cases"])!=12
            or plan.get("layer_rules")!=RULES
            or any(plan.get(k) is not False for k in ("production_enabled","training","lora_active","new_model_inference"))):
        raise ValueError("Focused non-lip experiment scope differs")
    for k in ("base_renderer","previous_extension"):
        if base.digest(owned(plan[k]))!=plan[k+"_sha256"]:raise ValueError("Previous code differs")
    if len({(r["subject_id"],r["style_id"]) for r in plan["cases"]})!=12:
        raise ValueError("Duplicate comparison case")
    for profile in plan["profiles"].values():check_profile(profile)
    for subject in plan["subjects"]:
        if base.digest(owned(subject["source"]))!=subject["sha256"]:raise ValueError("Original changed")
        row=next(r for r in plan["cached_maps"] if r["id"]==subject["id"])
        if base.digest(owned(row["labels"]))!=row["labels_sha256"]:raise ValueError("Source map changed")
    for row in plan["cases"]:
        if base.digest(owned(row["previous"]))!=row["previous_sha256"]:raise ValueError("Previous output changed")
    return plan


def regions(labels):
    _,protected,_,placements=base.geometry(labels)
    yy,xx=np.mgrid[:512,:512]
    skin=(labels==1)
    skin_soft=base.inside(skin,2)
    body=np.zeros((512,512),np.float32)
    crease=np.zeros_like(body);liner=np.zeros_like(body);lower=np.zeros_like(body);blush=np.zeros_like(body)
    mouth_y,mouth_x=np.where(np.isin(labels,(10,11,12)))
    mouth_top=float(mouth_y.min())
    mouth_guard=np.zeros_like(skin)
    mouth_guard[max(0,mouth_y.min()-5):min(512,mouth_y.max()+6),
                max(0,mouth_x.min()-5):min(512,mouth_x.max()+6)]=True
    face_center=np.where(np.isin(labels,(1,2)))[1].mean()
    for eye_label,brow_label in ((4,6),(5,7)):
        eye=base.largest(labels==eye_label,20)
        brow=base.largest(labels==brow_label,20)
        ey,ex=np.where(eye);by,bx=np.where(brow)
        cx=float(ex.mean());width=float(ex.max()-ex.min()+1)
        columns=np.unique(ex)
        top=np.array([np.where(eye[:,x])[0].min() for x in columns],np.float32)
        bottom=np.array([np.where(eye[:,x])[0].max() for x in columns],np.float32)
        top_curve=np.interp(np.arange(512),columns,top)[None,:]
        bottom_curve=np.interp(np.arange(512),columns,bottom)[None,:]
        bcols=np.unique(bx)
        brow_lower=np.array([np.where(brow[:,x])[0].max() for x in bcols],np.float32)
        brow_curve=np.interp(np.arange(512),bcols,brow_lower)[None,:]
        # Use actual source brow-to-lid space; do not cap it to a thin strip.
        gap=np.maximum(top_curve-brow_curve-2,4)
        t=(top_curve-yy-1)/gap
        horizontal=np.clip(1-((xx-cx)/(width*.82))**2,0,1)**1.2
        band=(t>0)&(t<1)
        body_piece=(np.sin(np.pi*np.clip(t,0,1))**.65)*horizontal*band*skin_soft
        direction=-1 if cx<face_center else 1
        outer=np.clip(.55+direction*(xx-cx)/width,.2,1)
        crease_piece=np.exp(-.5*((t-.67)/.19)**2)*horizontal*outer*band*skin_soft
        body=np.maximum(body,body_piece.astype(np.float32))
        crease=np.maximum(crease,crease_piece.astype(np.float32))
        d=top_curve-yy
        line=np.exp(-.5*((d-.8)/1.05)**2)*(d>=0)*(d<=4)*horizontal*skin_soft
        liner=np.maximum(liner,line.astype(np.float32))
        dd=yy-bottom_curve
        lower_piece=np.exp(-.5*((dd-1.3)/2.0)**2)*(dd>0)*(dd<7)*horizontal*skin_soft
        lower=np.maximum(lower,lower_piece.astype(np.float32))
        gap_mouth=max(20,mouth_top-float(ey.max()))
        cheek_x=cx+direction*width*.45
        cheek_y=float(ey.max())+.53*gap_mouth
        cheek=np.exp(-.5*(((xx-cheek_x)/(width*.55))**2+((yy-cheek_y)/(gap_mouth*.29))**2))
        cheek[cheek<.025]=0
        blush=np.maximum(blush,(cheek*base.inside(skin,4)).astype(np.float32))
    fields={"body":body,"crease":crease,"liner":liner,"lower":lower,"blush":blush}
    mouth_fade=base.inside(~mouth_guard,8)
    for field in fields.values():
        field*=mouth_fade
        field[protected|mouth_guard]=0
        field[field<.002]=0
    return fields,protected,mouth_guard


def render(source,previous,labels,profile):
    check_profile(profile)
    if source.shape!=(512,512,3) or previous.shape!=source.shape or source.dtype!=np.uint8 or previous.dtype!=np.uint8:
        raise ValueError("Expected matching original/previous512RGB")
    fields,protected,mouth_guard=regions(labels)
    original=base.lab(source);out=original.copy()
    stats={}
    stats["body"]=base.tint(out,original,fields["body"],profile["shadow_rgb"],profile["shadow_opacity"],36.0,-profile["shadow_darkening"])
    stats["crease"]=base.tint(out,original,fields["crease"],profile["crease_rgb"],profile["crease_opacity"],24.0,-profile["crease_darkening"])
    stats["blush"]=base.tint(out,original,fields["blush"],profile["blush_rgb"],profile["blush_opacity"],28.0,-.5)
    out[:,:,0]-=fields["liner"]*profile["liner_opacity"]*profile["liner_darkening"]
    out[:,:,0]-=fields["lower"]*profile["lower_opacity"]*14
    delta=out-original
    out[:,:,0]=original[:,:,0]+np.clip(delta[:,:,0],-RULES["maximum_nonlip_lightness_reduction"],RULES["maximum_nonlip_lightness_increase"])
    chroma=delta[:,:,1:]
    norm=np.linalg.norm(chroma,axis=2)
    scale=np.minimum(1,RULES["maximum_nonlip_chroma_shift"]/np.maximum(norm,1e-6))
    out[:,:,1:]=original[:,:,1:]+chroma*scale[:,:,None]
    allowed=((labels==1)&~mouth_guard)&(
        np.logical_or.reduce([v>0 for v in fields.values()])|np.any(previous!=source,axis=2))
    out,gamut=base.gamut_safe(out,allowed)
    converted=np.rint(np.clip(cv2.cvtColor(out,cv2.COLOR_LAB2RGB),0,1)*255).astype(np.uint8)
    result=previous.copy()
    result[allowed]=converted[allowed]
    if not np.array_equal(result[mouth_guard],previous[mouth_guard]):
        raise RuntimeError("Lip/mouth comparison changed")
    if not np.array_equal(result[protected],previous[protected]):
        raise RuntimeError("Protected features changed")
    changed=np.any(result!=previous,axis=2)
    if np.any(changed&~allowed):raise RuntimeError("Unrelated comparison pixels changed")
    return result,fields,{
        "nonlip_changed_pixels":int(changed.sum()),"lip_mouth_changed_pixels":int(np.any(result[mouth_guard]!=previous[mouth_guard],axis=1).sum()),
        "outside_allowed_changed_pixels":int((changed&~allowed).sum()),
        "protected_changed_pixels":int((changed&protected).sum()),"gamut_compressed_pixels":gamut,
        "layers":stats,"allowed_pixels":int(allowed.sum())}


def prepare(plan_path,output):
    plan=load_plan(plan_path);output=Path(output)
    if output.exists():raise ValueError("New visibility directory required")
    output.mkdir(parents=True);shutil.copyfile(plan_path,output/"plan.json")
    for subject in plan["subjects"]:
        row=next(r for r in plan["cached_maps"] if r["id"]==subject["id"])
        source=base.read_rgb(owned(subject["source"]))
        labels=np.asarray(Image.open(owned(row["labels"]))).copy()
        fields,_,_=regions(labels)
        preview=source.astype(np.float32)
        for key,color in (("body",[70,130,250]),("crease",[200,140,35]),("blush",[70,210,100])):
            alpha=fields[key][:,:,None]*.5
            preview=preview*(1-alpha)+np.array(color)*alpha
        Image.fromarray(np.rint(preview).clip(0,255).astype(np.uint8)).save(output/(subject["id"]+"-regions.png"))
    base.write_json(output/"prepared.json",{"plan_sha256":base.digest(plan_path),"production_enabled":False})
    print("Prepared four source-coordinate eye/cheek overlays.",flush=True)


def apply(plan_path,output):
    plan=load_plan(plan_path);output=Path(output)
    if (output/"report.json").exists() or list(output.glob("*-candidate.png")):raise ValueError("Do not overwrite visibility evidence")
    prepared=json.loads((output/"prepared.json").read_text())
    if prepared["plan_sha256"]!=base.digest(plan_path) or base.digest(output/"plan.json")!=base.digest(plan_path):
        raise ValueError("Prepared plan differs")
    records=[]
    for subject in plan["subjects"]:
        sid=subject["id"]
        source=base.read_rgb(owned(subject["source"]))
        row=next(r for r in plan["cached_maps"] if r["id"]==sid)
        labels=np.asarray(Image.open(owned(row["labels"]))).copy()
        sheet=Image.new("RGB",(1536,1650),"white");draw=ImageDraw.Draw(sheet)
        for i,style in enumerate(STYLES):
            case=next(r for r in plan["cases"] if r["subject_id"]==sid and r["style_id"]==style)
            previous=base.read_rgb(owned(case["previous"]))
            started=time.perf_counter()
            result,fields,metrics=render(source,previous,labels,plan["profiles"][style])
            filename=sid+"-"+style+"-candidate.png"
            Image.fromarray(result).save(output/filename)
            for column,(title,rgb) in enumerate((("ORIGINAL",source),("PREVIOUS",previous),("NON-LIP REVISION",result))):
                sheet.paste(Image.fromarray(rgb),(column*512,i*550+30))
                draw.text((column*512+5,i*550+8),title+" / "+style,fill="black")
            records.append({**case,"output":filename,"sha256":base.digest(output/filename),"metrics":metrics,
                            "render_seconds":time.perf_counter()-started,"human_approval":"PENDING"})
            print("VISIBILITY",len(records),"/12",sid,style,flush=True)
        sheet.save(output/(sid+"-comparison.png"))
    base.write_json(output/"report.json",{"experiment":plan["experiment"],"generator":plan["generator"],
                    "plan_sha256":base.digest(plan_path),"runner_sha256":base.digest(Path(__file__)),
                    "production_enabled":False,"training":False,"lora_active":False,"new_model_inference":False,
                    "cases":records,"status":"COMPLETE_REQUIRES_VISUAL_REVIEW","limits":plan["limits"]})


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan",type=Path,required=True);parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--stage",choices=("prepare","apply"),required=True)
    args=parser.parse_args()
    (prepare if args.stage=="prepare" else apply)(args.plan,args.output)

"""Offline reference-guided complete-look prototype; not a serving backend."""
import argparse
import json
from pathlib import Path
import sys
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import makeup_source_render as base
from scripts import makeup_visibility_pilot as visibility

GENERATOR="beautycore_complete_soft_glam_pilot_v1"
PROFILE={
    "lid_rgb":[162,111,91],"lid_opacity":.65,
    "crease_rgb":[100,65,56],"crease_opacity":.54,
    "blush_rgb":[190,83,81],"blush_opacity":.38,
    "lip_rgb":[158,78,69],"lip_opacity":.82,
    "brow_strength":.30,"lash_strength":.88,
    "highlight_strength":.65
}


def owned(path):
    result=(ROOT/path).resolve()
    if not result.is_relative_to(ROOT):
        raise ValueError("Path escapes project")
    return result


def load_plan(path):
    plan=json.loads(Path(path).read_text(encoding="utf-8"))
    if (plan.get("experiment")!="MAKEUP-COMPLETE-001" or plan.get("generator")!=GENERATOR
        or plan.get("profile")!=PROFILE or plan.get("case_count")!=4
        or len(plan.get("subjects",[]))!=4 or len({s["id"] for s in plan["subjects"]})!=4
        or any(plan.get(k) is not False for k in
               ("production_enabled","training","lora_active","new_model_inference"))):
        raise ValueError("Frozen complete-look scope differs")
    for helper in plan["helpers"]:
        if base.digest(owned(helper["path"]))!=helper["sha256"]:
            raise ValueError("Source helper changed")
    if {r["id"] for r in plan["maps"]}!={s["id"] for s in plan["subjects"]}:
        raise ValueError("Source maps differ")
    for row in plan["subjects"]:
        if Path(row["id"]).name!=row["id"] or base.digest(owned(row["source"]))!=row["sha256"]:
            raise ValueError("Original source changed")
        if base.digest(owned(row["previous"]))!=row["previous_sha256"]:
            raise ValueError("Previous comparison changed")
    for row in plan["maps"]:
        if base.digest(owned(row["labels"]))!=row["sha256"]:
            raise ValueError("Source parsing map changed")
    return plan


def stroke(canvas,points,width):
    scale=3
    points=np.asarray(points,np.float32)
    for i in range(len(points)-1):
        # Taper each lash to a fine tip, with antialiasing before downsampling.
        taper=max(.15,1-i/(len(points)-1))
        cv2.line(canvas,tuple(np.rint(points[i]*scale).astype(int)),
                 tuple(np.rint(points[i+1]*scale).astype(int)),255,
                 max(1,int(round(width*scale*taper))),cv2.LINE_AA)


def fields_for(labels):
    old,_,_,placements=base.geometry(labels)
    visible,_,mouth_guard=visibility.regions(labels)
    skin=labels==1
    skin_soft=base.inside(skin,2)
    yy,xx=np.mgrid[:512,:512]
    fields={"lid":np.zeros((512,512),np.float32),
            "crease":np.zeros((512,512),np.float32),
            "liner":visible["liner"].copy(),"lower":visible["lower"].copy(),
            "blush":visible["blush"].copy(),
            "highlight":np.zeros((512,512),np.float32),
            "shimmer":np.zeros((512,512),np.float32),
            "brow":base.inside(np.isin(labels,(6,7)),1.5),
            "lip":old["lip"].copy()}
    lashes=np.zeros((1536,1536),np.uint8)
    face_center=np.where(np.isin(labels,(1,2)))[1].mean()
    mouth_top=float(np.where(np.isin(labels,(10,11,12)))[0].min())
    for eye_id,brow_id in ((4,6),(5,7)):
        eye=base.largest(labels==eye_id,20)
        brow=base.largest(labels==brow_id,20)
        ey,ex=np.where(eye);by,bx=np.where(brow)
        columns=np.unique(ex);bcols=np.unique(bx)
        top=np.array([np.where(eye[:,x])[0].min() for x in columns],np.float32)
        bbottom=np.array([np.where(brow[:,x])[0].max() for x in bcols],np.float32)
        # Smooth parser stair steps; no independent landmark accuracy claim.
        smooth=cv2.GaussianBlur(top.reshape(1,-1),(0,0),1.4).ravel()
        top_curve=np.interp(np.arange(512),columns,smooth)[None,:]
        brow_curve=np.interp(np.arange(512),bcols,bbottom)[None,:]
        gap=np.maximum(top_curve-brow_curve-2,4)
        t=(top_curve-yy-1)/gap
        cx=float(ex.mean());width=float(ex.max()-ex.min()+1)
        direction=-1 if cx<face_center else 1
        horizontal=np.clip(1-((xx-cx)/(width*.72))**2,0,1)**1.1
        band=(t>0)&(t<1)
        lid=np.exp(-.5*((t-.28)/.23)**2)*horizontal*band*skin_soft
        outer=np.clip(.5+direction*(xx-cx)/width,.15,1)
        crease=np.exp(-.5*((t-.60)/.18)**2)*horizontal*outer*band*skin_soft
        fields["lid"]=np.maximum(fields["lid"],lid.astype(np.float32))
        fields["crease"]=np.maximum(fields["crease"],crease.astype(np.float32))
        inner=np.exp(-.5*((xx-(cx-direction*.12*width))/(width*.27))**2)
        fields["shimmer"]=np.maximum(fields["shimmer"],(lid*inner).astype(np.float32))
        cheek_x=cx+direction*width*.48
        gap_mouth=max(20,mouth_top-float(ey.max()))
        cheek_y=float(ey.max())+.27*gap_mouth
        high=np.exp(-.5*(((xx-cheek_x)/(width*.44))**2+
                       ((yy-cheek_y)/(gap_mouth*.14))**2))*skin_soft
        high[high<.025]=0
        fields["highlight"]=np.maximum(fields["highlight"],high.astype(np.float32))
        # Procedural lash accents follow the source upper-eye contour.
        # They stay on eyelid skin; eye whites/iris/brows are never painted.
        for j,fraction in enumerate(np.linspace(.10,.92,17)):
            x=float(columns.min()+fraction*(columns.max()-columns.min()))
            y=float(np.interp(x,columns,smooth))-1.0
            outer_weight=np.clip(.55+direction*(x-cx)/width,.15,1)
            length=width*(.095+.055*outer_weight)
            dx=direction*width*(.035+.065*outer_weight)
            p0=np.array([x,y]);p1=p0+np.array([dx*.05,-length*.82])
            p2=p0+np.array([dx,-length])
            u=np.linspace(0,1,14)[:,None]
            points=(1-u)**2*p0+2*(1-u)*u*p1+u**2*p2
            stroke(lashes,points,width*.022)
    fields["lashes"]=cv2.resize(lashes.astype(np.float32)/255,(512,512),interpolation=cv2.INTER_AREA)*skin_soft
    for key in fields:
        if key not in ("lip","brow"):
            fields[key][~skin|mouth_guard]=0
        fields[key][fields[key]<.002]=0
    allowed=np.logical_or.reduce([v>0 for v in fields.values()])
    protected=~np.isin(labels,(1,6,7,11,12))
    if np.any(allowed&protected):
        raise RuntimeError("Cosmetics overlap protected anatomy")
    return fields,protected,allowed


def render(source,labels):
    if source.shape!=(512,512,3) or source.dtype!=np.uint8:
        raise ValueError("Expected original 512 RGB8")
    fields,protected,allowed=fields_for(labels)
    original=base.lab(source);out=original.copy();p=PROFILE;stats={}
    stats["lid"]=base.tint(out,original,fields["lid"],p["lid_rgb"],p["lid_opacity"],28,-4)
    stats["crease"]=base.tint(out,original,fields["crease"],p["crease_rgb"],p["crease_opacity"],25,-8)
    stats["blush"]=base.tint(out,original,fields["blush"],p["blush_rgb"],p["blush_opacity"],30,-.8)
    stats["lip"]=base.tint(out,original,fields["lip"],p["lip_rgb"],p["lip_opacity"],35,("target",9))
    out[:,:,0]-=fields["liner"]*18+fields["lower"]*2.0
    # Brow definition enhances existing hair contrast only; no new brow shape.
    brow=fields["brow"]*p["brow_strength"]
    out[:,:,0]-=brow*12
    out[:,:,1:]*=(1-brow[:,:,None]*.12)
    out[:,:,0]+=fields["shimmer"]*3.8
    out[:,:,0]+=fields["highlight"]*p["highlight_strength"]*4
    lip_core=fields["lip"]>.5
    low=cv2.GaussianBlur(original[:,:,0],(0,0),1.8)
    q50,q95=np.quantile(low[lip_core],(.5,.95))
    existing_sheen=np.clip((low-q50)/max(2.,q95-q50),0,1)
    out[:,:,0]+=fields["lip"]*existing_sheen*5
    # Soft inner lip edge for definition without enlarging the mouth.
    distance=cv2.distanceTransform(np.isin(labels,(11,12)).astype(np.uint8),cv2.DIST_L2,5)
    lip_edge=fields["lip"]*np.clip(1-distance/3.5,0,1)
    out[:,:,0]-=lip_edge*4
    # Bound non-lash pigment/lightness; lashes have their own black-pigment blend.
    nonlip=(labels==1)
    delta=out-original
    out[:,:,0][nonlip]=original[:,:,0][nonlip]+np.clip(delta[:,:,0][nonlip],-15,5)
    norm=np.linalg.norm(delta[:,:,1:],axis=2)
    scaling=np.minimum(1,38/np.maximum(norm,1e-6))
    out[:,:,1:]=original[:,:,1:]+delta[:,:,1:]*scaling[:,:,None]
    out,gamut=base.gamut_safe(out,allowed)
    rgb=np.clip(cv2.cvtColor(out,cv2.COLOR_LAB2RGB),0,1)
    alpha=(fields["lashes"]*p["lash_strength"])[:,:,None]
    # Dark warm pigment restricted to antialiased source-contour lash strokes.
    rgb=rgb*(1-alpha)+np.array([.075,.050,.042],np.float32)*alpha
    result=source.copy()
    result[allowed]=np.rint(rgb[allowed]*255).clip(0,255).astype(np.uint8)
    changed=np.any(result!=source,axis=2)
    if np.any(changed&(~allowed|protected)):
        raise RuntimeError("Changed source outside cosmetic support")
    return result,fields,{"changed_pixels":int(changed.sum()),
        "outside_allowed_changes":int((changed&~allowed).sum()),
        "protected_changes":int((changed&protected).sum()),
        "regions":{k:int((changed&(v>0)).sum()) for k,v in fields.items()},
        "gamut_compressed_pixels":gamut,"pigments":stats}


def run(plan_path,output):
    plan=load_plan(plan_path);output=Path(output)
    if output.exists():
        raise ValueError("Use a new directory; preserve earlier evidence")
    output.mkdir(parents=True)
    base.write_json(output/"plan.json",plan)
    records=[]
    for row in plan["subjects"]:
        sid=row["id"];source=base.read_rgb(owned(row["source"]))
        previous=base.read_rgb(owned(row["previous"]))
        mapping=next(m for m in plan["maps"] if m["id"]==sid)
        labels=np.asarray(Image.open(owned(mapping["labels"]))).copy()
        started=time.perf_counter();result,fields,metrics=render(source,labels)
        Image.fromarray(result).save(output/(sid+"-complete.png"))
        sheet=Image.new("RGB",(1536,550),"white");draw=ImageDraw.Draw(sheet)
        for x,title,rgb in ((0,"ORIGINAL",source),(512,"PREVIOUS SOFT GLAM",previous),(1024,"REFERENCE-GUIDED PROTOTYPE",result)):
            sheet.paste(Image.fromarray(rgb),(x,30));draw.text((x+7,9),title,fill="black")
        sheet.save(output/(sid+"-comparison.png"))
        overlay=source.astype(np.float32)
        for key,color in (("lashes",[50,150,255]),("lid",[220,160,70]),("blush",[70,200,120]),("highlight",[240,220,70]),("brow",[180,80,220])):
            a=fields[key][:,:,None]*.5;overlay=overlay*(1-a)+np.array(color)*a
        Image.fromarray(np.rint(overlay).clip(0,255).astype(np.uint8)).save(output/(sid+"-regions.png"))
        records.append({"id":sid,"output":sid+"-complete.png","sha256":base.digest(output/(sid+"-complete.png")),
                        "seconds":time.perf_counter()-started,"metrics":metrics,"human_acceptance":"PENDING"})
        print("COMPLETE_LOOK",len(records),"/4",sid,flush=True)
    base.write_json(output/"report.json",{"experiment":plan["experiment"],"generator":GENERATOR,
        "plan_sha256":base.digest(plan_path),"runner_sha256":base.digest(Path(__file__)),
        "production_enabled":False,"training":False,"lora_active":False,"new_model_inference":False,
        "cases":records,"release_ready":False,"status":"REQUIRES_VISUAL_REVIEW",
        "limitations":plan["limitations"]})


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    run(args.plan,args.output)

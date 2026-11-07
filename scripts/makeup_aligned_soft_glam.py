"""Single offline aligned Soft Glam comparison, using cached pretrained landmarks."""
import argparse
import json
from pathlib import Path
import sys
import time

import cv2
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import makeup_source_render as base
from scripts import makeup_visibility_pilot as visibility
from scripts import makeup_complete_look as previous
from scripts import makeup_alignment_pilot as alignment

GENERATOR="beautycore_aligned_soft_glam_pilot_v1"


def polygon(points):
    result=np.zeros((512,512),np.uint8)
    cv2.fillPoly(result,[np.rint(points).astype(np.int32)],1)
    return result.astype(bool)


def tapered_lash(canvas,points,width):
    points=np.asarray(points,np.float32)
    tangent=np.gradient(points,axis=0)
    normals=np.stack((-tangent[:,1],tangent[:,0]),axis=1)
    normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-6)
    taper=(1-np.linspace(0,1,len(points)))**1.3
    edge=normals*(width*.5*taper[:,None])
    outline=np.concatenate((points+edge,(points-edge)[::-1]))
    cv2.fillPoly(canvas,[np.rint(outline*6).astype(np.int32)],255,lineType=cv2.LINE_AA)


def fields_for(labels,points):
    geo=alignment.geometry(points,labels)
    old,_,_,_=base.geometry(labels)
    visible,_,mouth_guard=visibility.regions(labels)
    yy,xx=np.mgrid[:512,:512]
    skin=labels==1
    eye_interior=np.zeros((512,512),bool)
    for eye in geo["eyes"]:
        upper=np.asarray(eye["upper"]);lower=np.asarray(eye["lower"])
        eye_interior|=polygon(np.concatenate((upper,lower[::-1])))
    # Preserve all landmark-estimated eye interiors plus the eroded semantic eye core.
    semantic_core=cv2.erode(np.isin(labels,(4,5)).astype(np.uint8),np.ones((3,3),np.uint8))>0
    eye_safe=eye_interior|semantic_core
    # Only a semantic eye rim outside that protected core can receive liner/lash roots.
    eyelid_zone=(skin|np.isin(labels,(4,5)))&~eye_safe
    eye_soft=base.inside(eyelid_zone,1)
    fields={key:np.zeros((512,512),np.float32) for key in
            ("lid","crease","liner","lower","shimmer","highlight")}
    fields["blush"]=visible["blush"].copy()
    fields["brow"]=base.inside(np.isin(labels,(6,7)),1.5)
    fields["lip"]=old["lip"]*base.inside(polygon(geo["lip_outer"]),1.5)
    if (fields["lip"]>.5).sum()<50:raise ValueError("Insufficient aligned lip region")
    lashes=np.zeros((3072,3072),np.uint8)
    rng=np.random.default_rng(7301)
    face_center=np.where(np.isin(labels,(1,2)))[1].mean()
    mouth_top=float(np.where(np.isin(labels,(10,11,12)))[0].min())
    for eye in geo["eyes"]:
        upper=np.asarray(eye["upper"]);lower=np.asarray(eye["lower"])
        cx,cy=eye["center"];width=eye["width"]
        direction=-1 if cx<face_center else 1
        top_curve=np.interp(np.arange(512),upper[:,0],upper[:,1])[None,:]
        lower_curve=np.interp(np.arange(512),lower[:,0],lower[:,1])[None,:]
        brow_id=6 if np.abs(np.where(labels==6)[1].mean()-cx)<np.abs(np.where(labels==7)[1].mean()-cx) else 7
        by,bx=np.where(base.largest(labels==brow_id,20))
        columns=np.unique(bx)
        bottom=np.array([np.where(labels[:,x]==brow_id)[0].max() for x in columns])
        brow_curve=np.interp(np.arange(512),columns,bottom)[None,:]
        gap=np.maximum(top_curve-brow_curve-2,4)
        t=(top_curve-yy)/gap
        horizontal=np.clip(1-((xx-cx)/(width*.72))**2,0,1)**1.1
        band=(t>0)&(t<1)
        lid=np.exp(-.5*((t-.28)/.23)**2)*horizontal*band*base.inside(skin,1.5)
        outer=np.clip(.5+direction*(xx-cx)/width,.15,1)
        crease=np.exp(-.5*((t-.60)/.18)**2)*horizontal*outer*band*base.inside(skin,1.5)
        fields["lid"]=np.maximum(fields["lid"],lid.astype(np.float32))
        fields["crease"]=np.maximum(fields["crease"],crease.astype(np.float32))
        fields["shimmer"]=np.maximum(fields["shimmer"],
            (lid*np.exp(-.5*((xx-(cx-direction*.12*width))/(width*.27))**2)).astype(np.float32))
        d=top_curve-yy
        liner=np.exp(-.5*((d-.30)/.68)**2)*(d>=0)*(d<3)*horizontal*eye_soft
        fields["liner"]=np.maximum(fields["liner"],liner.astype(np.float32))
        dd=yy-lower_curve
        lower_field=np.exp(-.5*((dd-1)/1.5)**2)*(dd>0)*(dd<5)*horizontal*eye_soft
        fields["lower"]=np.maximum(fields["lower"],lower_field.astype(np.float32))
        gap_mouth=max(20,mouth_top-cy)
        high=np.exp(-.5*(((xx-(cx+direction*width*.48))/(width*.44))**2+
                        ((yy-(cy+.27*gap_mouth))/(gap_mouth*.14))**2))*base.inside(skin,2)
        high[high<.025]=0
        fields["highlight"]=np.maximum(fields["highlight"],high.astype(np.float32))
        for fraction in (.14,.23,.35,.47,.58,.67,.76,.84,.91):
            for fiber in range(3):
                f=float(np.clip(fraction+rng.uniform(-.012,.012),.08,.95))
                x=float(upper[0,0]+f*(upper[-1,0]-upper[0,0]))
                y=float(np.interp(x,upper[:,0],upper[:,1]))
                slope=(np.interp(x+1,upper[:,0],upper[:,1])-np.interp(x-1,upper[:,0],upper[:,1]))/2
                tangent=np.array([1.,slope]);tangent/=np.linalg.norm(tangent)
                normal=np.array([tangent[1],-tangent[0]])
                outer_weight=float(np.clip(.5+direction*(x-cx)/width,.1,1))
                length=width*(.055+.060*outer_weight)*rng.uniform(.76,1.15)
                fan=(fiber-1)*.18
                p0=np.array([x,y])+normal*.25
                p1=p0+normal*length*.64+tangent*(direction*.10+fan)*length
                p2=p0+normal*length+tangent*(direction*.35+fan)*length
                u=np.linspace(0,1,24)[:,None]
                curve=(1-u)**2*p0+2*(1-u)*u*p1+u**2*p2
                tapered_lash(lashes,curve,width*rng.uniform(.007,.011))
    fields["lashes"]=cv2.resize(lashes.astype(np.float32)/255,(512,512),interpolation=cv2.INTER_AREA)*eye_soft
    for key,field in fields.items():
        if key in ("liner","lower","lashes"):
            field[~eyelid_zone|mouth_guard]=0
        elif key not in ("brow","lip"):
            field[~skin|mouth_guard|eye_safe]=0
        field[field<.002]=0
    allowed=np.logical_or.reduce([field>0 for field in fields.values()])
    protected=~np.isin(labels,(1,4,5,6,7,11,12))|eye_safe
    if np.any(allowed&protected):raise RuntimeError("Aligned cosmetics overlap protected eye/anatomy")
    return fields,protected,allowed,eye_safe


def render(source,labels,points):
    if source.shape!=(512,512,3) or source.dtype!=np.uint8:
        raise ValueError("Expected original512 RGB8")
    fields,protected,allowed,eye_safe=fields_for(labels,points)
    original=base.lab(source);out=original.copy();p=previous.PROFILE
    base.tint(out,original,fields["lid"],p["lid_rgb"],p["lid_opacity"],28,-4)
    base.tint(out,original,fields["crease"],p["crease_rgb"],p["crease_opacity"],25,-8)
    base.tint(out,original,fields["blush"],p["blush_rgb"],p["blush_opacity"],30,-.8)
    base.tint(out,original,fields["lip"],p["lip_rgb"],p["lip_opacity"],35,("target",9))
    out[:,:,0]-=fields["liner"]*18+fields["lower"]*2
    brow=fields["brow"]*p["brow_strength"]
    out[:,:,0]-=brow*12;out[:,:,1:]*=(1-brow[:,:,None]*.12)
    out[:,:,0]+=fields["shimmer"]*3.8+fields["highlight"]*p["highlight_strength"]*4
    core=fields["lip"]>.5
    low=cv2.GaussianBlur(original[:,:,0],(0,0),1.8)
    q50,q95=np.quantile(low[core],(.5,.95))
    sheen=np.clip((low-q50)/max(2.,q95-q50),0,1)
    out[:,:,0]+=fields["lip"]*sheen*5
    distance=cv2.distanceTransform(np.isin(labels,(11,12)).astype(np.uint8),cv2.DIST_L2,5)
    out[:,:,0]-=fields["lip"]*np.clip(1-distance/3.5,0,1)*4
    delta=out-original;skin=labels==1
    out[:,:,0][skin]=original[:,:,0][skin]+np.clip(delta[:,:,0][skin],-15,5)
    norm=np.linalg.norm(delta[:,:,1:],axis=2)
    out[:,:,1:]=original[:,:,1:]+delta[:,:,1:]*np.minimum(1,38/np.maximum(norm,1e-6))[:,:,None]
    out,gamut=base.gamut_safe(out,allowed)
    rgb=np.clip(cv2.cvtColor(out,cv2.COLOR_LAB2RGB),0,1)
    alpha=fields["lashes"][:,:,None]*p["lash_strength"]
    rgb=rgb*(1-alpha)+np.array([.075,.050,.042],np.float32)*alpha
    result=source.copy();result[allowed]=np.rint(rgb[allowed]*255).clip(0,255).astype(np.uint8)
    changed=np.any(result!=source,axis=2)
    if np.any(changed&(~allowed|protected)):raise RuntimeError("Changed unrelated/protected pixels")
    return result,fields,{"changed_pixels":int(changed.sum()),"outside_support_changes":int((changed&~allowed).sum()),
         "protected_changes":int((changed&protected).sum()),"eye_interior_changes":int((changed&eye_safe).sum()),
         "semantic_eye_rim_changes":int((changed&np.isin(labels,(4,5))).sum()),
         "gamut_compressed_pixels":gamut,"regions":{key:int((changed&(v>0)).sum()) for key,v in fields.items()}}


def run(plan_path,alignment_dir,output):
    plan=alignment.load_plan(plan_path);alignment_dir=Path(alignment_dir);output=Path(output)
    if output.exists():raise ValueError("Preserve evidence; new render directory required")
    report=json.loads((alignment_dir/"report.json").read_text())
    review=json.loads((alignment_dir/"visual-review.json").read_text())
    if (report["plan_sha256"]!=base.digest(plan_path) or report["runner_sha256"]!=base.digest(Path(alignment.__file__))
        or review.get("decision")!="PASS_FOR_FOUR_CASE_PROTOTYPE_ONLY"
        or review.get("alignment_report_sha256")!=base.digest(alignment_dir/"report.json")):
        raise ValueError("Alignment review/provenance differs")
    output.mkdir(parents=True)
    records=[]
    for subject in plan["subjects"]:
        sid=subject["id"];source=base.read_rgb(alignment.owned(subject["source"]))
        old=base.read_rgb(alignment.owned(subject["previous"]))
        row=next(r for r in report["cases"] if r["id"]==sid)
        path=alignment_dir/row["landmarks"]
        if Path(row["landmarks"]).name!=row["landmarks"] or base.digest(path)!=row["sha256"]:
            raise ValueError("Cached landmarks differ")
        cached=json.loads(path.read_text())
        if cached["source_sha256"]!=subject["sha256"] or cached["model_sha256"]!=plan["model"]["sha256"] or cached["face_count"]!=1:
            raise ValueError("Cached landmark identity/model differs")
        labels=np.asarray(Image.open(alignment.owned(next(m for m in plan["maps"] if m["id"]==sid)["labels"]))).copy()
        started=time.perf_counter();result,fields,metrics=render(source,labels,cached["points"])
        filename=sid+"-aligned.png";Image.fromarray(result).save(output/filename)
        sheet=Image.new("RGB",(1536,550),"white");draw=ImageDraw.Draw(sheet)
        for x,title,rgb in ((0,"ORIGINAL",source),(512,"PREVIOUS - REJECTED",old),(1024,"ALIGNED PROTOTYPE - NOT DEPLOYED",result)):
            sheet.paste(Image.fromarray(rgb),(x,30));draw.text((x+6,9),title,fill="black")
        sheet.save(output/(sid+"-comparison.png"))
        record={"id":sid,"output":filename,"sha256":base.digest(output/filename),
                "metrics":metrics,"render_seconds":time.perf_counter()-started,"human_acceptance":"PENDING"}
        records.append(record);print("ALIGNED_SOFT_GLAM",len(records),"/4",sid,flush=True)
    base.write_json(output/"report.json",{"experiment":"MAKEUP-ALIGN-001","generator":GENERATOR,
      "production_enabled":False,"training":False,"lora_active":False,
      "new_model_inference":"Cached pretrained landmark detections; no image generator",
      "plan_sha256":base.digest(plan_path),"runner_sha256":base.digest(Path(__file__)),
      "alignment_report_sha256":base.digest(alignment_dir/"report.json"),"profile":previous.PROFILE,
      "palette_and_strengths":"EXACT_PREVIOUS_COMPLETE_PROFILE",
      "cases":records,"release_ready":False,
      "protection":"Semantic eyes may receive cosmetics only on a one-pixel outer rim outside both landmark eye polygons and eroded semantic eye core. All protected RGB exact.",
      "warning":"Geometry alignment is not a guarantee of reference-quality cosmetic rendering."})


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan",required=True,type=Path)
    parser.add_argument("--alignment",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args();run(args.plan,args.alignment,args.output)

"""Isolated AI-assisted Makeup rendering pilot; never imports a generative model."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
STYLES = ("natural_makeup", "soft_glam", "classic_red_lip")
PARSER_SHA = "c2bec795a8c243db71bd95be538fd62559003566466c71237e45c99b920f4b62"
PROFILE_KEYS = {"name", "lip_rgb", "lip_opacity", "lip_chroma_cap", "lip_lightness_cap",
                "shadow_rgb", "shadow_opacity", "shadow_darkening", "liner_opacity",
                "liner_darkening", "blush_rgb", "blush_opacity"}


def digest(path):
    h=sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def read_rgb(path):
    with Image.open(path) as im:
        return np.array(im.convert("RGB"))


def lab(rgb):
    return cv2.cvtColor(rgb.astype(np.float32)/255.0,cv2.COLOR_RGB2LAB)



def linear_rgb(values):
    """Unclipped inverse Lab/D65, following OpenCV color-conversion constants."""
    values=np.asarray(values,dtype=np.float32)
    fy=(values[...,0]+16)/116
    terms=np.stack((fy+values[...,1]/500,fy,fy-values[...,2]/200),axis=-1)
    xyz=np.where(terms>6/29,terms**3,(terms-16/116)/7.787)
    xyz*=np.array([0.950456,1.0,1.088754],np.float32)
    flat=xyz.reshape(-1,1,3)
    return cv2.cvtColor(flat,cv2.COLOR_XYZ2RGB).reshape(values.shape)


def gamut_safe(values,allowed):
    """Compress only out-of-gamut chroma; keep hue direction and local lightness."""
    result=values.copy()
    result[:,:,0]=np.clip(result[:,:,0],0,100)
    rgb=linear_rgb(result)
    bad=allowed & np.any((rgb < -1e-5)|(rgb > 1+1e-5),axis=2)
    if bad.any():
        pixels=result[bad].copy()
        low=np.zeros(len(pixels),np.float32)
        high=np.ones(len(pixels),np.float32)
        for _ in range(12):
            middle=(low+high)/2
            candidate=pixels.copy()
            candidate[:,1:]*=middle[:,None]
            check=linear_rgb(candidate)
            valid=np.all((check>=0)&(check<=1),axis=1)
            low=np.where(valid,middle,low)
            high=np.where(valid,high,middle)
        pixels[:,1:]*=low[:,None]
        result[bad]=pixels
    remaining=allowed & np.any((linear_rgb(result)<-1e-5)|(linear_rgb(result)>1+1e-5),axis=2)
    if remaining.any():
        raise RuntimeError("Unable to map cosmetic color into RGB gamut")
    return result,int(bad.sum())

def owned(relative):
    path=(ROOT/relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Input path escapes project")
    return path


def profile_check(profile):
    if set(profile)!=PROFILE_KEYS or not isinstance(profile["name"],str):
        raise ValueError("Unexpected cosmetic profile fields")
    for key in ("lip_rgb","shadow_rgb","blush_rgb"):
        value=profile[key]
        if len(value)!=3 or any(type(v) is not int or not 0<=v<=255 for v in value):
            raise ValueError("Invalid pigment RGB")
    limits={"lip_opacity":1,"shadow_opacity":1,"liner_opacity":1,"blush_opacity":0.2,
            "lip_chroma_cap":50,"lip_lightness_cap":30,"shadow_darkening":10,"liner_darkening":25}
    for key,maximum in limits.items():
        value=profile[key]
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not np.isfinite(value) or not 0<=value<=maximum:
            raise ValueError("Invalid cosmetic strength")


def load_plan(path):
    plan=json.loads(Path(path).read_text(encoding="utf-8"))
    if (plan.get("experiment")!="MAKEUP-RENDER-001" or plan.get("production_enabled") is not False
            or plan.get("training") is not False or plan.get("lora_active") is not False
            or plan.get("project_trained_generator_used") is not False
            or plan.get("generator")!="beautycore_makeup_render_pilot_v1"
            or plan.get("case_count")!=12 or len(plan["subjects"])!=4
            or len({r["id"] for r in plan["subjects"]})!=4
            or set(plan["profiles"])!=set(STYLES)):
        raise ValueError("Frozen source-renderer pilot scope differs")
    for profile in plan["profiles"].values():
        profile_check(profile)
    for row in plan["subjects"]:
        if Path(row["id"]).name!=row["id"] or digest(owned(row["source"]))!=row["sha256"]:
            raise ValueError("Source identity/path/hash differs")
    if plan["parser"]["files"].get("model.safetensors")!=PARSER_SHA:
        raise ValueError("Unexpected parser weights")
    return plan


def largest(binary,minimum):
    count, components, stats, _=cv2.connectedComponentsWithStats(binary.astype(np.uint8),8)
    if count<2:
        raise ValueError("Missing facial component")
    index=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))
    if stats[index,cv2.CC_STAT_AREA]<minimum:
        raise ValueError("Facial component too small")
    return components==index


def inside(binary,width=2):
    distance=cv2.distanceTransform(binary.astype(np.uint8),cv2.DIST_L2,5)
    t=np.clip(distance/width,0,1)
    return (t*t*(3-2*t)).astype(np.float32)


def geometry(labels):
    if (labels.ndim!=2 or labels.shape!=(512,512) or not np.issubdtype(labels.dtype,np.integer)
            or labels.min()<0 or labels.max()>18):
        raise ValueError("Expected 512-square parser labels 0..18")
    skin=labels==1
    if skin.sum()<10000:
        raise ValueError("Insufficient facial skin")
    face=np.isin(labels,(1,2,3,4,5,6,7,10,11,12))
    main=largest(face,15000)
    if main.sum()/face.sum()<0.97:
        raise ValueError("Ambiguous disconnected face regions")
    lips=np.isin(labels,(11,12)) & main
    mouth=np.isin(labels,(10,11,12)) & main
    if lips.sum()<100 or mouth.sum()<150:
        raise ValueError("Missing reliable lip/mouth regions")
    mouth_y=int(np.where(mouth)[0].min())
    yy,xx=np.mgrid[:512,:512]
    shadow=np.zeros((512,512),np.float32)
    liner=np.zeros_like(shadow)
    cheeks=np.zeros_like(shadow)
    summaries=[]
    # Source coordinates only; no hand-set per-person eye/cheek positions.
    for eye_label,brow_label in ((4,6),(5,7)):
        eye=largest(labels==eye_label,20)
        brow=largest(labels==brow_label,20)
        ey,ex=np.where(eye);by,bx=np.where(brow)
        x0,x1=int(ex.min()),int(ex.max())
        width=x1-x0+1
        if not 18<=width<=120:
            raise ValueError("Unsupported eye scale")
        columns=np.arange(x0,x1+1)
        upper=np.array([np.where(eye[:,x])[0].min() for x in columns],np.float32)
        upper_curve=np.interp(np.arange(512),columns,upper)[None,:]
        bcols=np.unique(bx)
        lower=np.array([np.where(brow[:,x])[0].max() for x in bcols],np.float32)
        brow_curve=np.interp(np.arange(512),bcols,lower)[None,:]
        gap=np.clip(upper_curve-brow_curve-2,6,width*0.50)
        t=(upper_curve-yy-1)/gap
        cx=float(ex.mean());cy=float(ey.mean())
        horizontal=np.clip(1-((xx-cx)/(width*0.68))**2,0,1)**1.4
        vertical=np.sin(np.pi*np.clip(t,0,1))**1.15
        field=horizontal*vertical*(t>0)*(t<1)
        field*=inside(skin & main,2.0)
        shadow=np.maximum(shadow,field.astype(np.float32))
        d=upper_curve-yy
        line=np.exp(-0.5*((d-0.8)/0.85)**2)*horizontal*(d>=0)*(d<=4)
        line*=inside(skin & main,1.3)
        liner=np.maximum(liner,line.astype(np.float32))
        # Locate cheek below/outside the actual eye, above the mouth.
        if mouth_y<=ey.max()+12:
            raise ValueError("Unsupported eye/mouth arrangement")
        outward=-1 if cx<np.where(main)[1].mean() else 1
        cheek_x=cx+outward*width*0.26
        cheek_y=float(ey.max())+0.53*(mouth_y-float(ey.max()))
        cheek=np.exp(-0.5*(((xx-cheek_x)/(width*0.48))**2+
                          ((yy-cheek_y)/max(12,(mouth_y-ey.max())*0.28))**2))
        cheek[cheek<0.025]=0
        cheek*=inside(skin & main,4)
        near_feature=cv2.dilate(np.isin(labels,(3,4,5,6,7,10,11,12)).astype(np.uint8),
                               cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)))>0
        cheek[near_feature]=0
        cheeks=np.maximum(cheeks,cheek.astype(np.float32))
        summaries.append({"eye_label":eye_label,"eye_center":[cx,cy],"eye_width":width,
                          "cheek_center":[cheek_x,cheek_y]})
    centers=sorted([s["eye_center"] for s in summaries])
    dx=centers[1][0]-centers[0][0]
    if dx<40 or abs(centers[1][1]-centers[0][1])/dx>0.25:
        raise ValueError("Unsupported eye alignment/tilt")
    protected=~np.isin(labels,(1,11,12))
    fields={"lip":inside(lips,1.8),"shadow":shadow,"liner":liner,"blush":cheeks}
    for key,field in fields.items():
        field[protected]=0
        field[field<0.002]=0
        if not np.isfinite(field).all() or (field>0).sum()<25:
            raise ValueError("Missing cosmetic region: "+key)
    allowed=np.logical_or.reduce([field>0 for field in fields.values()])
    return fields,protected,allowed,summaries


def tint(out,original,field,color,opacity,chroma_cap,lightness):
    core=field>max(0.1,float(field.max())*0.45)
    if core.sum()<20:
        raise ValueError("Insufficient pigment sampling region")
    center=np.median(original[core],axis=0)
    target=lab(np.array([[color]],np.uint8))[0,0]
    delta=target[1:]-center[1:]
    norm=float(np.linalg.norm(delta))
    if norm>chroma_cap:
        delta*=chroma_cap/norm
    alpha=field*opacity
    out[:,:,1:]+=alpha[:,:,None]*delta
    if isinstance(lightness,tuple):
        cap=lightness[1]
        shift=float(np.clip(target[0]-center[0],-cap,cap))
    else:
        shift=float(lightness)
    out[:,:,0]+=alpha*shift
    return {"source_core_lab":center.tolist(),"chroma_offset":delta.tolist(),
            "lightness_offset":shift,"maximum_alpha":float(alpha.max())}


def render(source,labels,profile):
    profile_check(profile)
    if source.shape!=(512,512,3) or source.dtype!=np.uint8:
        raise ValueError("Expected original 512-square uint8 RGB")
    fields,protected,allowed,placements=geometry(labels)
    allowed=np.logical_or.reduce([
        fields[key]*profile[key+"_opacity"]>0 for key in ("lip","shadow","liner","blush")])
    original=lab(source);out=original.copy()
    stats={}
    stats["lip"]=tint(out,original,fields["lip"],profile["lip_rgb"],profile["lip_opacity"],
                      profile["lip_chroma_cap"],("target",profile["lip_lightness_cap"]))
    stats["shadow"]=tint(out,original,fields["shadow"],profile["shadow_rgb"],profile["shadow_opacity"],
                         28.0,-profile["shadow_darkening"])
    stats["blush"]=tint(out,original,fields["blush"],profile["blush_rgb"],profile["blush_opacity"],18.0,0.0)
    # Liner only darkens source eyelid skin; does not redraw eyes or lashes.
    out[:,:,0]-=fields["liner"]*profile["liner_opacity"]*profile["liner_darkening"]
    out,gamut_pixels=gamut_safe(out,allowed)
    converted=cv2.cvtColor(out,cv2.COLOR_LAB2RGB)
    result=source.copy()
    result[allowed]=np.rint(np.clip(converted,0,1)*255).astype(np.uint8)[allowed]
    changed=np.any(result!=source,axis=2)
    if np.any(changed & (~allowed | protected)):
        raise RuntimeError("Changed protected/noncosmetic source pixels")
    return result,fields,{
        "changed_pixels":int(changed.sum()),
        "outside_cosmetic_changed_pixels":int((changed & ~allowed).sum()),
        "protected_changed_pixels":int((changed & protected).sum()),
        "placements":placements,"pigments":stats,
        "gamut_compressed_pixels":gamut_pixels,
        "region_changed_pixels":{key:int((changed & (field>0)).sum()) for key,field in fields.items()},
        "limit":"Pixel preservation is not calibrated region accuracy or visual acceptance.",
    }


def overlay(source,fields):
    preview=source.astype(np.float32).copy()
    for key,color in (("lip",[245,70,70]),("shadow",[70,140,245]),("liner",[230,180,0]),("blush",[70,220,120])):
        alpha=fields[key][:,:,None]*0.6
        preview=preview*(1-alpha)+np.array(color)*alpha
    return np.rint(preview).clip(0,255).astype(np.uint8)


def write_json(path,value):
    Path(path).write_text(json.dumps(value,indent=2)+"\n",encoding="utf-8")


def prepare(plan_path,output):
    plan=load_plan(plan_path);output=Path(output)
    if output.exists():
        raise ValueError("New pilot directory required")
    parser_dir=owned(plan["parser"]["directory"])
    for name,expected in plan["parser"]["files"].items():
        if Path(name).name!=name or digest(parser_dir/name)!=expected:
            raise ValueError("Cached parser file differs")
    output.mkdir(parents=True)
    shutil.copyfile(plan_path,output/"plan.json")
    import torch
    from transformers import SegformerForSemanticSegmentation,SegformerImageProcessor
    torch.set_num_threads(4)
    started=time.perf_counter()
    processor=SegformerImageProcessor.from_pretrained(str(parser_dir),local_files_only=True)
    model=SegformerForSemanticSegmentation.from_pretrained(str(parser_dir),local_files_only=True,use_safetensors=True).eval()
    load_seconds=time.perf_counter()-started
    prepared=[]
    sheet=Image.new("RGB",(2048,550),"white");draw=ImageDraw.Draw(sheet)
    for i,subject in enumerate(plan["subjects"]):
        rgb=read_rgb(owned(subject["source"]))
        with torch.inference_mode():
            inputs=processor(images=Image.fromarray(rgb),return_tensors="pt")
            logits=model(**inputs).logits
            labels=torch.nn.functional.interpolate(logits,size=(512,512),mode="bilinear",align_corners=False).argmax(1)[0].byte().numpy()
        fields,_,allowed,placements=geometry(labels)
        p=output/(subject["id"]+"-labels.png")
        Image.fromarray(labels).save(p)
        Image.fromarray(allowed.astype(np.uint8)*255).save(output/(subject["id"]+"-allowed.png"))
        np.savez_compressed(output/(subject["id"]+"-fields.npz"),**fields)
        region_image=overlay(rgb,fields)
        Image.fromarray(region_image).save(output/(subject["id"]+"-regions.png"))
        sheet.paste(Image.fromarray(region_image),(i*512,28))
        draw.text((i*512+6,6),subject["id"]+" SOURCE REGIONS / EXPERIMENTAL",fill="black")
        prepared.append({"id":subject["id"],"labels":p.name,"labels_sha256":digest(p),
                         "allowed":subject["id"]+"-allowed.png","placements":placements})
        print("REGIONS",subject["id"],flush=True)
    sheet.save(output/"region-review.png")
    write_json(output/"prepared.json",{"plan_sha256":digest(plan_path),"subjects":prepared,"parser_load_seconds":load_seconds,
                                      "mask_review":"PENDING","production_enabled":False})


def apply(plan_path,output):
    plan=load_plan(plan_path);output=Path(output)
    prepared=json.loads((output/"prepared.json").read_text(encoding="utf-8"))
    if (output/"report.json").exists() or list(output.glob("*-rendered.png")):
        raise ValueError("Do not overwrite complete/partial rendering evidence")
    if digest(plan_path)!=prepared["plan_sha256"] or digest(output/"plan.json")!=prepared["plan_sha256"]:
        raise ValueError("Prepared plan differs")
    records=[]
    for subject in plan["subjects"]:
        source=read_rgb(owned(subject["source"]))
        item=next(r for r in prepared["subjects"] if r["id"]==subject["id"])
        path=(output/item["labels"]).resolve()
        if not path.is_relative_to(output.resolve()) or digest(path)!=item["labels_sha256"]:
            raise ValueError("Prepared labels differ")
        labels=np.asarray(Image.open(path)).copy()
        sheet=Image.new("RGB",(2048,550),"white");draw=ImageDraw.Draw(sheet)
        sheet.paste(Image.fromarray(source),(0,28));draw.text((7,7),"ORIGINAL "+subject["id"],fill="black")
        for i,style in enumerate(STYLES,1):
            started=time.perf_counter()
            result,fields,metrics=render(source,labels,plan["profiles"][style])
            elapsed=time.perf_counter()-started
            filename=subject["id"]+"-"+style+"-rendered.png"
            Image.fromarray(result).save(output/filename)
            sheet.paste(Image.fromarray(result),(i*512,28))
            draw.text((i*512+5,7),plan["profiles"][style]["name"]+" / AI-ASSISTED PILOT",fill="black")
            record={"subject_id":subject["id"],"style_id":style,"output":filename,"sha256":digest(output/filename),
                    "source_sha256":subject["sha256"],"render_seconds_excluding_file_io":elapsed,"metrics":metrics,
                    "generator":plan["generator"],"lora_active":False,"project_trained_generator_used":False,
                    "human_approval":"PENDING"}
            records.append(record)
            print("RENDER",len(records),"/12",subject["id"],style,metrics["changed_pixels"],flush=True)
        sheet.save(output/(subject["id"]+"-comparison.png"))
    write_json(output/"report.json",{"experiment":plan["experiment"],"plan_sha256":digest(plan_path),
               "runner_sha256":digest(Path(__file__)),"generator":plan["generator"],"production_enabled":False,
               "training":False,"gpu_generation_calls":0,"lora_active":False,"project_trained_generator_used":False,
               "cases":records,"limits":plan["limits"],"status":"COMPLETE_REQUIRES_VISUAL_REVIEW"})
    return records


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--stage",choices=("prepare","apply"),required=True)
    args=parser.parse_args()
    (prepare if args.stage=="prepare" else apply)(args.plan,args.output)

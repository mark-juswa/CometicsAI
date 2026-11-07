"""Offline alignment gate for Makeup; no serving changes or image generation."""
import argparse
import importlib.metadata
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

CHAINS={
 "right_upper":[33,246,161,160,159,158,157,173,133],
 "right_lower":[33,7,163,144,145,153,154,155,133],
 "left_upper":[362,398,384,385,386,387,388,466,263],
 "left_lower":[362,382,381,380,374,373,390,249,263],
 "right_brow_lower":[46,53,52,65,55],"right_brow_upper":[70,63,105,66,107],
 "left_brow_lower":[276,283,282,295,285],"left_brow_upper":[300,293,334,296,336],
 "lip_outer":[61,185,40,39,37,0,267,269,270,409,291,375,321,405,314,17,84,181,91,146],
 "lip_inner":[78,191,80,81,82,13,312,311,310,415,308,324,318,402,317,14,87,178,88,95]
}


def owned(path):
    result=(ROOT/path).resolve()
    if not result.is_relative_to(ROOT):raise ValueError("Path escapes project")
    return result


def load_plan(path):
    plan=json.loads(Path(path).read_text(encoding="utf-8"))
    if (plan.get("experiment")!="MAKEUP-ALIGN-001" or plan.get("case_count")!=4
        or len(plan.get("subjects",[]))!=4 or len({s["id"] for s in plan["subjects"]})!=4
        or plan.get("chains")!=CHAINS or plan.get("mediapipe")!="0.10.33"
        or any(plan.get(k) is not False for k in ("training","lora_active","production_enabled"))
        or plan.get("new_model_inference")!="PRETRAINED_LANDMARK_DETECTION_ONLY"):
        raise ValueError("Offline alignment scope differs")
    if base.digest(owned(plan["model"]["path"]))!=plan["model"]["sha256"]:
        raise ValueError("Landmark model differs")
    if len(plan["maps"])!=4 or {m["id"] for m in plan["maps"]}!={s["id"] for s in plan["subjects"]}:
        raise ValueError("Map identities differ")
    for source in plan["subjects"]:
        for name,hash_key in (("source","sha256"),("previous","previous_sha256")):
            if base.digest(owned(source[name]))!=source[hash_key]:
                raise ValueError("Frozen source/previous image differs")
    for mapping in plan["maps"]:
        if base.digest(owned(mapping["labels"]))!=mapping["sha256"]:
            raise ValueError("Source labels differ")
    for helper in plan["helpers"]:
        if base.digest(owned(helper["path"]))!=helper["sha256"]:
            raise ValueError("Previous helper differs")
    return plan


def geometry(points,labels):
    base.geometry(labels)
    points=np.asarray(points,dtype=np.float32)
    if points.shape!=(478,3) or not np.isfinite(points).all():
        raise ValueError("Expected 478 finite normalized face landmarks")
    if (points[:,:2]<0).any() or (points[:,:2]>1).any() or (np.abs(points[:,2])>2).any():
        raise ValueError("Out of frame/invalid landmarks")
    pixel=points[:,:2]*512
    eyes=[];used=set()
    for side in ("right","left"):
        upper=pixel[CHAINS[side+"_upper"]]
        lower=pixel[CHAINS[side+"_lower"]]
        upper=upper[np.argsort(upper[:,0])]
        lower=lower[np.argsort(lower[:,0])]
        center=np.vstack((upper,lower)).mean(axis=0)
        width=float(upper[-1,0]-upper[0,0])
        candidates=[]
        for label in (4,5):
            y,x=np.where(labels==label)
            candidates.append((float(np.linalg.norm(np.array([x.mean(),y.mean()])-center)),label))
        distance,label=min(candidates)
        if label in used or not 18<=width<=120 or distance>max(14,width*.3):
            raise ValueError("Eye/semantic alignment ambiguous")
        used.add(label)
        xs=np.linspace(upper[0,0]+.15*width,upper[-1,0]-.15*width,80)
        gap=np.interp(xs,lower[:,0],lower[:,1])-np.interp(xs,upper[:,0],upper[:,1])
        if float(np.median(gap))<3 or float(np.max(gap))>width*.7:
            raise ValueError("Unsupported closed/ambiguous eye")
        brow_lower=pixel[CHAINS[side+"_brow_lower"]]
        brow_lower=brow_lower[np.argsort(brow_lower[:,0])]
        brow_upper=pixel[CHAINS[side+"_brow_upper"]]
        bx=float(brow_lower[:,0].mean())
        if abs(bx-center[0])>width*.6 or float(brow_lower[:,1].mean())>=center[1]:
            raise ValueError("Brow/eye alignment invalid")
        ey,ex=np.where(base.largest(labels==label,20))
        columns=np.unique(ex)
        old_top=np.array([np.where(labels[:,x]==label)[0].min() for x in columns],np.float32)
        samples=np.linspace(max(columns.min(),upper[0,0]),min(columns.max(),upper[-1,0]),80)
        differences=np.interp(samples,columns,old_top)-np.interp(samples,upper[:,0],upper[:,1])
        eyes.append({"side":side,"label":label,"center":center.tolist(),"width":width,
          "upper":upper.tolist(),"lower":lower.tolist(),"brow_lower":brow_lower.tolist(),
          "brow_upper":brow_upper.tolist(),
          "parser_minus_landmark_upper_y":{"mean":float(differences.mean()),
              "median":float(np.median(differences)),"mean_absolute":float(np.abs(differences).mean())}})
    eyes.sort(key=lambda e:e["center"][0])
    delta=np.array(eyes[1]["center"])-eyes[0]["center"]
    if delta[0]<40 or abs(delta[1]/delta[0])>.25:
        raise ValueError("Unsupported face tilt")
    mouth=pixel[CHAINS["lip_outer"]]
    my,mx=np.where(np.isin(labels,(10,11,12)))
    if np.linalg.norm(mouth.mean(axis=0)-[mx.mean(),my.mean()])>25:
        raise ValueError("Mouth/semantic alignment invalid")
    return {"eyes":eyes,"lip_outer":mouth.tolist(),"lip_inner":pixel[CHAINS["lip_inner"]].tolist()}


def detect(plan_path,output):
    plan=load_plan(plan_path);output=Path(output)
    if output.exists():raise ValueError("Preserve evidence; new alignment directory required")
    if importlib.metadata.version("mediapipe")!=plan["mediapipe"]:
        raise ValueError("MediaPipe version differs")
    output.mkdir(parents=True);base.write_json(output/"plan.json",plan)
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    options=vision.FaceLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(owned(plan["model"]["path"])),
                                        delegate=python.BaseOptions.Delegate.CPU),
        running_mode=vision.RunningMode.IMAGE,num_faces=2,
        min_face_detection_confidence=.6,min_face_presence_confidence=.6)
    records=[]
    with vision.FaceLandmarker.create_from_options(options) as detector:
        for row in plan["subjects"]:
            source=base.read_rgb(owned(row["source"]));sid=row["id"]
            labels=np.asarray(Image.open(owned(next(m for m in plan["maps"] if m["id"]==sid)["labels"]))).copy()
            started=time.perf_counter()
            result=detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB,data=np.ascontiguousarray(source)))
            seconds=time.perf_counter()-started
            if len(result.face_landmarks)!=1:raise ValueError("Expected exactly one detected face")
            points=[[p.x,p.y,p.z] for p in result.face_landmarks[0]]
            geom=geometry(points,labels)
            path=output/(sid+"-landmarks.json")
            base.write_json(path,{"id":sid,"source_sha256":row["sha256"],"model_sha256":plan["model"]["sha256"],
                                  "points":points,"geometry":geom,"face_count":1,
                                  "mediapipe":plan["mediapipe"],"cpu_seconds":seconds})
            overlay=source.copy()
            for eye in geom["eyes"]:
                label=eye["label"];ys,xs=np.where(labels==label)
                cols=np.unique(xs)
                old=np.array([[x,np.where(labels[:,x]==label)[0].min()] for x in cols],np.int32)
                cv2.polylines(overlay,[old],False,(255,75,50),1,cv2.LINE_AA)
                for name,color in (("upper",(60,255,100)),("lower",(60,200,230)),("brow_lower",(255,220,60))):
                    cv2.polylines(overlay,[np.rint(eye[name]).astype(np.int32)],False,color,1,cv2.LINE_AA)
            for name in ("lip_outer","lip_inner"):
                cv2.polylines(overlay,[np.rint(geom[name]).astype(np.int32)],True,(240,100,220),1,cv2.LINE_AA)
            Image.fromarray(overlay).save(output/(sid+"-alignment.png"))
            # Nearest-neighbor enlargement of actual source pixels for placement review.
            combined=Image.new("RGB",(1200,410),"white");draw=ImageDraw.Draw(combined)
            for i,eye in enumerate(geom["eyes"]):
                cx,cy=eye["center"];w=eye["width"]
                box=(int(cx-.75*w),int(cy-.6*w),int(cx+.75*w),int(cy+.4*w))
                before=Image.fromarray(source).crop(box).resize((300,300),Image.Resampling.NEAREST)
                after=Image.fromarray(overlay).crop(box).resize((300,300),Image.Resampling.NEAREST)
                combined.paste(before,(i*600,40));combined.paste(after,(i*600+300,40))
                draw.text((i*600+5,10),"SOURCE / PARSER RED / LANDMARK UPPER GREEN",fill="black")
            combined.save(output/(sid+"-eye-alignment.png"))
            records.append({"id":sid,"landmarks":path.name,"sha256":base.digest(path),
                            "cpu_seconds":seconds,"eyes":[e["parser_minus_landmark_upper_y"] for e in geom["eyes"]],
                            "geometry_guard":"PASS","visual_review":"PENDING"})
            print("ALIGNMENT",len(records),"/4",sid,round(seconds,3),"seconds",flush=True)
    base.write_json(output/"report.json",{"experiment":plan["experiment"],
        "plan_sha256":base.digest(plan_path),"runner_sha256":base.digest(Path(__file__)),
        "model_sha256":plan["model"]["sha256"],"production_enabled":False,
        "new_model_inference":"PRETRAINED_LANDMARK_DETECTION_ONLY","training":False,"lora_active":False,
        "cases":records,"warning":"Detection/geometry guards do not establish accurate placement or cosmetic realism."})


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan",required=True,type=Path);parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args();detect(args.plan,args.output)

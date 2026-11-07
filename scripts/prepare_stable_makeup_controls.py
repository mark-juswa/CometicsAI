"""Prepare four frozen structural controls locally; never changes BeautyCore serving."""
import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def prepare(workspace):
    workspace=Path(workspace).resolve()
    if not workspace.is_relative_to(ROOT):raise ValueError("Workspace escapes project")
    out=workspace/"inputs"
    if out.exists():raise ValueError("Do not overwrite prepared controls")
    sys.path[:0]=[str(workspace/"runtime"/name) for name in ("stable","spiga","facelib")]
    import numpy as np
    import torch
    import cv2
    import PIL
    from PIL import Image
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.path import Path as PlotPath
    from facelib import FaceDetector
    from spiga.inference.config import ModelConfig
    from spiga.inference.framework import SPIGAFramework
    torch.set_num_threads(4)
    config=ModelConfig("300wpublic",load_model_url=False)
    config.model_weights_path=str(workspace/"assets")
    processor=SPIGAFramework(config)
    detector=FaceDetector(device=torch.device("cpu"),verbose=False)
    original=workspace/"vendor/stable/spiga_draw.py"
    parsed=ast.parse(original.read_text(encoding="utf-8"))
    names={"get_patch","conditioning_from_landmarks","parse_landmarks","bbox_from_landmarks"}
    selected=[node for node in parsed.body if isinstance(node,ast.FunctionDef) and node.name in names]
    if len(selected)!=4:raise ValueError("Upstream conditioning functions differ")
    scope={"np":np,"plt":plt,"patches":patches,"Path":PlotPath,"PIL":PIL}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(original),"exec"),scope)
    source_plan=json.loads((ROOT/"data/makeup/MAKEUP-COMPLETE-001/plan.json").read_text())
    out.mkdir()
    records=[]
    for row in source_plan["subjects"]:
        source=(ROOT/row["source"]).resolve()
        if not source.is_relative_to(ROOT) or digest(source)!=row["sha256"]:
            raise ValueError("Frozen portrait differs")
        image=Image.open(source).convert("RGB")
        if image.size!=(512,512):raise ValueError("Expected512source")
        bgr=cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR)
        with torch.inference_mode():
            boxes,scores,_=detector.detect_faces(bgr)
            if len(boxes)!=1:raise ValueError("Exactly one RetinaFace detection required")
            box=boxes[0].cpu().tolist()
            first=processor.inference(bgr,[[box[0],box[1],box[2]-box[0],box[3]-box[1]]])
            refined=scope["bbox_from_landmarks"](np.asarray(first["landmarks"]))
            features=processor.inference(bgr,refined)
        landmarks=np.asarray(features["landmarks"],np.float32)
        if landmarks.shape!=(1,68,2) or not np.isfinite(landmarks).all():
            raise ValueError("SPIGA68point control invalid")
        pose=scope["conditioning_from_landmarks"](landmarks.tolist(),size=512)
        sid=row["id"]
        image.save(out/(sid+"-source.png"));pose.save(out/(sid+"-control.png"))
        record={**row,"trial_source":sid+"-source.png","trial_source_sha256":digest(out/(sid+"-source.png")),
          "control":sid+"-control.png","control_sha256":digest(out/(sid+"-control.png")),
          "landmarks":landmarks.tolist(),"retina_score":float(scores[0].cpu()),
          "structural_method":"Author RetinaFace + SPIGA300wpublic, two SPIGA passes and unchanged conditioning drawing functions"}
        records.append(record);print("STRUCTURAL_CONTROL",len(records),"/4",sid,flush=True)
    reference=Path("C:/Users/Gigabyte/AppData/Local/Temp")/source_plan["reference"]["filename"]
    if digest(reference)!=source_plan["reference"]["sha256"]:raise ValueError("User reference changed")
    full=Image.open(reference).convert("RGB")
    crop=(350,350,1350,1350)
    if full.size!=(1600,2399):raise ValueError("Reference dimensions differ")
    full.crop(crop).resize((512,512),Image.Resampling.LANCZOS).save(out/"makeup-reference.png")
    receipt={"subjects":records,"reference":{"file":"makeup-reference.png","sha256":digest(out/"makeup-reference.png"),
      "original_sha256":digest(reference),"original_size":list(full.size),"crop":list(crop),
      "use":"User provided visual target; model evaluation reference only, no training"},
      "torch":torch.__version__,"device":"cpu","new_training":False,"image_generation_run":False,
      "spiga_sha256":digest(workspace/"assets/spiga_300wpublic.pt"),
      "retina_sha256":digest(workspace/"assets/mobilenet.pth"),
      "drawing_source_sha256":digest(original)}
    (workspace/"controls-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--workspace",type=Path,required=True)
    args=parser.parse_args();prepare(args.workspace)

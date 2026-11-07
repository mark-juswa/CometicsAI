"""Package the isolated pretrained trial; no cloud changes and no model inference."""
import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path
import shutil
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def jsonwrite(path,value):
    Path(path).write_text(json.dumps(value,indent=2)+"\n",encoding="utf-8")


def build(workspace):
    workspace=Path(workspace).resolve()
    if not workspace.is_relative_to(ROOT):raise ValueError("Project workspace required")
    package=workspace/"package"
    if package.exists():raise ValueError("Preserve old package")
    controls=json.loads((workspace/"controls-receipt.json").read_text())
    if len(controls["subjects"])!=4:raise ValueError("Four CPU controls required")
    package.mkdir()
    manifest=json.loads((workspace/"source-manifest.json").read_text())
    stable=next(r for r in manifest if r["alias"]=="stable")
    for row in stable["files"]:
        name=row["path"]
        if not (name.startswith(("diffusers/","detail_encoder/")) or name in ("pipeline_sd15.py","LICENSE","README.md")):continue
        source=workspace/"vendor/stable"/name
        if digest(source)!=row["sha256"]:raise ValueError("Upstream source differs")
        target=package/"vendor/stable"/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    encoder=package/"vendor/stable/detail_encoder/encoder_plus.py"
    before=encoder.read_text(encoding="utf-8")
    old="""        clip_encoder = OriginalCLIPVisionModel.from_pretrained(image_encoder_path)
        self.image_encoder = CLIPVisionModel(clip_encoder.config)
        state_dict = clip_encoder.state_dict()
        self.image_encoder.load_state_dict(state_dict, strict=False)
        self.image_encoder.to(self.device, self.dtype)
        del clip_encoder"""
    new="""        from transformers import CLIPConfig
        vision_config = CLIPConfig.from_pretrained(image_encoder_path, local_files_only=True).vision_config
        self.image_encoder = CLIPVisionModel(vision_config)
        self.image_encoder.to(self.device, self.dtype)
        # Entire trained encoder state must be loaded with strict=True by the trial."""
    if before.count(old)!=1:raise ValueError("Encoder initialization patch no longer matches")
    encoder.write_text(before.replace(old,new),encoding="utf-8")
    jsonwrite(package/"source-patches.json",{"source_commit":stable["commit"],
      "original_encoder_sha256":sha256(before.encode()).hexdigest(),"patched_encoder_sha256":digest(encoder),
      "reason":"Complete author checkpoint includes image_encoder/resampler/SSR state. Instantiate config only, then require strict full trained state loading; do not download unused original CLIP weights.",
      "entry":"New bounded runner imports root pipeline; broken upstream infer_kps.py is not executed."})
    (package/"clip").mkdir();shutil.copyfile(workspace/"assets/clip-config.json",package/"clip/config.json")
    (package/"inputs").mkdir()
    cases=[]
    for row in controls["subjects"]:
        for name,key in (("trial_source","trial_source_sha256"),("control","control_sha256")):
            source=workspace/"inputs"/row[name]
            if digest(source)!=row[key]:raise ValueError("Prepared control/source changed")
            shutil.copyfile(source,package/"inputs"/row[name])
        cases.append({"id":row["id"],"source":"inputs/"+row["trial_source"],"source_sha256":row["trial_source_sha256"],
                      "control":"inputs/"+row["control"],"control_sha256":row["control_sha256"]})
    reference=workspace/"inputs"/controls["reference"]["file"]
    if digest(reference)!=controls["reference"]["sha256"]:raise ValueError("Reference changed")
    shutil.copyfile(reference,package/"inputs/makeup-reference.png")
    shutil.copyfile(workspace/"controls-receipt.json",package/"controls-receipt.json")
    for name in ("stable_makeup_trial.py","stable_makeup_bootstrap.py"):
        shutil.copyfile(ROOT/"scripts"/name,package/name)
    shutil.copyfile(workspace/"requirements-linux.lock",package/"requirements.txt")
    credits=[{key:row[key] for key in ("id","source_photo","source_dataset_license","usage","note")} for row in controls["subjects"]]
    jsonwrite(package/"source-credits.json",credits)
    metadata=json.loads((workspace/"stable-diffusion-v1-5-stable-diffusion-v1-5-assets.json").read_text())
    wanted=("model_index.json","feature_extractor/preprocessor_config.json","scheduler/scheduler_config.json",
        "text_encoder/config.json","text_encoder/model.fp16.safetensors",
        "tokenizer/merges.txt","tokenizer/special_tokens_map.json","tokenizer/tokenizer_config.json","tokenizer/vocab.json",
        "unet/config.json","unet/diffusion_pytorch_model.fp16.safetensors","vae/config.json","vae/diffusion_pytorch_model.fp16.safetensors")
    assets=[]
    for name in wanted:
        row=next(s for s in metadata["siblings"] if s["rfilename"]==name)
        url="https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5/resolve/"+metadata["sha"]+"/"+name
        if row.get("lfs"):
            assets.append({"path":"base/"+name,"url":url,"size":row["lfs"]["size"],"sha256":row["lfs"]["sha256"]})
        else:
            with urllib.request.urlopen(url,timeout=25) as response:data=response.read(2000000)
            blob=sha256(data).hexdigest()
            target=package/"base"/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    access=json.loads((workspace.parent/"method-reassessment/checkpoint-access.json").read_text())
    keys=json.loads((workspace.parent/"method-reassessment/checkpoint-metadata.json").read_text())
    for row in access:
        info=next(k for k in keys if k["name"]==row["name"])
        assets.append({"path":"weights/"+row["name"],"url":row["url"],"size":info["size"],
                       "pickle_sha256":info["pickle_sha256"]})
    plan={"experiment":"STABLE-MAKEUP-001","training":False,"production_enabled":False,
      "cases":cases,"reference":{"file":"inputs/makeup-reference.png","sha256":digest(package/"inputs/makeup-reference.png"),
      "preprocessing":controls["reference"]},
      "source_commit":stable["commit"],"base_model":{"id":"stable-diffusion-v1-5/stable-diffusion-v1-5","revision":metadata["sha"]},
      "steps":30,"guidance":1.6,"seed":1977,"dtype":"float16","max_seconds":7200,"assets":assets,
      "own_trained_makeup_adapter_used":False,"quality_acceptance":"PENDING",
      "limits":["Isolated test, not production or a guaranteed cosmetic quality fix",
       "FP16 is an explicit T4 evaluation change from the author's FP32 entry example",
       "Prepared controls use author SPIGA/RetinaFace on CPU and frozen source images",
       "No training, servers, API keys, tunnels, Render connection, or catalog changes",
       "Do not redistribute this photo-containing evaluation input publicly",
       "No automatic acceptance or claimed pixel preservation for the generative output"]}
    jsonwrite(package/"plan.json",plan)
    files={}
    for path in sorted(package.rglob("*")):
        if path.is_file():
            if path.suffix==".py":ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
            files[path.relative_to(package).as_posix()]=digest(path)
    jsonwrite(package/"bundle-manifest.json",{"files":files,"production_enabled":False})
    bundle=workspace/"beautycore-stable-makeup-pilot.bin"
    with zipfile.ZipFile(bundle,"w",zipfile.ZIP_DEFLATED) as archive:
        for name in [*files,"bundle-manifest.json"]:archive.write(package/name,name)
    with zipfile.ZipFile(bundle) as archive:
        if archive.testzip() is not None:raise ValueError("Bundle CRC failure")
    jsonwrite(workspace/"package-receipt.json",{"bundle_sha256":digest(bundle),"bytes":bundle.stat().st_size,
      "members":len(files)+1,"asset_download_bytes":sum(a["size"] for a in assets),"gpu_inference_tested":False})
    print("BUNDLE_READY",bundle,flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--workspace",required=True,type=Path)
    args=parser.parse_args();build(args.workspace)

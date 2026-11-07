"""Four-case offline Stable-Makeup trial. Never imports BeautyCore serving code."""
import argparse
import gc
from hashlib import sha256
import json
from pathlib import Path
import sys
import time
import urllib.request
import zipfile


def digest(path):
    h=sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()


def owned(root,name):
    if not isinstance(name,str) or "\\" in name or ":" in name:
        raise ValueError("Invalid relative path")
    result=(Path(root)/name).resolve()
    if not result.is_relative_to(Path(root).resolve()):raise ValueError("Path escapes trial")
    return result


def validate(root):
    root=Path(root);plan=json.loads((root/"plan.json").read_text())
    if (plan.get("experiment")!="STABLE-MAKEUP-001" or len(plan.get("cases",[]))!=4
        or len({r["id"] for r in plan["cases"]})!=4
        or plan.get("training") is not False or plan.get("production_enabled") is not False
        or plan.get("steps")!=30 or plan.get("guidance")!=1.6 or plan.get("seed")!=1977
        or plan.get("dtype")!="float16" or plan.get("max_seconds")!=7200):
        raise ValueError("Frozen four-case evaluation scope differs")
    manifest=json.loads((root/"bundle-manifest.json").read_text())
    for name,expected in manifest["files"].items():
        if digest(owned(root,name))!=expected:raise ValueError("Trial file differs: "+name)
    for row in plan["cases"]:
        for name,key in (("source","source_sha256"),("control","control_sha256")):
            if digest(owned(root,row[name]))!=row[key]:raise ValueError("Frozen input differs")
    if digest(owned(root,plan["reference"]["file"]))!=plan["reference"]["sha256"]:
        raise ValueError("Reference differs")
    return plan


def verify_asset(path,asset):
    if not path.is_file() or path.stat().st_size!=asset["size"]:
        raise ValueError("Downloaded asset size differs: "+asset["path"])
    actual=digest(path)
    if asset.get("sha256") and actual!=asset["sha256"]:
        raise ValueError("Downloaded asset hash differs: "+asset["path"])
    if asset.get("pickle_sha256"):
        with zipfile.ZipFile(path) as archive:
            entries=[entry for entry in archive.infolist() if entry.filename.endswith("/data.pkl")]
            if len(entries)!=1 or entries[0].file_size>5000000:
                raise ValueError("Unexpected checkpoint metadata")
            if sha256(archive.read(entries[0])).hexdigest()!=asset["pickle_sha256"]:
                raise ValueError("Checkpoint metadata differs")
            bad=archive.testzip()
            if bad:raise ValueError("Corrupt checkpoint member: "+bad)
    return actual


def download_assets(root,result):
    plan=validate(root);root=Path(root);result=Path(result)
    assets=[]
    for item in plan["assets"]:
        path=owned(root,item["path"]);path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():
            partial=path.with_suffix(path.suffix+".part")
            count=0;h=sha256();last=time.monotonic()
            print("DOWNLOAD",item["path"],item["size"],"bytes",flush=True)
            request=urllib.request.Request(item["url"],headers={"User-Agent":"BeautyCore-isolated-trial"})
            with urllib.request.urlopen(request,timeout=45) as response,partial.open("wb") as output:
                if "text/html" in response.headers.get("Content-Type",""):
                    raise ValueError("Model download returned a web page: "+item["path"])
                while True:
                    chunk=response.read(1024*1024)
                    if not chunk:break
                    count+=len(chunk)
                    if count>item["size"]:raise ValueError("Download larger than frozen asset")
                    output.write(chunk);h.update(chunk)
                    if time.monotonic()-last>20:
                        print("DOWNLOAD_PROGRESS",item["path"],count,"/",item["size"],flush=True);last=time.monotonic()
            verify_asset(partial,item);partial.replace(path)
        actual=verify_asset(path,item)
        assets.append({"path":item["path"],"sha256":actual,"size":path.stat().st_size,
                       "hash_basis":"upstream_expected" if item.get("sha256") else "observed_after_size_metadata_and_crc_checks"})
        (result/"downloaded-assets.json").write_text(json.dumps(assets,indent=2)+"\n")
    print("ALL_ASSETS_VERIFIED",len(assets),flush=True)


def infer(root,result):
    root=Path(root).resolve();result=Path(result).resolve();plan=validate(root)
    sys.path.insert(0,str(root/"vendor/stable"))
    import torch
    import diffusers
    from PIL import Image,ImageDraw
    from diffusers import UNet2DConditionModel,ControlNetModel,DDIMScheduler
    from detail_encoder.encoder_plus import detail_encoder
    from pipeline_sd15 import StableDiffusionControlNetPipeline
    if not torch.cuda.is_available():raise RuntimeError("CUDA GPU required; select T4")
    if not diffusers.__file__.replace("\\","/").startswith(str(root/"vendor/stable").replace("\\","/")):
        raise RuntimeError("Wrong diffusers source imported")
    if diffusers.__version__!="0.23.1" or not torch.__version__.startswith("2.0.1"):
        raise RuntimeError("Trial Torch/diffusers versions differ")
    name=torch.cuda.get_device_name(0)
    if "T4" not in name or torch.cuda.get_device_properties(0).total_memory<14000*1024*1024:
        raise RuntimeError("This trial targets Kaggle T4 with at least14GiB")
    dtype=torch.float16;torch.set_num_threads(4)
    torch.cuda.reset_peak_memory_stats()
    environment={"torch":torch.__version__,"cuda":torch.version.cuda,"gpu":name,"diffusers":diffusers.__version__,
                 "dtype":"float16","training":False,"new_method":"Externally pretrained Stable-Makeup",
                 "base_model":plan["base_model"],"source_commit":plan["source_commit"],
                 "note":"FP16 is a bounded T4 evaluation choice; original example uses FP32. Quality unverified."}
    (result/"environment.json").write_text(json.dumps(environment,indent=2)+"\n")
    started=time.monotonic();base=owned(root,"base")
    print("MODEL_LOAD_START",flush=True)
    unet=UNet2DConditionModel.from_pretrained(base,subfolder="unet",variant="fp16",
        use_safetensors=True,torch_dtype=dtype,local_files_only=True)
    identity=ControlNetModel.from_unet(unet)
    pose=ControlNetModel.from_unet(unet)
    encoder=detail_encoder(unet,str(root/"clip"),"cuda",dtype=dtype)
    for model,path in ((encoder,"weights/pytorch_model.bin"),(identity,"weights/pytorch_model_1.bin"),(pose,"weights/pytorch_model_2.bin")):
        state=torch.load(owned(root,path),map_location="cpu",weights_only=True)
        model.load_state_dict(state,strict=True)
        del state;gc.collect()
        model.to(device="cuda",dtype=dtype).eval()
    unet.to(device="cuda",dtype=dtype).eval()
    pipeline=StableDiffusionControlNetPipeline.from_pretrained(base,unet=unet,
        controlnet=[identity,pose],safety_checker=None,torch_dtype=dtype,variant="fp16",
        use_safetensors=True,local_files_only=True).to("cuda")
    pipeline.scheduler=DDIMScheduler.from_config(pipeline.scheduler.config)
    # Do not replace SSR attention processors with generic attention slicing.
    load_seconds=time.monotonic()-started
    print("MODEL_LOAD_COMPLETE",round(load_seconds,2),"seconds",flush=True)
    records=[];reference=Image.open(owned(root,plan["reference"]["file"])).convert("RGB")
    reference.save(result/"reference.png")
    for case in plan["cases"]:
        source=Image.open(owned(root,case["source"])).convert("RGB")
        control=Image.open(owned(root,case["control"])).convert("RGB")
        if source.size!=(512,512) or control.size!=(512,512) or reference.size!=(512,512):
            raise ValueError("Frozen image resolution differs")
        begin=time.monotonic()
        print("TRANSFER_START",case["id"],len(records)+1,"/4",flush=True)
        with torch.inference_mode():
            generated=encoder.generate(id_image=[source,control],makeup_image=reference,
                seed=plan["seed"],guidance_scale=plan["guidance"],
                num_inference_steps=plan["steps"],pipe=pipeline)
        if generated.size!=(512,512):raise ValueError("Unexpected output size")
        path=result/(case["id"]+"-generated.png");generated.convert("RGB").save(path)
        source.save(result/(case["id"]+"-source.png"));control.save(result/(case["id"]+"-control.png"))
        sheet=Image.new("RGB",(1536,550),"white");draw=ImageDraw.Draw(sheet)
        for column,title,image in ((0,"ORIGINAL",source),(1,"MAKEUP REFERENCE",reference),(2,"RAW MODEL OUTPUT - NOT DEPLOYED",generated)):
            sheet.paste(image,(column*512,30));draw.text((column*512+5,9),title,fill="black")
        sheet.save(result/(case["id"]+"-comparison.png"))
        records.append({"id":case["id"],"output":path.name,"sha256":digest(path),
            "seconds":time.monotonic()-begin,"peak_allocated_bytes":torch.cuda.max_memory_allocated(),
            "peak_reserved_bytes":torch.cuda.max_memory_reserved(),"human_acceptance":"PENDING"})
        (result/"report.json").write_text(json.dumps({"experiment":plan["experiment"],"cases":records,
            "environment":environment,"production_enabled":False,"training":False,
            "model_load_seconds":load_seconds,
            "status":"COMPLETE_REQUIRES_VISUAL_REVIEW" if len(records)==4 else "PARTIAL",
            "own_trained_makeup_adapter_used":False,"quality_acceptance":"PENDING"},indent=2)+"\n")
        print("TRANSFER_DONE",case["id"],round(records[-1]["seconds"],2),"seconds",flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",required=True,type=Path);parser.add_argument("--result",required=True,type=Path)
    parser.add_argument("--stage",choices=("download","infer"),required=True)
    args=parser.parse_args();args.result.mkdir(parents=True,exist_ok=True)
    (download_assets if args.stage=="download" else infer)(args.root,args.result)

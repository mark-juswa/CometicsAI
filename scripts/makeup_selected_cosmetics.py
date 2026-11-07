"""Offline selected-cosmetics transfer onto the original face; no new generation."""
import time
import cv2
import numpy as np
from scipy.spatial import Delaunay

from scripts.makeup_alignment_pilot import CHAINS
from scripts.makeup_source_render import gamut_safe

CONFIG = {"neutral_sigma": 30.0, "texture_sigma": 1.4, "edge_pixels": 1.5,
          "makeup_strength": 1.0, "new_diffusion_calls": 0,
          "cosmetic_boundary_sigma": 5.0, "dark_stroke_sigma": 3.0,
          "color_transfer": "reference-relative-linear-reflectance", "retain_dark_stroke_core": True}


def polygon(points):
    result=np.zeros((512,512),np.uint8)
    cv2.fillPoly(result,[np.rint(points).astype(np.int32)],1)
    return result.astype(bool)


def inside(mask,width=1.5):
    d=cv2.distanceTransform(mask.astype(np.uint8),cv2.DIST_L2,5)
    t=np.clip(d/width,0,1)
    return t*t*(3-2*t)


def warp_reference(reference, labels, original_points, reference_points):
    a=np.asarray(original_points,np.float64)
    b=np.asarray(reference_points,np.float64)
    if a.shape!=(478,3) or b.shape!=(478,3) or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("Expected478finite paired landmarks")
    a,b=a[:468,:2]*512,b[:468,:2]*512
    triangulation=Delaunay(a)
    yy,xx=np.mgrid[:512,:512]
    grid=np.column_stack((xx.ravel(),yy.ravel()))
    simplex=triangulation.find_simplex(grid)
    valid=simplex>=0
    selected=simplex[valid]
    transform=triangulation.transform[selected]
    first=np.einsum("nij,nj->ni",transform[:,:2],grid[valid]-transform[:,2])
    weights=np.column_stack((first,1-first.sum(axis=1)))
    mapped=np.einsum("ni,nij->nj",weights,b[triangulation.simplices[selected]])
    map_x=np.full(512*512,-1,np.float32);map_y=map_x.copy()
    map_x[valid]=mapped[:,0];map_y[valid]=mapped[:,1]
    map_x,map_y=map_x.reshape(512,512),map_y.reshape(512,512)
    rgb=cv2.remap(reference,map_x,map_y,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    mapped_labels=cv2.remap(labels.astype(np.uint8),map_x,map_y,cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT)
    return rgb,mapped_labels,valid.reshape(512,512)


def normalized(values,mask,sigma):
    weights=cv2.GaussianBlur(mask.astype(np.float32),(0,0),sigma)
    blurred=cv2.GaussianBlur(values*mask[:,:,None],(0,0),sigma)
    fallback=np.median(values[mask],axis=0)
    return np.where((weights>1e-5)[:,:,None],blurred/np.maximum(weights[:,:,None],1e-5),fallback)


def linear(values):
    return np.where(values<=.04045,values/12.92,((values+.055)/1.055)**2.4)


def srgb(values):
    return np.where(values<=.0031308,12.92*values,1.055*np.maximum(values,0)**(1/2.4)-.055)


def transfer(original,reference,source_labels,reference_labels,source_points,reference_points):
    for rgb,labels in ((original,source_labels),(reference,reference_labels)):
        if rgb.dtype!=np.uint8 or rgb.shape!=(512,512,3) or labels.shape!=(512,512):
            raise ValueError("Expected512squareRGB/labels")
    started=time.perf_counter()
    mapped,ref_labels,valid=warp_reference(reference,reference_labels,source_points,reference_points)
    points=np.asarray(source_points,np.float32)[:,:2]*512
    src=cv2.cvtColor(original.astype(np.float32)/255,cv2.COLOR_RGB2LAB)
    ref=cv2.cvtColor(mapped.astype(np.float32)/255,cv2.COLOR_RGB2LAB)
    skin=(source_labels==1)&valid
    common=skin&(ref_labels==1)
    if common.sum()<10000:raise ValueError("Insufficient aligned skin")
    yy,xx=np.mgrid[:512,:512]
    eyes=[]
    for side in ("right","left"):
        upper=points[CHAINS[side+"_upper"]];upper=upper[np.argsort(upper[:,0])]
        lower=points[CHAINS[side+"_lower"]];lower=lower[np.argsort(lower[:,0])]
        brow=points[CHAINS[side+"_brow_lower"]];brow=brow[np.argsort(brow[:,0])]
        eyes.append((upper,lower,brow))
    eye_y=float(np.mean([u[:,1].mean() for u,l,b in eyes]))
    mouth_top=float(points[CHAINS["lip_outer"],1].min())
    face_height=float(np.ptp(points[:468,1]))
    neutral=common&((yy<eye_y-.10*face_height)|(yy>mouth_top+.17*face_height))
    if neutral.sum()<1000:raise ValueError("Missing neutral complexion references")
    src_base=normalized(src,neutral,CONFIG["neutral_sigma"])
    ref_base=normalized(ref,neutral,CONFIG["neutral_sigma"])
    src_smooth=cv2.GaussianBlur(src,(0,0),CONFIG["texture_sigma"])
    src_detail=src-src_smooth
    delta=ref-ref_base
    output=src.copy()
    masks={"eye":np.zeros((512,512),np.float32),"lash_liner":np.zeros((512,512),np.float32),
           "blush":np.zeros((512,512),np.float32),"lip":np.zeros((512,512),np.float32),"brow":np.zeros((512,512),np.float32)}
    # Color-only blush: reference pigment residual, not its white foundation/glow.
    for upper,lower,brow in eyes:
        width=float(upper[-1,0]-upper[0,0]);cx=float(upper[:,0].mean())
        center_x=float(points[:468,0].mean());outward=-1 if cx<center_x else 1
        bottom=float(lower[:,1].max())
        cy=bottom+.5*(mouth_top-bottom)
        region=skin&((((xx-(cx+outward*.20*width))/(width*.90))**2+
                       ((yy-cy)/max(15,(mouth_top-bottom)*.55))**2)<1)
        pigment=np.linalg.norm(delta[:,:,1:],axis=2)
        confidence=np.clip((pigment-2)/4,0,1)
        alpha=cv2.GaussianBlur((inside(region,2)*confidence).astype(np.float32),(0,0),CONFIG["cosmetic_boundary_sigma"])
        alpha[~skin]=0
        masks["blush"]=np.maximum(masks["blush"],alpha.astype(np.float32))
    # Relative reflectance keeps the selected pigment effect while allowing the
    # original complexion/lighting to remain underneath it. It does not assert
    # exact displayed RGB equality across different foundation colors.
    ref_base_rgb=cv2.cvtColor(ref_base,cv2.COLOR_LAB2RGB)
    ratio=linear(mapped.astype(np.float32)/255)/np.maximum(linear(ref_base_rgb),1e-4)
    ratio=np.clip(ratio,.02,4)
    physical=srgb(np.clip(linear(original.astype(np.float32)/255)*ratio,0,1))
    physical_lab=cv2.cvtColor(np.clip(physical,0,1),cv2.COLOR_RGB2LAB)
    color_target=physical_lab[:,:,1:]
    alpha=masks["blush"]
    output[:,:,1:]=output[:,:,1:]*(1-alpha[:,:,None])+color_target*alpha[:,:,None]
    # Actual mapped dark strokes and eyelid pigments; no procedural new lashes.
    for upper,lower,brow in eyes:
        width=float(upper[-1,0]-upper[0,0])
        top=np.interp(np.arange(512),upper[:,0],upper[:,1])[None,:]
        brow_line=np.interp(np.arange(512),brow[:,0],brow[:,1])[None,:]
        region=skin&(xx>upper[0,0]-.12*width)&(xx<upper[-1,0]+.12*width)&(yy>brow_line+1)&(yy<top+2)
        pigment=np.linalg.norm(delta[:,:,1:],axis=2)
        darkness=np.maximum(0,-delta[:,:,0])
        confidence=np.clip((np.maximum(pigment,darkness)-2)/4,0,1)
        alpha=cv2.GaussianBlur((inside(region,CONFIG["edge_pixels"])*confidence).astype(np.float32),(0,0),CONFIG["cosmetic_boundary_sigma"])
        alpha[~skin]=0
        eye_target=src.copy()
        eye_target[:,:,1:]=physical_lab[:,:,1:]
        # Transfer actual narrow dark strokes; broad model facial shading is not
        # a reliable cosmetic layer and produced the rejected rectangular patches.
        ref_dark=np.maximum(0,cv2.GaussianBlur(ref[:,:,0],(0,0),CONFIG["dark_stroke_sigma"])-ref[:,:,0])
        src_dark=np.maximum(0,cv2.GaussianBlur(src[:,:,0],(0,0),CONFIG["dark_stroke_sigma"])-src[:,:,0])
        # Feather transitions, but do not attenuate narrow black cosmetic cores.
        alpha=np.maximum(alpha,inside(region,1)*(ref_dark>6).astype(np.float32))
        alpha[~skin]=0
        extra_dark=-np.maximum(0,ref_dark-src_dark)
        eye_target[:,:,0]=np.clip(src[:,:,0]+extra_dark,0,100)
        output=output*(1-alpha[:,:,None])+eye_target*alpha[:,:,None]
        masks["eye"]=np.maximum(masks["eye"],alpha.astype(np.float32))
        masks["lash_liner"]=np.maximum(masks["lash_liner"],(alpha*(darkness>12)).astype(np.float32))
    # Original brow geometry stays; reference pigment can darken existing hairs.
    brow_region=np.isin(source_labels,(6,7))&valid
    alpha=inside(brow_region,3)
    alpha*=np.isin(ref_labels,(6,7))
    brow_target=src.copy()
    brow_target[:,:,0]=np.minimum(src[:,:,0],cv2.GaussianBlur(ref[:,:,0],(0,0),CONFIG["texture_sigma"])+src_detail[:,:,0])
    output=output*(1-alpha[:,:,None])+brow_target*alpha[:,:,None]
    masks["brow"]=alpha.astype(np.float32)
    # Full chosen lipstick shade, with original fine lip detail and mouth outline.
    lip_region=np.isin(source_labels,(11,12))&valid
    if lip_region.sum()<100:raise ValueError("Missing source lips")
    coverage=float(np.mean(np.isin(ref_labels[ lip_region],(11,12))))
    if coverage<.65:raise ValueError("Lip alignment is uncertain")
    lip_reference_mask=np.isin(ref_labels,(11,12))&valid
    ref_lip=normalized(ref,lip_reference_mask,CONFIG["texture_sigma"])
    src_lip=normalized(src,lip_region,CONFIG["texture_sigma"])
    lip_target=ref_lip+(src-src_lip)
    alpha=inside(lip_region,CONFIG["edge_pixels"])
    output=output*(1-alpha[:,:,None])+lip_target*alpha[:,:,None]
    masks["lip"]=alpha.astype(np.float32)
    # Eye interiors, nose, inner mouth/teeth, hair, neck and scene are original.
    editable=np.isin(source_labels,(1,6,7,11,12))
    allowed=np.logical_or.reduce([v>0 for v in masks.values()])&editable
    output,gamut_pixels=gamut_safe(output,allowed)
    converted=cv2.cvtColor(output,cv2.COLOR_LAB2RGB)
    result=original.copy()
    result[allowed]=np.rint(np.clip(converted,0,1)*255).astype(np.uint8)[allowed]
    if np.any(result[~allowed]!=original[~allowed]):raise RuntimeError("Protected source changed")
    return result,masks,{
        "generator":"beautycore_selected_cosmetics_layer_pilot_v3",
        "makeup_strength":1.0,"new_diffusion_calls":0,"display_source_warped":False,
        "original_is_canvas":True,"protected_original_changed_pixels":0,
        "lip_alignment_coverage":coverage,"gamut_compressed_pixels":gamut_pixels,
        "region_pixels":{k:int((v>0).sum()) for k,v in masks.items()},
        "cpu_seconds":time.perf_counter()-started,
        "limit":"Flattened reference has no true makeup layers. Extracted pigments/strokes may differ; style/intensity and source texture require visual review. Not exact pixel preservation."
    }

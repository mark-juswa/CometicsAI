"""One complete cosmetic specification for target creation and model supervision.

This does not change the serving presets or imply acceptance of a style/model.
"""
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ("eyes", "lips", "blush", "complexion_finish", "brows", "contour_highlight")
BROWS = "Retain the existing brow outline and individual hairs; do not redraw or reshape brows."
FINISH = "Foundation and any local concealer must match the original skin shade and undertone, retaining pores, fine lines and natural lighting."
SPECS = {
    "natural_makeup": ("soft upper-lash definition and light neutral lid color", "muted rose satin lips", "soft neutral rose blush", "light satin coverage with natural texture", "very restrained natural cheek dimension"),
    "no_makeup_makeup": ("minimal natural lash definition without a visible heavy shadow", "sheer natural rose lip tint", "a faint natural cheek flush", "sheer local complexion evening with original freckles visible", "no obvious contour or added bright highlight"),
    "soft_glam": ("clearly visible blended warm taupe/bronze shadow, fine liner and naturally separated lashes", "medium nude-rose satin lipstick", "feathered warm rose blush", "polished medium satin coverage and discreet matched concealer", "soft cheek contour and a restrained satin highlight"),
    "smoky_glam": ("strong charcoal/deep brown smoky upper lids and soft outer corners, defined lash lines and realistic mascara", "subdued nude satin lipstick", "restrained neutral rose blush", "matched medium satin base", "soft contour with no pale under-eye triangles"),
    "dewy_peach": ("soft peach-neutral lids and fine natural lashes", "peach-rose lightly glossy lips", "visible feathered peach blush adapted to the original complexion", "light dewy skin coverage with visible pores", "small naturally placed sheen, not a broad white highlight"),
    "rosy_pink": ("delicate rose upper-eyelid color and fine liner", "soft rose-pink satin lips", "coordinated softly feathered rose-pink cheek color", "light satin matched foundation", "restrained neutral cheek dimension"),
    "bronze_golden_glam": ("visible blended warm bronze lids, localized gold shimmer, fine dark liner and separated lashes", "warm nude satin lipstick", "warm softly blended bronze-rose cheeks", "matched medium luminous satin coverage", "soft bronze contour and a small gold highlight without orange skin"),
    "matte_nude": ("neutral brown lid definition and fine lash lines", "opaque but naturally shaded matte nude lipstick", "restrained nude-rose blush", "matched medium soft matte foundation retaining fine skin texture", "light natural contour, no added glossy highlight"),
    "classic_red_lip": ("minimal neutral lids with fine dark lash-line definition", "classic rich red satin lipstick inside the existing lip outline", "restrained natural cheeks", "matched light-to-medium satin base", "subtle natural cheek dimension"),
    "bold_evening_glam": ("strong blended deep brown/plum lids, defined dark liner and realistic separated mascara", "rich berry-red satin lipstick", "visible naturally blended rose blush", "matched polished medium coverage foundation and discreet concealer", "softly sculpted cheeks and restrained photographic highlight"),
    "exp_cloud_berry_lips": ("understated neutral eyes and fine natural lashes", "muted berry stain with visibly diffused edges within the original lip outline", "restrained soft berry cheek color", "soft cloud-like matte coverage with natural skin texture", "very soft neutral contour without a white cast"),
    "exp_manga_lash": ("distinct separated upper-lash clusters and delicate dark liner fitted to the original eye shape; no enlarged eyes", "restrained muted rose lipstick", "soft pink blush", "matched light satin skin coverage", "restrained natural cheek dimension"),
    "exp_icy_silver": ("clearly visible localized cool silver-blue upper-lid shimmer, fine charcoal lash lines and realistic lashes", "subtle natural neutral-rose lips", "subdued neutral cheeks", "matched light-to-medium satin skin coverage", "restrained natural dimension without silver pigment on the whole face"),
}


def build_catalog(root=ROOT):
    presets = json.loads((root / "data/makeup/DATA-M001-paired/inference_presets.json").read_text(encoding="utf-8"))
    release = json.loads((root / "backend/app/style_release.json").read_text(encoding="utf-8"))
    originals = presets["styles"]
    held = [r for r in release["candidates"] if r["feature"] == "makeup"]
    names = {r["id"]: r["name"] for r in originals + held}
    if set(names) != set(SPECS) or len(names) != 13:
        raise ValueError("Complete corrective catalog must match all current and held Makeup IDs")
    styles = []
    for style_id, name in names.items():
        eyes, lips, blush, finish, contour = SPECS[style_id]
        components = dict(eyes=eyes, lips=lips, blush=blush, complexion_finish=finish,
                          brows=BROWS, contour_highlight=contour)
        instruction = "Apply " + name + ". " + " ".join(key.replace("_", " ").capitalize() + ": " + components[key] + "." for key in COMPONENTS)
        caption = instruction + " " + FINISH + " " + presets["preservation_instruction"]
        styles.append({"id": style_id, "name": name, "components": components,
            "serving_status": "existing" if style_id in {s["id"] for s in originals} else "held",
            "instruction": instruction, "caption": caption})
    return {"schema": "makeup-corrective-catalog-v1", "production_enabled": False,
        "preservation_instruction": presets["preservation_instruction"], "styles": styles,
        "source_presets_sha256": sha256((root / "data/makeup/DATA-M001-paired/inference_presets.json").read_bytes()).hexdigest(),
        "source_release_sha256": sha256((root / "backend/app/style_release.json").read_bytes()).hexdigest()}


def teacher_prompt(style):
    return ("Edit target: image1 is the ORIGINAL portrait and sole identity, geometry, complexion, expression, "
        "lighting and scene reference. Make a realistic photographic cosmetic edit of this exact image, with the same crop. "
        + style["caption"] + " Show a coordinated complete makeup look at this style's intended strength, including its "
        "complexion finish, eyes and cheeks as well as lips. Keep the person recognizable and their original skin shade. "
        "Natural texture must remain visible. Do not replace teeth, enlarge eyes, reshape the nose or lips, alter expression, "
        "bleach skin, change undertone, redraw brows, add cosmetic plates, airbrush skin into plastic, change hair or background, "
        "or add text, panels or a collage. Output one edited photograph.")

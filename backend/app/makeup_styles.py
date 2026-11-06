"""Makeup catalog kept outside the Hairstyle adapter registry.

Legacy Base experiment instructions remain intact. Live MAKEUP-001 uses the
frozen reviewed inference presets in makeup_contract, not these older prompts.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MakeupStyle:
    id: str
    name: str
    description: str
    prompt: str
    status: str = "prototype"


MAKEUP_STYLES = (
    MakeupStyle("natural_makeup", "Natural Makeup", "Subtle, balanced everyday color.", "Apply natural everyday makeup with light complexion coverage, softly defined eyes, and a muted natural lip."),
    MakeupStyle("no_makeup_makeup", "No-Makeup Makeup", "Barely visible polish and even tone.", "Apply a no-makeup makeup look: very sheer complexion correction, subtle brows, nearly invisible eye definition, and a natural lip tint."),
    MakeupStyle("soft_glam", "Soft Glam", "Blended eyes and a polished finish.", "Apply soft glam makeup with blended neutral eyeshadow, defined lashes, softly sculpted cheeks, and a polished nude lip."),
    MakeupStyle("smoky_glam", "Smoky Glam", "Smoky eyes with a refined base.", "Apply smoky glam makeup with deep blended smoky eyeshadow, defined eyeliner and lashes, balanced complexion, and a restrained nude lip."),
    MakeupStyle("dewy_peach", "Dewy Peach", "Fresh peach color and luminous skin.", "Apply dewy peach makeup with luminous skin, peach blush, warm subtle eye color, and a peach tinted lip."),
    MakeupStyle("rosy_pink", "Rosy Pink", "Soft pink eyes, cheeks, and lips.", "Apply rosy pink makeup with soft pink blush, delicate rosy eyeshadow, natural lashes, and a coordinated pink lip."),
    MakeupStyle("bronze_golden_glam", "Bronze / Golden Glam", "Warm bronze eyes and golden glow.", "Apply bronze golden glam makeup with warm bronze and gold eyeshadow, softly bronzed cheeks, defined lashes, and a warm nude lip."),
    MakeupStyle("matte_nude", "Matte Nude", "Muted neutral color with a matte finish.", "Apply matte nude makeup with a natural matte complexion, neutral brown eye definition, subtle contour, and a matte nude lip."),
    MakeupStyle("classic_red_lip", "Classic Red Lip", "A crisp red lip with simple eyes.", "Apply classic red lip makeup with a precisely defined rich red lipstick, clean complexion, and understated eye makeup."),
    MakeupStyle("bold_evening_glam", "Bold Evening Glam", "Statement eyes and evening color.", "Apply bold evening glam makeup with dramatic defined eyes, full lashes, sculpted cheeks, and a rich statement lip."),
)

MAKEUP_STYLE_BY_ID = {style.id: style for style in MAKEUP_STYLES}


def base_prompt(style: MakeupStyle) -> str:
    return (
        f"{style.prompt} Preserve the person's identity, facial proportions, face shape, eye shape, nose structure, mouth and lip geometry, "
        "expression, hairstyle, hair color, clothing, pose, lighting, framing, and background. "
        "Change only the visible makeup."
    )

# Reviewed corrective model catalog, release candidate.
MAKEUP_STYLES += (
    MakeupStyle('exp_cloud_berry_lips', 'Cloud-Skin Makeup with Blurred Berry Lips', 'A soft base with diffused berry lip edges and restrained cheek color.', 'Apply Cloud-Skin Makeup with Blurred Berry Lips. Eyes: understated neutral eyes and fine natural lashes. Lips: muted berry stain with visibly diffused edges within the original lip outline. Blush: restrained soft berry cheek color. Complexion finish: soft cloud-like matte coverage with natural skin texture. Brows: Retain the existing brow outline and individual hairs; do not redraw or reshape brows.. Contour highlight: very soft neutral contour without a white cast. Foundation and any local concealer must match the original skin shade and undertone, retaining pores, fine lines and natural lighting. Edit the supplied photo of the same person. Keep their recognizable identity, face shape, eyes, nose, mouth geometry, expression, natural skin tone and skin texture. Keep the original hairstyle, hair color, clothing, background, pose, framing and lighting. Change makeup only. Keep cosmetic color in plausible facial regions and avoid mask-like patches or plastic skin.'),
    MakeupStyle('exp_manga_lash', 'Manga-Lash Makeup', 'Separated lash clusters with delicate liner, soft blush, and a restrained lip.', 'Apply Manga-Lash Makeup. Eyes: distinct separated upper-lash clusters and delicate dark liner fitted to the original eye shape; no enlarged eyes. Lips: restrained muted rose lipstick. Blush: soft pink blush. Complexion finish: matched light satin skin coverage. Brows: Retain the existing brow outline and individual hairs; do not redraw or reshape brows.. Contour highlight: restrained natural cheek dimension. Foundation and any local concealer must match the original skin shade and undertone, retaining pores, fine lines and natural lighting. Edit the supplied photo of the same person. Keep their recognizable identity, face shape, eyes, nose, mouth geometry, expression, natural skin tone and skin texture. Keep the original hairstyle, hair color, clothing, background, pose, framing and lighting. Change makeup only. Keep cosmetic color in plausible facial regions and avoid mask-like patches or plastic skin.'),
    MakeupStyle('exp_icy_silver', 'Icy Silver Eye Makeup', 'Localized silver-blue eyelid shimmer balanced with subdued cheeks and lips.', 'Apply Icy Silver Eye Makeup. Eyes: clearly visible localized cool silver-blue upper-lid shimmer, fine charcoal lash lines and realistic lashes. Lips: subtle natural neutral-rose lips. Blush: subdued neutral cheeks. Complexion finish: matched light-to-medium satin skin coverage. Brows: Retain the existing brow outline and individual hairs; do not redraw or reshape brows.. Contour highlight: restrained natural dimension without silver pigment on the whole face. Foundation and any local concealer must match the original skin shade and undertone, retaining pores, fine lines and natural lighting. Edit the supplied photo of the same person. Keep their recognizable identity, face shape, eyes, nose, mouth geometry, expression, natural skin tone and skin texture. Keep the original hairstyle, hair color, clothing, background, pose, framing and lighting. Change makeup only. Keep cosmetic color in plausible facial regions and avoid mask-like patches or plastic skin.'),
)
MAKEUP_STYLE_BY_ID = {style.id: style for style in MAKEUP_STYLES}

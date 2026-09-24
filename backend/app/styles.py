"""The prototype style catalog served to the frontend."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Style:
    id: str
    name: str
    description: str
    status: str = "prototype"


STYLES = (
    Style("crew-cut", "Crew Cut", "Short and clean with a close finish."),
    Style("textured-crop", "Textured Crop", "Soft texture with a relaxed fringe."),
    Style("curtain", "Curtain", "A center part with easy movement."),
    Style("bob", "Bob", "A neat shape at jaw length."),
    Style("pixie", "Pixie", "A short cut with light texture."),
    Style("layered", "Layered", "Longer lengths with gentle layers."),
)

STYLE_BY_ID = {style.id: style for style in STYLES}

# The trained conditional adapter only contains these three DATA-001 labels.
REAL_STYLES = (
    Style("crew_cut", "Crew Cut", "A short, close hairstyle.", "experimental"),
    Style("bob_hair", "Bob Hair", "A bob hairstyle.", "experimental"),
    Style("layered_hair", "Layered Hair", "A layered hairstyle.", "experimental"),
)
REAL_STYLE_BY_ID = {style.id: style for style in REAL_STYLES}
REAL_STYLE_PROMPTS = {
    "crew_cut": "Change the person's hairstyle to a crew cut while preserving their identity, facial features, expression, pose, clothing, lighting, framing, and background.",
    "bob_hair": "Change the person's hairstyle to a bob hairstyle while preserving their identity, facial features, expression, pose, clothing, lighting, framing, and background.",
    "layered_hair": "Change the person's hairstyle to layered hair while preserving their identity, facial features, expression, pose, clothing, lighting, framing, and background.",
}

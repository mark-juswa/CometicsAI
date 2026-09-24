"""The prototype style catalog served to the frontend."""

from dataclasses import dataclass

from app.registry import enabled_styles, load_registry


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

REGISTRY = load_registry()
REAL_STYLES = tuple(Style(item["style_id"], item["display_name"], item["description"],
                          item["support_status"]) for item in enabled_styles(REGISTRY))
REAL_STYLE_BY_ID = {style.id: style for style in REAL_STYLES}
REAL_STYLE_PROMPTS = {item["style_id"]: item["prompt"] for item in enabled_styles(REGISTRY)}

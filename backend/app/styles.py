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

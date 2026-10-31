"""Baseline Nails catalog plus explicitly accepted installed renderer additions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class NailStyle:
    id: str
    name: str
    description: str
    prompt: str
    training_label: str
    adapter_id: str | None = None
    status: str = "prototype"


NAIL_STYLES = (
    NailStyle("classic_red", "Classic Red Gloss", "Rich glossy red polish.", "Change the visible fingernails to glossy classic red polish while preserving the same hand, nail shape, skin, jewelry, pose, and background.", "classic_red", adapter_id="NAILS-001-LOCAL-v1"),
    NailStyle("nude_pink", "Nude Pink Gloss", "Soft natural pink polish.", "Apply glossy nude pink polish to the visible fingernails while preserving the same hand, nail shape, skin, jewelry, pose, and background.", "nude_pink"),
    NailStyle("glossy_black", "Glossy Black", "Deep reflective black polish.", "Apply glossy black polish to the visible fingernails while preserving the same hand, nail shape, skin, jewelry, pose, and background.", "glossy_black", adapter_id="NAILS-001-LOCAL-v1"),
    NailStyle("french_tip", "French Tip", "Natural pink nails with white tips.", "Apply a clean French manicure to the visible fingernails while preserving the existing nail length, hand, skin, jewelry, pose, and background.", "french_tip"),
    NailStyle("pink_ombre", "Pink Ombre", "A soft pink gradient toward each tip.", "Apply a soft pink ombre manicure to the visible fingernails while preserving the same hand, nail geometry, skin, jewelry, pose, and background.", "pink_ombre"),
)
NAIL_STYLE_BY_ID = {style.id: style for style in NAIL_STYLES}


def active_nail_styles(release=None):
    """Pending/held manifest entries never become public merely by existing."""
    from app.style_release import RELEASE
    from app.style_capabilities import installed_candidates

    release = RELEASE if release is None else release
    additions = installed_candidates(release)
    return NAIL_STYLES + tuple(
        NailStyle(c.id, c.name, c.description, "", "", status="available")
        for c in additions if c.feature == "nails"
    )


def active_nail_style_by_id(release=None):
    return {style.id: style for style in active_nail_styles(release)}

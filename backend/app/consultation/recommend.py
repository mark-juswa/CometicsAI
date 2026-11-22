"""Small deterministic provider and strict backend validation boundary."""

from hashlib import sha256
import re
from typing import Protocol

from pydantic import ValidationError

from app.consultation.catalog import AVAILABLE_STATUSES
from app.consultation.metadata import SERVICES
from app.consultation.models import (CatalogResponse, CatalogStyle, ConsultationState,
                                     FeatureId, Preferences, ProposedRecommendation,
                                     ProposedSet, Recommendation, RecommendationSet,
                                     ResolvedChoice, StyleChoice)


class InsufficientCandidates(ValueError):
    pass


class InvalidRecommendation(ValueError):
    pass


def _words(value: str) -> set[str]:
    words = set(re.findall(r"[a-z0-9]+", value.lower()))
    aliases = {'office': 'everyday', 'work': 'everyday', 'daily': 'everyday',
               'wedding': 'formal', 'graduation': 'formal', 'party': 'evening',
               'subtle': 'natural', 'minimal': 'natural', 'dramatic': 'bold',
               'smokey': 'smoky', 'golden': 'gold', 'rose': 'pink'}
    return words | {aliases[word] for word in words if word in aliases}


_SERVICE_WORDS = frozenset({"hair", "hairstyle", "makeup", "nail", "nails"})
_AVOID_TAG_ALIASES = {"heavy": "bold", "dramatic": "bold"}


def _avoid_terms(phrase: str) -> set[str]:
    words = _words(phrase)
    # A category word inside a longer phrase describes what is being styled,
    # not the unwanted quality: "heavy makeup" must not exclude "Natural Makeup".
    if len(words) > 1:
        words -= _SERVICE_WORDS
    return words | {_AVOID_TAG_ALIASES[word] for word in words if word in _AVOID_TAG_ALIASES}


def preference_terms(preferences: Preferences) -> set[str]:
    values = [preferences.occasion, preferences.vibe, preferences.hair_length,
              preferences.hair_maintenance, preferences.makeup_intensity,
              preferences.makeup_finish, preferences.nail_color, preferences.nail_finish,
              *preferences.likes]
    return set().union(*(_words(value) for value in values if value))


def candidate_styles(styles: list[CatalogStyle], preferences: Preferences) -> list[CatalogStyle]:
    """Explicit things to avoid remove candidates; all other answers rank them."""
    avoids = set().union(*(_avoid_terms(value) for value in preferences.avoids))
    terms = preference_terms(preferences)
    eligible = [style for style in styles if style.status in AVAILABLE_STATUSES
                and not (_words(" ".join(style.tags)) | _words(style.name)) & avoids]
    # Explicit Makeup intensity is a compatibility constraint, not a weak tie.
    if preferences.makeup_intensity:
        def compatible(style):
            if style.feature != 'makeup':
                return True
            tags = set(style.tags)
            intensity = 'bold' if 'bold' in tags else 'natural' if 'natural' in tags else 'soft'
            return intensity == preferences.makeup_intensity
        eligible = [style for style in eligible if compatible(style)]
    if preferences.makeup_finish:
        eligible = [style for style in eligible if style.feature != 'makeup'
                    or preferences.makeup_finish in style.tags]
    return sorted(eligible, key=lambda style: (-style_score(style, preferences), style.style_id))


def style_score(style: CatalogStyle, preferences: Preferences) -> int:
    tags = _words(' '.join(style.tags))
    score = 2 * len(tags & preference_terms(preferences))
    specific = {'makeup': (preferences.makeup_intensity, preferences.makeup_finish),
                'hairstyle': (preferences.hair_length, preferences.hair_maintenance),
                'nails': (preferences.nail_color, preferences.nail_finish)}[style.feature]
    score += sum(8 * len(tags & _words(value)) for value in specific if value)
    score += sum(3 * len(tags & _words(value)) for value in preferences.likes)
    return score


def grounded_reason(style: CatalogStyle, preferences: Preferences) -> str:
    matched = sorted(_words(' '.join(style.tags)) & preference_terms(preferences))
    return (f"{style.name} matches your stated {', '.join(matched[:3])} preferences."
            if matched else f"{style.name} is a supported option to explore; no specific preference match was established.")


class RecommendationProvider(Protocol):
    def recommend(self, state: ConsultationState,
                  candidates: dict[FeatureId, list[CatalogStyle]]) -> ProposedSet: ...


class DeterministicProvider:
    def recommend(self, state: ConsultationState,
                  candidates: dict[FeatureId, list[CatalogStyle]]) -> ProposedSet:
        primary = candidates[state.primary_service]
        if len(primary) < 3:
            raise InsufficientCandidates("Fewer than three supported styles match these preferences.")
        terms = preference_terms(state.preferences)
        other_features = [feature for feature in SERVICES if feature != state.primary_service
                          and candidates.get(feature)]
        rows = []
        for index, style in enumerate(primary[:3]):
            matched = sorted(set(style.tags) & terms)
            reason = grounded_reason(style, state.preferences)
            complements = []
            if other_features:
                other = other_features[index % len(other_features)]
                complement = candidates[other][0]
                if style_score(complement, state.preferences) > 0:
                    complements.append(StyleChoice(feature=other, style_id=complement.style_id))
            rows.append(ProposedRecommendation(
                primary=StyleChoice(feature=state.primary_service, style_id=style.style_id),
                reason=reason, complements=complements))
        return ProposedSet(recommendations=rows)


def validate_recommendations(raw: object, state: ConsultationState, catalog: CatalogResponse,
                             candidates: dict[FeatureId, list[CatalogStyle]]) -> RecommendationSet:
    """Recheck every provider-selected ID against the current active feature catalog.

    The provider cannot supply service price, duration, style names, or Nail
    execution paths; the backend resolves those from its own catalogs.
    """
    try:
        proposed = ProposedSet.model_validate(raw)
    except ValidationError as exc:
        raise InvalidRecommendation("Malformed recommendation set.") from exc
    active = {feature: {style.style_id: style for style in styles}
              for feature, styles in catalog.styles.items()}
    candidate_ids = {feature: {style.style_id for style in styles}
                     for feature, styles in candidates.items()}
    selected = set()
    resolved = []
    for row in proposed.recommendations:
        choice = row.primary
        if choice.feature != state.primary_service:
            raise InvalidRecommendation("Primary feature differs from the consultation service.")
        if choice.style_id in selected:
            raise InvalidRecommendation("Duplicate primary recommendation.")
        selected.add(choice.style_id)
        if (choice.style_id not in candidate_ids.get(choice.feature, set())
                or choice.style_id not in active.get(choice.feature, {})):
            raise InvalidRecommendation("Primary style is unavailable or excluded.")
        primary_style = active[choice.feature][choice.style_id]
        if primary_style.status not in AVAILABLE_STATUSES:
            raise InvalidRecommendation("Primary style is disabled.")
        extras = []
        seen_extras = set()
        for extra in row.complements:
            if extra.feature == state.primary_service:
                raise InvalidRecommendation("Complement must be another service.")
            pair = (extra.feature, extra.style_id)
            if pair in seen_extras:
                raise InvalidRecommendation("Duplicate complementary style.")
            seen_extras.add(pair)
            if (extra.style_id not in candidate_ids.get(extra.feature, set())
                    or extra.style_id not in active.get(extra.feature, {})):
                raise InvalidRecommendation("Complementary style is unavailable or excluded.")
            extra_style = active[extra.feature][extra.style_id]
            if extra_style.status not in AVAILABLE_STATUSES:
                raise InvalidRecommendation("Complementary style is disabled.")
            if style_score(extra_style, state.preferences) <= 0:
                continue
            extras.append(ResolvedChoice(feature=extra.feature, style_id=extra.style_id,
                                         style_name=extra_style.name, service=SERVICES[extra.feature],
                                         nail_path=extra_style.nail_path))
        digest = sha256(f"{state.primary_service}:{choice.style_id}".encode()).hexdigest()[:12]
        resolved.append(Recommendation(
            id=f"rec-{digest}",
            primary=ResolvedChoice(feature=choice.feature, style_id=choice.style_id,
                                   style_name=primary_style.name, service=SERVICES[choice.feature],
                                   nail_path=primary_style.nail_path),
            reason=grounded_reason(primary_style, state.preferences), complements=extras))
    # Gemini extracts intent; the backend owns the final preference ranking.
    # Validate all proposed IDs first so hallucinations and exclusions never pass.
    ranked = sorted(candidates[state.primary_service],
                    key=lambda style: (-style_score(style, state.preferences), style.style_id))
    if len(ranked) < 3:
        raise InvalidRecommendation('Fewer than three compatible styles remain.')
    selected_scores = sorted((style_score(active[row.primary.feature][row.primary.style_id], state.preferences)
                              for row in resolved), reverse=True)
    best_scores = [style_score(style, state.preferences) for style in ranked[:3]]
    if selected_scores == best_scores:
        return RecommendationSet(recommendations=resolved)
    for index, style in enumerate(ranked[:3]):
        primary = ResolvedChoice(feature=style.feature, style_id=style.style_id,
            style_name=style.name, service=SERVICES[style.feature], nail_path=style.nail_path)
        resolved[index] = resolved[index].model_copy(update={
            'id': 'rec-' + sha256(f'{style.feature}:{style.style_id}'.encode()).hexdigest()[:12],
            'primary': primary, 'reason': grounded_reason(style, state.preferences)})
    return RecommendationSet(recommendations=resolved)

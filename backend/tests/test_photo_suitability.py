"""Subject rejection must precede storage, consultant calls and image generation."""
import asyncio
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image
import pytest

from app import main, photo_suitability as subject
from app.consultation.models import CatalogStyle, Preferences
from app.consultation.recommend import candidate_styles, style_score


def photo():
    out = BytesIO()
    Image.new('RGB', (256, 256), 'white').save(out, format='PNG')
    return {'image': ('object.png', out.getvalue(), 'image/png')}


@pytest.mark.parametrize('feature,style', [('makeup', 'natural_makeup'), ('hairstyle', 'bob'), ('nails', 'classic_red')])
def test_wrong_subject_never_reaches_generator(monkeypatch, feature, style):
    monkeypatch.setattr(subject, 'check_subject', lambda *_: False)
    client = TestClient(main.app)
    response = client.post(f'/features/{feature}/generate', data={'style_id': style}, files=photo())
    assert response.status_code == 422
    assert response.json()['detail'] == subject.MESSAGES[feature]


def test_rejected_photo_is_not_attached_and_existing_session_is_rechecked(monkeypatch):
    main.consultation_store._entries.clear()
    client = TestClient(main.app)
    identity = client.post('/consultations', json={'primary_service': 'makeup'}).json()['id']
    monkeypatch.setattr(subject, 'check_subject', lambda *_: False)
    assert client.put(f'/consultations/{identity}/photo', files=photo()).status_code == 422
    assert client.get(f'/consultations/{identity}').json()['photo'] is None
    monkeypatch.setattr(subject, 'check_subject', lambda *_: True)
    assert client.put(f'/consultations/{identity}/photo', files=photo()).status_code == 200
    monkeypatch.setattr(subject, 'check_subject', lambda *_: False)
    assert client.post(f'/consultations/{identity}/recommendations').status_code == 422
    assert client.post(f'/consultations/{identity}/recommendations/anything/generation').status_code == 422


def test_missing_detector_is_service_error_not_wrong_photo(monkeypatch):
    def broken(*_):
        raise RuntimeError('private detector path')
    monkeypatch.setattr(subject, 'check_subject', broken)
    with pytest.raises(main.HTTPException) as error:
        asyncio.run(subject.ensure_photo_subject(Image.new('RGB', (256, 256)), 'makeup'))
    assert error.value.status_code == 503
    assert error.value.detail == subject.UNAVAILABLE


def style(identity, *tags):
    return CatalogStyle(feature='makeup', style_id=identity, name=identity,
                        description='', status='available', tags=tags)


def test_explicit_intensity_exclusions_and_finish_cannot_be_overridden():
    styles = [style('natural', 'natural', 'everyday'), style('smoky', 'bold', 'smoky'),
              style('nude', 'natural', 'matte'), style('peach', 'soft', 'peach')]
    assert [s.style_id for s in candidate_styles(styles, Preferences(makeup_intensity='natural', makeup_finish='matte'))] == ['nude']
    assert 'smoky' not in {s.style_id for s in candidate_styles(styles, Preferences(avoids=['dramatic makeup']))}
    assert style_score(styles[0], Preferences(occasion='office')) > style_score(styles[1], Preferences(occasion='office'))


def test_valid_but_irrelevant_provider_choices_are_reranked():
    from datetime import datetime, timezone
    from uuid import uuid4
    from app.consultation.models import CatalogResponse, ConsultationState
    from app.consultation.recommend import validate_recommendations
    now = datetime.now(timezone.utc)
    preferences = Preferences(occasion='office')
    state = ConsultationState(id=uuid4(), primary_service='makeup', preferences=preferences,
                              created_at=now, updated_at=now, expires_at=now)
    styles = [style('daily_a', 'everyday'), style('daily_b', 'everyday'),
              style('daily_c', 'everyday'), style('party_a', 'evening'),
              style('party_b', 'evening'), style('party_c', 'evening')]
    candidates = {'makeup': candidate_styles(styles, preferences)}
    raw = {'recommendations': [
        {'primary': {'feature': 'makeup', 'style_id': identity},
         'reason': 'Invented flattering claim'}
        for identity in ('party_a', 'party_b', 'party_c')]}
    result = validate_recommendations(raw, state,
        CatalogResponse(services=[], styles={'makeup': styles}), candidates)
    assert {row.primary.style_id for row in result.recommendations} == {'daily_a', 'daily_b', 'daily_c'}
    assert all('everyday' in row.reason and 'Invented' not in row.reason for row in result.recommendations)

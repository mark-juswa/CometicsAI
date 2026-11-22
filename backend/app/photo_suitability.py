"""Local subject checks. No identity inference, cloud requests or generation."""
import asyncio
from hashlib import sha256
import os
from pathlib import Path
from threading import Lock

from fastapi import HTTPException
from PIL import Image

FACE_MODEL_SHA256 = 'b4578f35940bf5a1a655214a1cce5cab13eba73c1297cd78e1a04c2380b0152f'
FACE_MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite'
ROOT = Path(__file__).resolve().parents[2]
MESSAGES = {
    'makeup': 'Makeup requires one clear face. Upload a well-lit portrait, not a hand or another object.',
    'hairstyle': 'Hair preview requires one clear face with the head and hair in frame. Upload a portrait, not a hand or another object.',
    'nails': 'Nails requires one clear hand with visible nails. Upload a hand photo, not a portrait or another object.',
}
UNAVAILABLE = 'Photo checking is temporarily unavailable. Please try again later.'
_lock = Lock()
_face = None
_hand = None


def portrait_is_usable(image: Image.Image) -> bool:
    global _face
    import mediapipe as mp
    import numpy as np
    path = Path(os.getenv('PHOTO_FACE_MODEL_PATH', str(ROOT / 'data/vision/blaze_face_short_range.tflite')))
    if _face is None:
        if sha256(path.read_bytes()).hexdigest() != FACE_MODEL_SHA256:
            raise RuntimeError('Face asset integrity failed')
        _face = mp.tasks.vision.FaceDetector.create_from_options(mp.tasks.vision.FaceDetectorOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(path)), min_detection_confidence=0.65))
    analysis = image.convert('RGB').copy()
    analysis.thumbnail((1024, 1024))
    result = _face.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.asarray(analysis)))
    if len(result.detections) != 1:
        return False
    box = result.detections[0].bounding_box
    w, h = analysis.size
    return (box.width / w >= 0.15 and box.height / h >= 0.15
            and box.width * box.height / (w * h) >= 0.03
            and box.origin_x >= -0.1 * box.width and box.origin_y >= -0.1 * box.height
            and box.origin_x + box.width <= w + 0.1 * box.width
            and box.origin_y + box.height <= h + 0.1 * box.height)


def check_subject(image: Image.Image, feature: str) -> bool:
    global _hand
    if feature not in MESSAGES:
        raise ValueError('Unknown photo service')
    # MediaPipe instances are reused, with serialized access across API requests.
    with _lock:
        if feature in ('makeup', 'hairstyle'):
            return portrait_is_usable(image)
        from app.nails.geometry import MediaPipeHandLocalizer, UnusableHand
        if _hand is None:
            path = Path(os.getenv('NAILS_HAND_LANDMARKER_PATH', str(
                ROOT / 'data/nails/checkpoints/mediapipe/hand_landmarker.task')))
            _hand = MediaPipeHandLocalizer(path)
        try:
            _hand.locate(image)
            return True
        except UnusableHand:
            return False


async def ensure_photo_subject(image: Image.Image, feature: str) -> None:
    try:
        usable = await asyncio.to_thread(check_subject, image, feature)
    except Exception:
        # Never relay native detector errors, filesystem paths, or photo contents.
        raise HTTPException(503, UNAVAILABLE) from None
    if not usable:
        raise HTTPException(422, MESSAGES[feature])

"""Acquire only the pinned public MediaPipe asset, never user photos."""
from hashlib import sha256
from pathlib import Path
import sys
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.photo_suitability import FACE_MODEL_SHA256, FACE_MODEL_URL

if __name__ == '__main__':
    target = ROOT / 'data/vision/blaze_face_short_range.tflite'
    if target.exists():
        raw = target.read_bytes()
    else:
        raw = urlopen(FACE_MODEL_URL, timeout=45).read(1024 * 1024)
    if sha256(raw).hexdigest() != FACE_MODEL_SHA256:
        raise ValueError('Face detector integrity check failed; existing files preserved')
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        with target.open('xb') as output:
            output.write(raw)
    print('Pinned local face detector ready:', target)

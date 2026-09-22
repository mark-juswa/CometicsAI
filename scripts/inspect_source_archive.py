"""Read the pinned FaceSketches ZIP directory through HTTP ranges, without images."""

from collections import Counter
from io import RawIOBase
from pathlib import PurePosixPath
from zipfile import ZipFile

import requests
from huggingface_hub import hf_hub_url


REPO = "yikaiwang/FaceSketches-HairStyle40"
REVISION = "45de974926fe64551fc2d0b80973335e20ca10e2"


class RangeReader(RawIOBase):
    def __init__(self, url: str):
        self.session = requests.Session()
        response = self.session.get(url, headers={"Range": "bytes=-1"}, timeout=60)
        response.raise_for_status()
        assert response.status_code == 206, "Archive host does not support byte ranges"
        self.url = response.url
        self.size = int(response.headers["Content-Range"].split("/")[1])
        self.position = 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        self.position = (0 if whence == 0 else self.position if whence == 1 else self.size) + offset
        return self.position

    def read(self, length=-1):
        if length < 0:
            length = self.size - self.position
        if not length:
            return b""
        end = min(self.size, self.position + length) - 1
        response = self.session.get(
            self.url,
            headers={"Range": f"bytes={self.position}-{end}"},
            timeout=120,
        )
        response.raise_for_status()
        assert response.status_code == 206, "Range request unexpectedly returned a full archive"
        self.position += len(response.content)
        return response.content


url = hf_hub_url(REPO, "FaceSketches-HairStyle40.zip", repo_type="dataset", revision=REVISION)
reader = RangeReader(url)
print(f"repo={REPO} revision={REVISION} archive_bytes={reader.size}")
with ZipFile(reader) as archive:
    images = Counter()
    other = Counter()
    examples = {}
    for info in archive.infolist():
        if info.is_dir():
            continue
        parts = PurePosixPath(info.filename.replace("\\", "/")).parts
        if "image" in parts:
            index = parts.index("image")
            if len(parts) >= index + 3:
                category = parts[index + 1]
                images[category] += 1
                examples.setdefault(category, info.filename)
        elif "sketches" in parts:
            other["sketches"] += 1
        else:
            other["other"] += 1
    print("original_photo_folders:")
    for category, count in sorted(images.items()):
        print(f"  {category}: {count} example={examples[category]}")
    print("other_files:", dict(other))

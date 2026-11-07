"""Offline learned local cosmetic features. Never imported by serving workers.

Uses pinned author weights on CPU. This is not our trained MAKEUP adapter.
"""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import time

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REVISION = "d033d3398751684eb8c4b5aef54c74b84f3a3ef8"
CHECKPOINT_SHA256 = "71473aa3abad4f66536cef89ab179851547811f1153e846333fa167655776737"


def array_hash(value):
    return sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def prepare_inputs(rgb, labels, points, torch):
    """Explicit Segformer19/SPIGA68 adaptation to the author's model inputs.

    SPIGA coordinates are x,y; the model uses y,x. Source pixels are not warped.
    The semantic masks correspond to the author's prepared lip/face union.
    """
    points = np.asarray(points, np.float32)
    if (rgb.shape != (512, 512, 3) or rgb.dtype != np.uint8 or labels.shape != (512, 512)
            or not np.issubdtype(labels.dtype, np.integer) or labels.min() < 0 or labels.max() > 18
            or points.shape != (68, 2) or not np.isfinite(points).all()
            or np.any((points < 0) | (points >= 512))):
        raise ValueError("Expected source512RGB, parser19 and true68pixel landmarks")
    if np.isin(labels, (11, 12)).sum() < 100 or (labels == 1).sum() < 10000:
        raise ValueError("Insufficient facial support")
    image = np.asarray(Image.fromarray(rgb).resize((256, 256), Image.Resampling.LANCZOS)).astype(np.float32) / 127.5 - 1
    small = cv2.resize(labels, (256, 256), interpolation=cv2.INTER_NEAREST)
    mask = np.stack([np.isin(small, (11, 12)), np.isin(small, (1, 2, 4, 5, 6, 7))]).astype(np.float32)
    yx = np.rint(points[:, ::-1] * .5).clip(0, 255).astype(np.float32)
    # Preserve the author's explicit separation of inner upper/lower lip points.
    yx[61:64, 0] -= 1
    yx[65:68, 0] += 1
    for index in range(3):
        if np.array_equal(yx[61 + index], yx[67 - index]):
            yx[61 + index, 0] -= 1
            yx[67 - index, 0] += 1
    yy, xx = np.mgrid[:256, :256]
    grid = np.concatenate([np.repeat(yy[None], 68, axis=0), np.repeat(xx[None], 68, axis=0)])
    diff = grid - yx.T.reshape(-1, 1, 1)
    return [torch.from_numpy(np.ascontiguousarray(value)).float().unsqueeze(0)
            for value in (image.transpose(2, 0, 1), mask, diff, yx)]


class LocalCosmeticFeatures:
    def __init__(self, workspace):
        import torch
        self.torch = torch
        self.workspace = Path(workspace).resolve()
        if not self.workspace.is_relative_to(ROOT):
            raise ValueError("Provider workspace escapes project")
        snapshot = json.loads((self.workspace / "source-snapshot.json").read_text(encoding="utf-8"))
        if snapshot["commit"] != REVISION:
            raise ValueError("Feature provider source revision differs")
        for row in snapshot["files"]:
            file = (self.workspace / "source" / row["path"]).resolve()
            if not file.is_relative_to(self.workspace / "source") or sha256(file.read_bytes()).hexdigest() != row["sha256"]:
                raise ValueError("Feature provider source changed")
        weight = self.workspace / "sow_pyramid_a5_e3d2_remapped.pth"
        if sha256(weight.read_bytes()).hexdigest() != CHECKPOINT_SHA256:
            raise ValueError("Feature provider checkpoint changed")
        spec = importlib.util.spec_from_file_location("_makeup_elegant", self.workspace / "source/models/__init__.py",
                                                      submodule_search_locations=[str(self.workspace / "source/models")])
        package = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = package
        spec.loader.exec_module(package)
        from _makeup_elegant.elegant import Generator
        torch.set_num_threads(4)
        self.model = Generator(num_layer_e=3, num_layer_d=2)
        self.model.load_state_dict(torch.load(weight, map_location="cpu", weights_only=True), strict=True)
        self.model.eval()
        self.cache = {}
        self.self_cache = {}

    def encode(self, rgb, labels, points):
        key = (array_hash(rgb), array_hash(labels), array_hash(np.asarray(points, np.float32)))
        if key not in self.cache:
            if len(self.cache) >= 20:
                raise ValueError("Bounded offline feature cache is full")
            inputs = prepare_inputs(rgb, labels, points, self.torch)
            with self.torch.inference_mode():
                self.cache[key] = self.model.get_transfer_input(*inputs)
        return key, self.cache[key]

    def decode(self, content, attention):
        # Upstream decode replaces entries in the input list. Never pass a cache
        # list directly, or results depend on which style was generated before.
        return self.model.decode([value.clone() for value in content[0]], [value.clone() for value in attention])

    def counterfactual(self, original, labels, points, reference, ref_labels, ref_points, coverage):
        if (coverage.shape != (512, 512) or coverage.dtype != np.float32
                or not np.isfinite(coverage).all() or np.any((coverage < 0) | (coverage > 1))):
            raise ValueError("Expected finite source coverage")
        started = time.perf_counter()
        source_key, content = self.encode(original, labels, points)
        _, style = self.encode(reference, ref_labels, ref_points)
        with self.torch.inference_mode():
            if source_key not in self.self_cache:
                own = self.model.get_transfer_output(*content, *content)
                baseline = self.decode(content, own)
                self.self_cache[source_key] = (own, baseline.clone())
            own, baseline = self.self_cache[source_key]
            other = self.model.get_transfer_output(*content, *style)
            weight = self.torch.from_numpy(coverage).unsqueeze(0).unsqueeze(0)
            attention = []
            for self_feature, selected_feature in zip(own, other):
                alpha = self.torch.nn.functional.interpolate(weight, self_feature.shape[2:], mode="bilinear", align_corners=False)
                attention.append(self_feature * (1 - alpha) + selected_feature * alpha)
            edited = self.decode(content, attention)
            arrays = [(value.squeeze(0).permute(1, 2, 0).cpu().numpy() + 1) / 2
                      for value in (baseline, edited)]
        if not all(np.isfinite(value).all() for value in arrays):
            raise ValueError("Nonfinite neural cosmetic field")
        return arrays[0], arrays[1], {"provider": "EleGANt-local-features", "source_revision": REVISION,
                                     "checkpoint_sha256": CHECKPOINT_SHA256, "device": "cpu",
                                     "seconds": time.perf_counter() - started,
                                     "preprocessing": "Segformer19/SPIGA68 adaptation, differs from author dlib/BiSeNet",
                                     "our_trained_makeup_adapter": False}

from __future__ import annotations
import cv2
import numpy as np

from . import typealias as tp
from pathlib import Path


def load_image(image: str | Path | bytes | tp.Image, flags: cv2.ImreadModes = cv2.IMREAD_COLOR) -> tp.Image:
    if isinstance(image, str | Path):
        return cv2.imdecode(np.fromfile(image, dtype=np.uint8), flags)
    elif isinstance(image, bytes | bytearray | memoryview):
        return cv2.imdecode(np.frombuffer(image, dtype=np.uint8), flags)
    else:
        return image


def save_image(image: tp.Image, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    success, buffer = cv2.imencode('.png', image)
    path.write_bytes(buffer)


def linear_operation(image: tp.Image, min: int, max: int) -> tp.Image:
    image = (image.astype(np.float32) - min) / (max - min) * 255
    return np.clip(image, 0, 255).astype(np.uint8)


def scope2slice(scope: tp.Scope | None) -> tp.Slice:
    """ ((x0, y0), (x1, y1)) -> (slice(y0, y1), slice(x0, x1)) """
    if scope is None:
        return slice(None), slice(None)
    (x0, y0), (x1, y1) = scope
    return slice(y0, y1), slice(x0, x1)

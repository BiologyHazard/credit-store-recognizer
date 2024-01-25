from __future__ import annotations
import cv2
import numpy as np

from . import typealias as tp
from .log import logger
from pathlib import Path


# def bytes2img(data: bytes, gray: bool = False) -> Union[tp.Image, tp.GrayImage]:
#     """ bytes -> image """
#     if gray:
#         return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_GRAYSCALE)
#     else:
#         return cv2.cvtColor(
#             cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR),
#             cv2.COLOR_BGR2RGB,
#         )


# def img2bytes(img) -> bytes:
#     """ bytes -> image """
#     return cv2.imencode('.png', img)[1]


# def load_image(filename: str, gray: bool = False) -> Image | GrayImage:
#     """ load image from file """
#     logger.debug(filename)
#     if gray:
#         return cv2.imdecode(np.fromfile(filename, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
#     else:
#         # return cv2.cvtColor(cv2.imdecode(np.fromfile(filename, dtype=np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
#         return cv2.imdecode(np.fromfile(filename, dtype=np.uint8), cv2.IMREAD_COLOR)


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
    """ ((x0, y0), (x1, y1)) -> ((y0, y1), (x0, x1)) """
    if scope is None:
        return slice(None), slice(None)
    (x0, y0), (x1, y1) = scope
    return slice(y0, y1), slice(x0, x1)


# def cropimg(img: tp.Image, scope: tp.Scope) -> tp.Image:
#     """ crop image """
#     return img[scope2slice(scope)]


# def saveimg(img, folder='failure'):
#     # save_screenshot(
#     #     img2bytes(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)),
#     #     subdir=f'{folder}/{img.shape[0]}x{img.shape[1]}',
#     # )
#     pass

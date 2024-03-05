from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from credit_store_recognizer.ocr import ocrhandle
from credit_store_recognizer.solvers.shop import CreditStore


class Logger:
    def __getattr__(self, name):
        return print


logger = Logger()

shop_items = [
    "讯使",
    "嘉维尔",
    "坚雷",
    "招聘许可",
    "龙门币",
    "技巧概要·卷2",
    "初级作战记录",
    "基础作战记录",
    "技巧概要·卷1",
    "异铁",
    "装置",
    "酮凝集",
    "固源岩",
    "糖",
    "聚酸酯",
    "赤金",
    "代糖",
    "异铁碎片",
    "酯原料",
    "双酮",
    "破损装置",
    "源岩",
    "碳",
    "碳素",
    "家具零件",
    "加急许可"
]


def load_image(image, flags: cv2.ImreadModes = cv2.IMREAD_COLOR):
    if isinstance(image, (str, Path)):
        return cv2.imdecode(np.fromfile(image, dtype=np.uint8), flags)
    elif isinstance(image, (bytes, bytearray, memoryview)):
        return cv2.imdecode(np.frombuffer(image, dtype=np.uint8), flags)
    else:
        return image


def save_image(image, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    success, buffer = cv2.imencode('.png', image)
    path.write_bytes(buffer)


def linear_operation(image, min: int, max: int):
    image = (image.astype(np.float32) - min) / (max - min) * 255
    return np.clip(image, 0, 255).astype(np.uint8)


def scope2slice(scope):
    """ ((x0, y0), (x1, y1)) -> ((y0, y1), (x0, x1)) """
    if scope is None:
        return slice(None), slice(None)
    (x0, y0), (x1, y1) = scope
    return slice(y0, y1), slice(x0, x1)


scopes = [
    ((25, 222), (378, 576)),
    ((405, 222), (757, 576)),
    ((784, 222), (1137, 576)),
    ((1164, 222), (1516, 576)),
    ((1544, 222), (1896, 576)),
    ((25, 603), (378, 957)),
    ((405, 603), (757, 957)),
    ((784, 603), (1137, 957)),
    ((1164, 603), (1516, 957)),
    ((1544, 603), (1896, 957)),
]

sold_out_image = load_image('credit_store_recognizer/resources/sold_out.png')


def get_item_image(image, index: int):
    return image[scope2slice(scopes[index])]


seen = set()


def get_item_name(item_image, sold: bool):
    scope = ((16, 0), (353-16, 54))
    item_name_segment = item_image[scope2slice(scope)]
    item_name_segment = cv2.cvtColor(item_name_segment, cv2.COLOR_BGR2GRAY)
    min_value, max_value = (177, 205) if sold else (49, 255)
    item_name_segment = linear_operation(item_name_segment, min_value, max_value)
    item_name_segment_to_ocr = np.vstack((item_name_segment, np.zeros(item_name_segment.shape, dtype=np.uint8), np.zeros(item_name_segment.shape, dtype=np.uint8)))
    item_name_segment_to_ocr = cv2.cvtColor(item_name_segment_to_ocr, cv2.COLOR_GRAY2BGR)
    # cv2.imshow('item_name_segment', item_name_segment)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    ocr = ocrhandle.predict(item_name_segment_to_ocr, False)
    if len(ocr) == 0:
        logger.error(('OCR未返回结果'))
        cv2.imshow('item_name_segment', item_name_segment)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return

    item_name = ocr[0][1]
    if item_name not in shop_items:
        logger.error(('OCR结果不在列表中', item_name))
        cv2.imshow('item_name_segment', item_name_segment)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return

    if item_name not in seen:
        seen.add(item_name)
        save_image(item_name_segment, f'resources/{item_name}.png')

    if set(shop_items) == seen:
        exit()


def is_sold(item_img) -> bool:
    res = cv2.matchTemplate(item_img, sold_out_image, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if max_val > 0.8:
        return True
    return False


# folder = Path(r'D:\BioHazard\Documents\Arknights\信用商店统计\信用商店截图')
# folder = Path(r'C:\Users\Administrator\Documents\MuMu共享文件夹\Screenshots')
# for path in folder.rglob('*.png'):
#     image = load_image(path)
#     if image.shape != (1080, 1920, 3):
#         continue
#     for index in range(10):
#         item_image = get_item_image(image, index)
#         sold = is_sold(item_image)
#         if sold:
#             continue
#         get_item_name(item_image, sold)


# folder = Path(r'D:\BioHazard\Documents\Arknights\信用商店统计\信用商店截图识别结果')
# for path in folder.rglob('*.json'):
#     with open(path, 'r', encoding='utf-8') as fp:
#         data = json.load(fp)
#     credit_store = CreditStore.from_json(data)
#     if any(item.name in ('坚雷') and not item.sold for item in credit_store.items):
#         print(path)


# image = load_image(r'D:\BioHazard\Documents\Arknights\信用商店统计\信用商店截图\CreditStore-20240210-154119-24-官服-eve#7543.png')
# for index in range(10):
#     item_image = get_item_image(image, index)
#     sold = is_sold(item_image)
#     if sold:
#         continue
#     get_item_name(item_image, sold)

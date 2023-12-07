from __future__ import annotations

import cv2
import numpy as np
from matplotlib import pyplot as plt

from . import typealias as tp
from .log import logger


def get_poly(x1: int, x2: int, y1: int, y2: int) -> tp.Rectangle:
    x1, x2 = int(x1), int(x2)
    y1, y2 = int(y1), int(y2)
    return np.array([[x1, y1], [x1, y2], [x2, y2], [x2, y1]])


def credit(img: tp.Image, draw: bool = False) -> list[tp.Scope]:
    """
    信用交易所特供的图像分割算法
    """
    # height, width, _ = img.shape

    # left, right = 0, width
    # while np.max(img[:, right - 1]) < 100:
    #     right -= 1
    # while np.max(img[:, left]) < 100:
    #     left += 1

    # def average(i: int) -> int:
    #     num, sum = 0, 0
    #     for j in range(left, right):
    #         if img[i, j, 0] == img[i, j, 1] and img[i, j, 1] == img[i, j, 2]:
    #             num += 1
    #             sum += img[i, j, 0]
    #     return sum // num

    # def ptp(j: int) -> int:
    #     maxval = -999999
    #     minval = 999999
    #     for i in range(up_1, up_2):
    #         minval = min(minval, img[i, j, 0])
    #         maxval = max(maxval, img[i, j, 0])
    #     return maxval - minval

    # up_1 = 0
    # flag = False
    # while not flag or average(up_1) >= 250:
    #     flag |= average(up_1) >= 250  # numpy.bool_
    #     up_1 += 1

    # up_2 = up_1
    # flag = False
    # while not flag or average(up_2) < 220:
    #     flag |= average(up_2) < 220
    #     up_2 += 1

    # down = height - 1
    # while average(down) < 180:
    #     down -= 1

    # right = width - 1
    # while ptp(right) < 50:
    #     right -= 1

    # left = 0
    # while ptp(left) < 50:
    #     left += 1

    # split_x = [left + (right - left) // 5 * i for i in range(0, 6)]
    # split_y = [up_1, (up_1 + down) // 2, down]

    # ret = []
    # for y1, y2 in zip(split_y[:-1], split_y[1:]):
    #     for x1, x2 in zip(split_x[:-1], split_x[1:]):
    #         ret.append(((x1, y1), (x2, y2)))

    # if draw:
    #     for y1, y2 in zip(split_y[:-1], split_y[1:]):
    #         for x1, x2 in zip(split_x[:-1], split_x[1:]):
    #             cv2.polylines(img, [get_poly(x1, x2, y1, y2)],
    #                           True, 0, 10, cv2.LINE_AA)
    #     plt.imshow(img)
    #     plt.show()

    ret = [
        ((25, 222), (399, 588)),
        ((399, 222), (773, 588)),
        ((773, 222), (1147, 588)),
        ((1147, 222), (1521, 588)),
        ((1521, 222), (1895, 588)),
        ((25, 588), (399, 955)),
        ((399, 588), (773, 955)),
        ((773, 588), (1147, 955)),
        ((1147, 588), (1521, 955)),
        ((1521, 588), (1895, 955)),
    ]
    if draw:
        for pt1, pt2 in ret:
            cv2.rectangle(img, pt1, pt2, (0, 0, 0), 5)
        cv2.imshow('', img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    logger.debug(f'segment.credit: {ret}')
    return ret

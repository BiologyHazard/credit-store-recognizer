import os
from pathlib import Path

import cv2
import numpy as np

from . import __rootdir__
from .image import load_image
from . import typealias as tp


class DigitReader:
    def __init__(self):
        self.recruit_template: list[tp.Image] = [
            load_image(f'{__rootdir__}/resources/recruit_ticket/{i}.png', cv2.IMREAD_GRAYSCALE)
            for i in range(10)
        ]
        self.spent_credit_number: list[tp.Image] = [
            load_image(f'{__rootdir__}/resources/spent_credit_number/{i}.png', cv2.IMREAD_GRAYSCALE)
            for i in range(10)
        ]

    def get_recruit_ticket(self, image) -> int:
        result = {}
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        for j in range(10):
            res = cv2.matchTemplate(
                image,
                self.recruit_template[j],
                cv2.TM_CCORR_NORMED,
            )
            threshold = 0.90
            loc = np.where(res >= threshold)
            for i in range(len(loc[0])):
                x = loc[1][i]
                accept = True
                for o in result:
                    if abs(o - x) < 5:
                        accept = False
                        break
                if accept:
                    result[loc[1][i]] = j

        l = [str(result[k]) for k in sorted(result)]
        return int(''.join(l))

    def get_discount(self, image):
        result = {}
        # digit_part = cv2.cvtColor(digit_part, cv2.COLOR_RGB2GRAY)
        image = image[:, :, 1]  # green channel
        image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        # cv2.imshow('', digit_part)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        for j in (0, 5, 7, 9):
            templ = self.recruit_template[j]
            templ = cv2.threshold(templ, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            # cv2.imshow('', templ)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()

            res = cv2.matchTemplate(
                image,
                # self.recruit_template[j],
                templ,
                cv2.TM_CCORR_NORMED,
            )
            threshold = 0.75
            loc = np.where(res >= threshold)
            # print(max(res.flatten()))
            # print(loc)
            for i in range(len(loc[0])):
                x = loc[1][i]
                accept = True
                for o in result:
                    if abs(o - x) < 5:
                        accept = False
                        break
                if accept:
                    result[loc[1][i]] = j

        l = [str(result[k]) for k in sorted(result)]
        s = "".join(l)
        if s == "":
            return 0
        return int("".join(l))

    def get_credit_number(self, digit_part):
        result = {}
        digit_part = cv2.cvtColor(digit_part, cv2.COLOR_RGB2GRAY)

        for j in range(10):
            res = cv2.matchTemplate(
                digit_part,
                self.spent_credit_number[j],
                cv2.TM_CCOEFF_NORMED,
            )
            threshold = 0.9
            loc = np.where(res >= threshold)
            for i in range(len(loc[0])):
                x = loc[1][i]
                accept = True
                for o in result:
                    if abs(o - x) < 5:
                        accept = False
                        break
                if accept:
                    result[loc[1][i]] = j

        l = [str(result[k]) for k in sorted(result)]

        return int("".join(l))

import os
from pathlib import Path

import cv2
import numpy as np

from .. import __rootdir__
from .image import loadimg


class DigitReader:
    def __init__(self, template_dir=None):
        if not template_dir:
            template_dir = Path(os.path.dirname(os.path.abspath(__file__))) / Path("templates")
        if not isinstance(template_dir, Path):
            template_dir = Path(template_dir)
        self.recruit_template = []
        self.spent_credit_number = []
        for i in range(10):
            self.recruit_template.append(
                loadimg(f'{__rootdir__}/resources/recruit_ticket/{i}.png', True)
            )
            self.spent_credit_number.append(
                loadimg(f'{__rootdir__}/resources/spent_credit_number/{i}.png', True)
            )

    def get_recruit_ticket(self, digit_part):
        result = {}
        digit_part = cv2.cvtColor(digit_part, cv2.COLOR_RGB2GRAY)

        for j in range(10):
            res = cv2.matchTemplate(
                digit_part,
                self.recruit_template[j],
                cv2.TM_CCORR_NORMED,
            )
            threshold = 0.94
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

    def get_credit_number(self, digit_part):
        result = {}
        digit_part = cv2.cvtColor(digit_part, cv2.COLOR_RGB2GRAY)

        for j in range(10):
            res = cv2.matchTemplate(
                digit_part,
                self.spent_credit_number[j],
                cv2.TM_CCOEFF_NORMED,
            )
            threshold = 0.95
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

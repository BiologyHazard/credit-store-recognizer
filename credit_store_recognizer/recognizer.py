from __future__ import annotations

import os
from pathlib import Path

import cv2
import numpy as np

from .credit_store import CreditStore, CreditStoreItem

from . import __rootdir__
from . import typealias as tp
from .data import credit_store_items
from .digit_reader import DigitReader
from .image import linear_operation, load_image, save_image, scope2slice
from .log import logger

scopes: list[tp.Scope] = [
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


def generate_template(item_name: str) -> tp.ColorImage:
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(f'{__rootdir__}/fonts/SourceHanSansCN-Medium.otf', 30)
    # left, top, right, bottom = font.getbbox(item_name)
    width, height = 300, 40  # right - left, bottom - top
    image = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(image)
    draw.text((width / 2, height / 2), item_name, 255, font, anchor='mm', features=['halt'])
    return np.array(image)


class CreditStoreRecognizer:
    def __init__(self) -> None:
        self.sold_out_image = load_image(f"{__rootdir__}/resources/sold_out.png")
        # self.credit_icon = load_image(f"{__rootdir__}/resources/credit_icon.png")
        # self.spent_credit = load_image(f"{__rootdir__}/resources/spent_credit.png")

        # self.item_credit_icon = load_image(f"{__rootdir__}/resources/item_credit_icon.png")
        # self.sold_credit_icon = load_image(f"{__rootdir__}/resources/sold_credit_icon.png")

        self.digit_reader = DigitReader()
        # self.discount = {}
        # self.discount_sold = {}
        # for item in os.listdir(f"{__rootdir__}/resources/shop_discount"):
        #     self.discount[item.replace(".png", "")] = load_image(f"{__rootdir__}/resources/shop_discount/{item}")
        # for item in os.listdir(f"{__rootdir__}/resources/shop_discount"):
        #     self.discount_sold[item.replace(".png", "")] = load_image(f"{__rootdir__}/resources/shop_discount_sold/{item}")

        self.item_name_templates = {
            item_name: generate_template(item_name)
            for item_name in credit_store_items
        }
        # for item_name, template in self.item_name_templates.items():
        #     save_image(template, f'{item_name}.png')
        self.sold_price_number = {}
        for item in os.listdir(f"{__rootdir__}/resources/sold_price_number"):
            self.sold_price_number[item.replace(".png", "")] = load_image(
                f"{__rootdir__}/resources/sold_price_number/{item}")

    def recognize(self, image: tp.ColorImage) -> CreditStore:
        if image.shape != (1920, 1080, 3):
            raise ValueError(f'image.shape must be (1920, 1080, 3), but got: {image.shape}')
        credit: int = self.get_credits(image)
        items: list[CreditStoreItem] = []
        for i in range(10):
            item_image: tp.Image = self.get_item_image(image, i)
            item_name = self.get_item_name(item_image)

            shop_sold, discount = self.get_discount(image[scope2slice(scope)])

            if item_name == '龙门币' or item_name == '家具零件':
                current_price = self.get_item_price(image[scope2slice(scope)], shop_sold)
                original_price = round(current_price / (1 - discount * 0.01))
                if item_name == '龙门币':
                    if original_price == 200:
                        item_name = "龙门币大"
                    elif original_price == 100:
                        item_name = "龙门币小"
                    else:
                        logger.error((i, item_name, current_price))
                elif item_name == '家具零件':
                    if original_price == 200:
                        item_name = "家具零件大"
                    elif original_price == 160:
                        item_name = "家具零件小"
                    else:
                        logger.error((i, item_name, original_price))

            items.append(CreditStoreItem(name=item_name, discount=discount, sold=shop_sold))

        return CreditStore(credit=credit, items=items)

    def get_item_image(self, image: tp.ColorImage, index: int) -> tp.ColorImage:
        return image[scope2slice(scopes[index])]

    def get_item_name(self, item_image: tp.ColorImage, sold: bool) -> str:
        scope = ((16, 0), (353-16, 54))
        item_name_segment = item_image[scope2slice(scope)]
        item_name_segment = cv2.cvtColor(item_name_segment, cv2.COLOR_BGR2GRAY)
        min_value, max_value = (177, 205) if sold else (49, 255)
        item_name_segment = linear_operation(item_name_segment, min_value, max_value)
        save_image(item_name_segment, 'item_name_segment.png')
        for item_name, template in self.item_name_templates.items():
            res = cv2.matchTemplate(item_name_segment, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            print(item_name, max_val)
            if max_val > 0.8:
                return item_name
        raise ValueError(f'Cannot recognize item name.')

    def get_discount(self, item_img) -> tuple[bool, int]:
        # 用digitReader识别折扣
        sold = self.is_sold(item_img)
        digit_part = item_img[54:106, 0:97]
        discount = self.digit_reader.get_discount(digit_part)
        if discount not in (0, 50, 75, 95, 99):
            logger.error(f'折扣识别错误: {discount}')
            raise
        return sold, discount

        # 所有图片都匹配一遍，取最可能的
        # most_probable_key = '0'
        # most_probable_value = 0
        # for key in self.discount:
        #     templ = self.discount_sold[key] if sold else self.discount[key]
        #     res = cv2.matchTemplate(item_img, templ, cv2.TM_CCOEFF_NORMED)
        #     min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        #     if max_val > most_probable_value:
        #         most_probable_key = key
        #         most_probable_value = max_val
        # if most_probable_value > 0.8:
        #     return sold, int(most_probable_key)
        # else:
        #     return sold, 0

    def is_sold(self, item_img) -> bool:
        res = cv2.matchTemplate(item_img, self.sold_out_image, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > 0.8:
            return True
        return False

    def get_credits(self, img) -> int:
        res = cv2.matchTemplate(img, self.credit_icon, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        h, w = self.credit_icon.shape[:-1]
        p0 = [max_loc[0] + w, max_loc[1]]
        p1 = [p0[0] + 90, p0[1] + 40]

        # cv2.imshow('', img[p0[1]:p1[1], p0[0]:p1[0]])
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        return self.digit_reader.get_recruit_ticket(img[p0[1]:p1[1], p0[0]:p1[0]])

    def get_spent_credits(self, img) -> int:
        res = cv2.matchTemplate(img, self.spent_credit, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        h, w = self.spent_credit.shape[:-1]
        p0 = [max_loc[0] + w, max_loc[1]]
        p1 = [p0[0] + 200, p0[1] + 60]
        spent_credits = self.digit_reader.get_credit_number(img[p0[1]:p1[1], p0[0]:p1[0]])
        return spent_credits

    def get_item_price(self, item_img, is_sold=False) -> int:
        if is_sold:
            res = cv2.matchTemplate(item_img, self.sold_credit_icon, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

            h, w = self.item_credit_icon.shape[:-1]
            p0 = [max_loc[0] + w, max_loc[1]]
            p1 = [p0[0] + 140, p0[1] + 40]
            return self.get_sold_number(item_img[p0[1]:p1[1], p0[0]:p1[0]])
        else:
            res = cv2.matchTemplate(item_img, self.item_credit_icon, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            h, w = self.item_credit_icon.shape[:-1]
            p0 = [max_loc[0] + w, max_loc[1]]
            p1 = [p0[0] + 140, p0[1] + 40]
            return self.digit_reader.get_credit_number(item_img[p0[1]:p1[1], p0[0]:p1[0]])

    def get_sold_number(self, digit_part: np.ndarray) -> int:
        result = {}
        for j in self.sold_price_number.keys():
            res = cv2.matchTemplate(
                digit_part,
                self.sold_price_number[j],
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


credit_store_recognizer = CreditStoreRecognizer()
recognize = credit_store_recognizer.recognize

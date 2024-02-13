from __future__ import annotations

import os
from typing import Any, NamedTuple

import cv2
import numpy as np

from .. import __rootdir__
from ..data import shop_items
from ..ocr import ocrhandle
from ..utils import segment
from ..utils.digit_reader import DigitReader
from ..utils.image import loadimg, scope2slice
from ..utils.log import logger


class CreditStoreItem(NamedTuple):
    name: str
    discount: int
    sold: bool

    def json(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'discount': self.discount,
            'sold': self.sold,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> CreditStoreItem:
        return cls(
            data['name'],
            data['discount'],
            data['sold'],
        )


class CreditStore(NamedTuple):
    credit: int
    items: list[CreditStoreItem]

    def json(self) -> dict[str, Any]:
        return {
            'credit': self.credit,
            'items': [item.json() for item in self.items],
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> CreditStore:
        return cls(
            data['credit'],
            [CreditStoreItem.from_json(item) for item in data['items']],
        )

    @staticmethod
    def is_same_store(*stores: CreditStore) -> bool:
        # if a.credit != b.credit:
        #     return False
        if len(stores) < 2:
            return True
        for items in zip(*(store.items for store in stores)):
            if not all(item.name == items[0].name for item in items):
                return False
        return True


class ShopSolver:
    def __init__(self) -> None:
        self.sold_template = loadimg(f"{__rootdir__}/resources/sold_out.png")
        self.credit_icon = loadimg(f"{__rootdir__}/resources/credit_icon.png")
        self.spent_credit = loadimg(f"{__rootdir__}/resources/spent_credit.png")

        self.item_credit_icon = loadimg(f"{__rootdir__}/resources/item_credit_icon.png")
        self.sold_credit_icon = loadimg(f"{__rootdir__}/resources/sold_credit_icon.png")

        self.digitReader = DigitReader()
        self.discount = {}
        self.discount_sold = {}
        for item in os.listdir(f"{__rootdir__}/resources/shop_discount"):
            self.discount[item.replace(".png", "")] = loadimg(f"{__rootdir__}/resources/shop_discount/{item}")
        for item in os.listdir(f"{__rootdir__}/resources/shop_discount"):
            self.discount_sold[item.replace(".png", "")] = loadimg(f"{__rootdir__}/resources/shop_discount_sold/{item}")

        self.sold_price_number = {}
        for item in os.listdir(f"{__rootdir__}/resources/sold_price_number"):
            self.sold_price_number[item.replace(".png", "")] = loadimg(
                f"{__rootdir__}/resources/sold_price_number/{item}")

    def recognize(self, img) -> CreditStore:
        scopes = segment.credit(img)
        credit: int = self.get_credits(img)
        items: list[CreditStoreItem] = []
        for i, scope in enumerate(scopes):
            (x0, y0), (x1, y1) = scope
            dx, dy = x1 - x0, y1 - y0
            name_scope = ((x0, y0), (x0 + dx, y0 + dy // 7))
            # scope = (segment_[0], (segment_[1][0], segment_[0][1] + (segment_[1][1] - segment_[0][1]) // 6))
            image_segment = img[scope2slice(name_scope)]
            image_segment = np.vstack((image_segment, np.ones(image_segment.shape, dtype=np.uint8) * 255))
            # image_segment = cv2.cvtColor(img[scope2slice(scope)], cv2.COLOR_BGR2GRAY)
            # threshold, image_segment = cv2.threshold(image_segment, 180, 255, cv2.THRESH_BINARY)
            # image_segment = cv2.cvtColor(image_segment, cv2.COLOR_GRAY2BGR)
            ocr = ocrhandle.predict(image_segment)
            # cv2.imshow('', image_segment)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()
            if len(ocr) == 0:
                # raise RecognizeError
                logger.error((i, 'OCR未返回结果'))
                item_name = 'UNKNOWN'
            item_name = ocr[0][1]
            if item_name not in shop_items:
                logger.error((i, 'OCR结果不在列表中', item_name))
                # item_name = ocr_rectify(img[scope2slice(scope)], ocr, shop_items, '物品名称')

            shop_sold, discount = self.get_discount(img[scope2slice(scope)])

            if item_name == '龙门币' or item_name == '家具零件':
                current_price = self.get_item_price(img[scope2slice(scope)], shop_sold)
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

            items.append(CreditStoreItem(item_name, discount, shop_sold))
            # if not shop_sold:
            #     self.item_list[i] = {
            #         'index': i,
            #         'name': item_name,
            #         'discount': discount,
            #         'shop_sold': shop_sold,
            #         'position': segment_,
            #         'price': round(float(shop_items[item_name]) / (1 - discount * 0.01), 0)
            #     }
            #     logger.info(self.item_list[i])

        return CreditStore(credit, items)
        # self.shop_data["item"] = sorted(self.item_list.values(), key=lambda x: x['price'], reverse=True)
        # logger.info("购买顺序:{}".format([f"{item['index']+1}:{item['name']}" for item in self.shop_data["item"]]))

        # return True
        # self.tap_element("agent_unlock")

    def get_discount(self, item_img) -> tuple[bool, int]:
        # 用digitReader识别折扣
        sold = self.is_sold(item_img)
        digit_part = item_img[54:106, 0:97]
        discount = self.digitReader.get_discount(digit_part)
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
        res = cv2.matchTemplate(item_img, self.sold_template, cv2.TM_CCOEFF_NORMED)
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

        return self.digitReader.get_recruit_ticket(img[p0[1]:p1[1], p0[0]:p1[0]])

    def get_spent_credits(self, img) -> int:
        res = cv2.matchTemplate(img, self.spent_credit, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        h, w = self.spent_credit.shape[:-1]
        p0 = [max_loc[0] + w, max_loc[1]]
        p1 = [p0[0] + 200, p0[1] + 60]
        spent_credits = self.digitReader.get_credit_number(img[p0[1]:p1[1], p0[0]:p1[0]])
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
            return self.digitReader.get_credit_number(item_img[p0[1]:p1[1], p0[0]:p1[0]])

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

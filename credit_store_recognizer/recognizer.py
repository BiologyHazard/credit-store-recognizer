import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import typing as tp
from .credit_store import CreditStore, CreditStoreItem
from .data import credit_store_items
from .image import linear_operation, load_image, scope2slice


class RecognizeError(Exception):
    pass


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


def get_template(item_name: str) -> tp.GrayImage:
    template = load_image(f'templates/credit_store_items/{item_name}.png', cv2.IMREAD_GRAYSCALE)
    height, width = template.shape
    return template[scope2slice(((1, 1), (width-1, height-1)))]


class CreditStoreRecognizer:
    def __init__(self) -> None:
        self.sold_out_image = load_image(f'resources/sold_out.png')
        self.bender_40: list[tp.GrayImage] = [
            load_image(f'templates/bender_40/{i}.png', cv2.IMREAD_GRAYSCALE)
            for i in range(10)
        ]
        self.bender_38: list[tp.GrayImage] = [
            load_image(f'templates/bender_38/{i}.png', cv2.IMREAD_GRAYSCALE)
            for i in range(10)
        ]
        self.sourceHanSansCN_medium_40: list[tp.Image] = [
            load_image(f'templates/SourceHanSansCN-Medium_40/{i}.png', cv2.IMREAD_GRAYSCALE)
            for i in range(10)
        ]

        self.item_name_templates = {
            item_name: get_template(item_name)
            for item_name in credit_store_items
        }

    def recognize(self, image: tp.ColorImage) -> CreditStore:
        if image.shape != (1080, 1920, 3):
            raise ValueError(f'image.shape must be (1080, 1920, 3), but got: {image.shape}')
        credit: int = self.get_credit(image)
        items: list[CreditStoreItem] = []
        for i in range(10):
            item_image: tp.Image = self.get_item_image(image, i)
            sold: bool = self.is_sold(item_image)
            item_name: str = self.get_item_name(item_image, sold)
            discount: int = self.get_discount(item_image)

            if item_name == '龙门币' or item_name == '家具零件':
                current_price: int = self.get_item_price(item_image, sold)
                original_price: int = round(current_price / (1 - discount * 0.01))
                if item_name == '龙门币':
                    if original_price == 200:
                        item_name = '龙门币大'
                    elif original_price == 100:
                        item_name = '龙门币小'
                    else:
                        raise RecognizeError(f'Failed to recognize {i=}, {item_name=}, {current_price=}, {discount=}')
                elif item_name == '家具零件':
                    if original_price == 200:
                        item_name = '家具零件大'
                    elif original_price == 160:
                        item_name = '家具零件小'
                    else:
                        raise RecognizeError(f'Failed to recognize {i=}, {item_name=}, {current_price=}, {discount=}')

            items.append(CreditStoreItem(name=item_name, discount=discount, sold=sold))

        return CreditStore(credit=credit, items=items)

    def get_item_image(self, image: tp.ColorImage, index: int) -> tp.ColorImage:
        return image[scope2slice(scopes[index])]

    def get_item_name(self, item_image: tp.ColorImage, sold: bool) -> str:
        scope = ((16, 0), (353-16, 54))
        item_name_segment = item_image[scope2slice(scope)]
        item_name_segment = cv2.cvtColor(item_name_segment, cv2.COLOR_BGR2GRAY)
        min_value, max_value = (177, 205) if sold else (49, 255)
        item_name_segment = linear_operation(item_name_segment, min_value, max_value)
        scores = {}
        for item_name, template in self.item_name_templates.items():
            res = cv2.matchTemplate(item_name_segment, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            scores[item_name] = max_val

        threshold = 0.70
        name = max(scores, key=lambda k: scores[k])
        if scores[name] >= threshold:
            return name
        raise RecognizeError(f'Failed to recognize item name, but the most similar is {name!r} with score {scores[name]}')

    def get_discount(self, item_img: tp.ColorImage) -> int:
        scope = ((0, 54), (97, 106))
        digit_part = item_img[scope2slice(scope)]
        b, digit_part, r = cv2.split(digit_part)  # green channel
        digit_part = cv2.threshold(digit_part, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        threshold = 0.70
        result = {}
        for num in (0, 5, 7, 9):
            templ = self.bender_38[num]
            templ = cv2.threshold(templ, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            res = cv2.matchTemplate(digit_part, templ, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= threshold)  # type: ignore
            for x in loc[1]:
                if all(abs(o - x) >= 5 for o in result):
                    result[x] = num
        s: str = ''.join(str(result[k]) for k in sorted(result))
        discount: int = int(s) if s else 0

        if discount not in (0, 50, 75, 95, 99):
            raise RecognizeError(f'Failed to recognize discount, but the most similar is {discount}')
        return discount

    def is_sold(self, item_img) -> bool:
        res = cv2.matchTemplate(item_img, self.sold_out_image, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        return max_val > 0.8

    def get_credit(self, image) -> int:
        scope = ((1710, 38), (1710+97, 38+41))
        image = image[scope2slice(scope)]
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image = linear_operation(image, 50, 255)

        threshold = 0.80
        result = {}
        for num in range(10):
            res = cv2.matchTemplate(image, self.bender_40[num], cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= threshold)  # type: ignore
            for x in loc[1]:
                if all(abs(o - x) >= 5 for o in result):
                    result[x] = num
        s: str = ''.join(str(result[k]) for k in sorted(result))
        if s == '':
            raise RecognizeError('Failed to recognize credit')
        return int(s)

    def get_item_price(self, item_img, sold=False) -> int:
        scope = ((10, 294), (344, 345))
        price_segment = item_img[scope2slice(scope)]
        price_segment = cv2.cvtColor(price_segment, cv2.COLOR_BGR2GRAY)
        _, price_segment = cv2.threshold(price_segment, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        threshold = 0.75
        result = {}
        for num in (0, 1, 2, 4, 5, 6, 8):
            templ = self.sourceHanSansCN_medium_40[num]
            templ = cv2.threshold(templ, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            res = cv2.matchTemplate(price_segment, templ, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= threshold)  # type: ignore
            for x in loc[1]:
                if all(abs(o - x) >= 5 for o in result):
                    result[x] = num
        s: str = ''.join(str(result[k]) for k in sorted(result))
        if s == '':
            raise RecognizeError('Failed to recognize item price')
        return int(s)


credit_store_recognizer = CreditStoreRecognizer()
recognize = credit_store_recognizer.recognize


def draw_result(image: Image.Image, result: CreditStore) -> Image.Image:
    credit_pos = (1600, 30)
    font = ImageFont.truetype('credit_store_recognizer/fonts/SourceHanSansCN-Medium.otf', 48)
    draw = ImageDraw.Draw(image)
    draw.text(credit_pos, str(result.credit), 'black', font, stroke_width=5, stroke_fill='white')
    for item, ((x0, y0), (x1, y1)) in zip(result.items, scopes):
        draw.multiline_text((x0, y0 + 100),
                            f'{item.name}\n{item.discount}\n{item.sold}',
                            'black', font, stroke_width=5, stroke_fill='white')
    return image

from __future__ import annotations

import csv
import datetime
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from credit_store_recognizer.solvers.shop import CreditStore, ShopSolver
from credit_store_recognizer.utils.image import loadimg
from credit_store_recognizer.utils.log import logger, set_level

set_level('INFO')

image_path = Path()
output_image_path = Path('image')
output_csv_path = Path('output')


def draw(image: Image.Image, result: CreditStore):
    credit_pos = (1600, 30)
    item_poses = [
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
    font = ImageFont.truetype(
        r'C:\Users\Administrator\AppData\Local\Microsoft\Windows\Fonts\SourceHanSansSC-Regular.otf', 48)
    credits, items = result
    draw = ImageDraw.Draw(image)
    draw.text(credit_pos, str(credits), 'black', font, stroke_width=5, stroke_fill='white')
    for (name, discount, sold), ((x0, y0), (x1, y1)) in zip(items, item_poses):
        draw.multiline_text((x0, y0 + 100),
                            f'{name}\n{discount}\n{sold}',
                            'black', font, stroke_width=5, stroke_fill='white')
    return image


def path_to_datetime(path: Path) -> datetime.datetime:
    date_string = path.stem[7:22]

    date_format = "%Y%m%d-%H%M%S"
    datetime_object = datetime.datetime.strptime(date_string, date_format)
    return datetime_object


def path_to_person(path: Path) -> str:
    person = path.suffixes[0][1:]
    if person == 'png':
        return 'BioHazard'
    return person


def datetime_to_yj_date(t: datetime.datetime) -> datetime.date:
    return (t - datetime.timedelta(hours=4)).date()


@logger.catch
def filter_path(image_path: Path, pass_recognized: bool = True) -> defaultdict[str, dict[datetime.date, Path]]:
    recognized_names = [p.name for p in output_image_path.glob('*.png')]
    paths = list(image_path.glob('*.png'))
    paths.sort(key=lambda path: path_to_datetime(path))
    filtered_paths = defaultdict(dict)
    for path in paths:
        person = path_to_person(path)
        date = datetime_to_yj_date(path_to_datetime(path))
        if pass_recognized and path.name in recognized_names:
            continue
        filtered_paths[person][date] = path
    return filtered_paths


@logger.catch
def main():
    shop_solver = ShopSolver()
    # for path in image_path.glob('MuMu12-20231124-234421.png'):
    # for path in image_path.glob('MuMu12-20231118-000020.png'):
    # for path in image_path.glob('*.png'):
    filtered_paths = filter_path(image_path)
    output_dict: defaultdict[str, dict[datetime.date, CreditStore]] = defaultdict(dict)
    for person, d in filtered_paths.items():
        for date, path in d.items():
            logger.info(path.name)
            result: CreditStore = shop_solver.recognize(loadimg(path.as_posix()))
            logger.info(result)
            output_dict[person][date] = result
            draw(Image.open(path), result).save(output_image_path / path.name)

    for person, d in output_dict.items():
        with open(output_csv_path / f'{person}.csv', 'a', encoding='utf-8', newline='') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for date, result in d.items():
                credit, items = result
                for i, item in enumerate(items):
                    name, discount, sold = item
                    spamwriter.writerow([date.strftime('%Y-%m-%d'), str(i), name, f'{-discount}%', str(sold), str(credit)])


if __name__ == '__main__':
    # main()
    # print(*(filter_path(image_path).items()), sep='\n')
    ...

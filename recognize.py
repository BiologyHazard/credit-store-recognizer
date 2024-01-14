from __future__ import annotations

import json
import threading
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageFont

from credit_store_recognizer.solvers.shop import CreditStore, ShopSolver
from credit_store_recognizer.utils.image import loadimg
from credit_store_recognizer.utils.log import logger, set_level


def draw(image: Image.Image, result: CreditStore) -> Image.Image:
    credit_pos = (1600, 30)
    item_poses = [
        ((25, 222), (399, 576)),
        ((405, 222), (773, 576)),
        ((784, 222), (1147, 576)),
        ((1164, 222), (1521, 576)),
        ((1544, 222), (1895, 576)),
        ((25, 603), (399, 957)),
        ((405, 603), (773, 957)),
        ((784, 603), (1147, 957)),
        ((1164, 603), (1521, 957)),
        ((1544, 603), (1895, 957)),
    ]
    font = ImageFont.truetype(
        r'C:\Users\Administrator\AppData\Local\Microsoft\Windows\Fonts\SourceHanSansSC-Regular.otf', 48)
    draw = ImageDraw.Draw(image)
    draw.text(credit_pos, str(result.credit), 'black', font, stroke_width=5, stroke_fill='white')
    for (name, discount, sold), ((x0, y0), (x1, y1)) in zip(result.items, item_poses):
        draw.multiline_text((x0, y0 + 100),
                            f'{name}\n{discount}\n{sold}',
                            'black', font, stroke_width=5, stroke_fill='white')
    return image


@logger.catch
def recognize_single(screenshot_path: Path,
                     screenshots_folder: Path,
                     output_json_folder: Path | None,
                     output_images_folder: Path | None,
                     shop_solver: ShopSolver,
                     result: dict[Path, CreditStore]) -> CreditStore:

    logger.info(screenshot_path.relative_to(screenshots_folder).as_posix())
    img = loadimg(screenshot_path.as_posix())
    img = cv2.resize(img, (1920, 1080))
    recognize_result: CreditStore = shop_solver.recognize(img)
    logger.info(recognize_result)
    result[screenshot_path] = recognize_result

    if output_json_folder is not None:
        output_json_path = output_json_folder / screenshot_path.relative_to(screenshots_folder).with_suffix('.json')
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(json.dumps(recognize_result.json(), ensure_ascii=False, indent=4), 'utf-8')

    if output_images_folder is not None:
        output_image_path = output_images_folder / screenshot_path.relative_to(screenshots_folder)
        output_image_path.parent.mkdir(parents=True, exist_ok=True)
        draw(Image.open(screenshot_path).resize((1920, 1080)), recognize_result).save(output_image_path)

    return recognize_result


@logger.catch
def recognize_all(screenshots_folder: Path,
                  output_json_folder: Path | None,
                  output_images_folder: Path | None,
                  skip_recognized: bool = True) -> dict[Path, CreditStore]:
    shop_solver = ShopSolver()

    result: dict[Path, CreditStore] = {}
    threads: list[threading.Thread] = []
    for path in screenshots_folder.rglob('*.png'):
        if (skip_recognized
                and output_json_folder is not None
                and (output_json_folder / path.relative_to(screenshots_folder).with_suffix('.json')).is_file()):
            continue
        thread = threading.Thread(
            target=recognize_single,
            args=(path, screenshots_folder, output_json_folder, output_images_folder, shop_solver, result),
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    logger.info(f'Finished {len(threads)} threads.')
    return result


if __name__ == '__main__':
    set_level('INFO')
    screenshots_folder = Path(r'D:\BioHazard\Documents\Arknights\信用商店统计\信用商店截图')
    output_json_folder = Path(r'D:\BioHazard\Documents\Arknights\信用商店统计\信用商店截图识别结果')
    output_images_folder = Path(r'D:\BioHazard\Documents\Arknights\信用商店统计\信用商店截图标记')

    result: dict[Path, CreditStore] = recognize_all(screenshots_folder,
                                                    output_json_folder=output_json_folder,
                                                    output_images_folder=output_images_folder)
    print(result)

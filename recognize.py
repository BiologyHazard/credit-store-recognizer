import json
import threading
from pathlib import Path

import cv2
from PIL import Image

from credit_store_recognizer.credit_store import CreditStore
from credit_store_recognizer.image import load_image
from credit_store_recognizer.log import logger, set_level
from credit_store_recognizer.recognizer import credit_store_recognizer, draw_result


@logger.catch
def recognize_single(screenshot_path: Path,
                     screenshots_folder: Path,
                     output_json_folder: Path | None,
                     output_images_folder: Path | None,
                     result: dict[Path, CreditStore]) -> CreditStore:

    logger.info(screenshot_path.relative_to(screenshots_folder).as_posix())
    img = load_image(screenshot_path.as_posix())
    img = cv2.resize(img, (1920, 1080))
    recognize_result: CreditStore = credit_store_recognizer.recognize(img)
    logger.info(recognize_result)
    result[screenshot_path] = recognize_result

    if output_json_folder is not None:
        output_json_path = output_json_folder / screenshot_path.relative_to(screenshots_folder).with_suffix('.json')
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(json.dumps(recognize_result.model_dump_json(), ensure_ascii=False, indent=4), 'utf-8')

    if output_images_folder is not None:
        output_image_path = output_images_folder / screenshot_path.relative_to(screenshots_folder)
        output_image_path.parent.mkdir(parents=True, exist_ok=True)
        draw_result(Image.open(screenshot_path).resize((1920, 1080)), recognize_result).resize((1280, 720)).save(output_image_path)

    return recognize_result


@logger.catch
def recognize_all(screenshots_folder: Path,
                  output_json_folder: Path | None,
                  output_images_folder: Path | None,
                  skip_recognized: bool = True) -> dict[Path, CreditStore]:
    result: dict[Path, CreditStore] = {}
    threads: list[threading.Thread] = []
    for path in screenshots_folder.rglob('*.png'):
        if (skip_recognized
                and output_json_folder is not None
                and (output_json_folder / path.relative_to(screenshots_folder).with_suffix('.json')).is_file()):
            continue
        thread = threading.Thread(
            target=recognize_single,
            args=(path, screenshots_folder, output_json_folder, output_images_folder, result),
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
                                                    output_images_folder=output_images_folder,
                                                    skip_recognized=False)
    print(result)

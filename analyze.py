from __future__ import annotations

import csv
import datetime
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from accounts import Account, filter_accounts, get_account_by_nickname
from credit_store_recognizer.credit_store import CreditStore
from credit_store_recognizer.log import logger, set_level
from recognize import recognize_all

shop_items = [
    '龙门币小',
    '龙门币大',
    '家具零件小',
    '家具零件大',
    '招聘许可',
    '加急许可',
    '赤金',
    '基础作战记录',
    '初级作战记录',
    '技巧概要·卷1',
    '技巧概要·卷2',
    '碳',
    '碳素',
    '源岩',
    '代糖',
    '酯原料',
    '异铁碎片',
    '双酮',
    '破损装置',
    '固源岩',
    '糖',
    '聚酸酯',
    '异铁',
    '酮凝集',
    '装置',
    '讯使',
    '嘉维尔',
    '坚雷',
]

T1_materials = [
    "异铁",
    "装置",
    "酮凝集",
    "固源岩",
    "糖",
    "聚酸酯",
]

T0_materials = [
    "代糖",
    "异铁碎片",
    "酯原料",
    "双酮",
    "破损装置",
    "源岩",
]

干员 = [
    "讯使",
    "嘉维尔",
    "坚雷",
]


def path_to_datetime(path: Path) -> datetime.datetime:
    if path.stem.startswith('CS'):
        date_string = path.stem.split('-')[2]
        date_format = "%m%d%H%M"
        datetime_object = datetime.datetime.strptime(date_string, date_format).replace(year=2023)
        return datetime_object

    date_string = path.stem[7:22]
    date_format = "%Y%m%d-%H%M%S"
    datetime_object = datetime.datetime.strptime(date_string, date_format)
    return datetime_object


def datetime_to_yj_date(t: datetime.datetime) -> datetime.date:
    return (t - datetime.timedelta(hours=4)).date()


def path_to_yj_date(path: Path) -> datetime.date:
    return datetime_to_yj_date(path_to_datetime(path))


def path_to_person(path: Path) -> str:
    if path.stem.startswith('CS-'):
        return path.stem.split('-')[1]
    return path.parts[-2]


def json_to_csv(recognize_result_folder: Path, output_csv_folder: Path, 忽略含有干员的商店: bool = True):
    output_csv_folder.mkdir(parents=True, exist_ok=True)
    person_paths = defaultdict(list)
    for path in recognize_result_folder.rglob('*.json'):
        person = path_to_person(path)
        if person in ('aa', 'ab', 'ac', 'ad', 'ae', 'af', 'ag', 'ah', 'ai'):
            continue
        person_paths[person].append(path)

    for person, json_paths in person_paths.items():
        # json_paths = list(path.glob('*.json'))
        json_paths.sort(key=path_to_datetime)
        date_to_path: dict[datetime.date, Path] = {}
        for json_path in json_paths:
            date_to_path[path_to_yj_date(json_path)] = json_path

        values = [path.stem for path in date_to_path.values()]
        if sorted(values) != sorted(set(values)):
            logger.error('Duplicate date')

        with open(output_csv_folder / f'{person}.csv', 'w', encoding='utf-8', newline='') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter='\t', quotechar='|')
            csv_writer.writerow(['日期', '序号', '名称', '折扣', '是否购买', '剩余信用'])
            for date, json_path in date_to_path.items():
                with open(json_path, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                if 忽略含有干员的商店 and any(item['name'] in 干员 for item in data['items']):
                    continue
                for i, item in enumerate(data['items']):
                    csv_writer.writerow([
                        date.strftime('%Y-%m-%d'),
                        i,
                        item['name'],
                        item['discount'],
                        item['sold'],
                        data['credit'],
                    ])


def analyze(csv_folder: Path, output_result_csv_path: Path, output_data_csv_path: Path):
    data_rows: list[dict[str, Any]] = []
    result_rows: list[dict[str, Any]] = []
    for path in csv_folder.glob('*.csv'):
        nickname: str = path.stem
        account: Account = get_account_by_nickname(nickname)
        item_counter: dict[str, int] = {k: 0 for k in shop_items}
        discount_counter: dict[int, int] = {0: 0, 50: 0, 75: 0, 95: 0, 99: 0}
        count = 0
        with open(path, 'r', encoding='utf-8', newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile, delimiter='\t', quotechar='|')
            for row in csv_reader:
                data_rows.append({'账号序号': account.index, **row})
                count += 1
                item_counter[row['名称']] += 1
                discount_counter[int(row['折扣'])] += 1

        assert count % 10 == 0
        天数 = count // 10
        if 天数 == 0:
            result_rows.append({'序号': account.index, '天数': '0'})
            continue
        总共白材料 = sum(item_counter[k] for k in T0_materials)
        总共绿材料 = sum(item_counter[k] for k in T1_materials)
        总共材料 = 总共白材料 + 总共绿材料
        平均每天白材料 = 总共白材料 / 天数
        平均每天绿材料 = 总共绿材料 / 天数
        平均每天材料 = 平均每天白材料 + 平均每天绿材料
        绿材料占材料 = 平均每天绿材料 / (平均每天白材料 + 平均每天绿材料)
        总共龙门币 = item_counter["龙门币小"] + item_counter["龙门币大"]
        平均每天龙门币 = 总共龙门币 / 天数
        大龙门币占龙门币 = item_counter["龙门币大"] / 总共龙门币 if 总共龙门币 != 0 else 0
        总共家具零件 = item_counter["家具零件小"] + item_counter["家具零件大"]
        平均每天家具零件 = 总共家具零件 / 天数
        大家具零件占家具零件 = item_counter["家具零件大"] / 总共家具零件 if 总共家具零件 != 0 else 0
        总共作战记录 = item_counter["基础作战记录"] + item_counter["初级作战记录"]
        平均每天作战记录 = 总共作战记录 / 天数
        初级作战记录占作战记录 = item_counter["初级作战记录"] / 总共作战记录 if 总共作战记录 != 0 else 0
        总共技巧概要 = item_counter["技巧概要·卷1"] + item_counter["技巧概要·卷2"]
        平均每天技巧概要 = 总共技巧概要 / 天数
        技巧概要卷_2占技巧概要 = item_counter["技巧概要·卷2"] / 总共技巧概要 if 总共技巧概要 != 0 else 0
        总共碳类 = item_counter["碳"] + item_counter["碳素"]
        平均每天碳类 = 总共碳类 / 天数
        碳素占碳类 = item_counter["碳素"] / 总共碳类 if 总共碳类 != 0 else 0
        高阶物品占分等阶物品 = (
            总共绿材料
            + item_counter['龙门币大']
            + item_counter['家具零件大']
            + item_counter['初级作战记录']
            + item_counter["技巧概要·卷2"]
            + item_counter["碳素"]
        ) / (
            总共材料
            + 总共龙门币
            + 总共家具零件
            + 总共作战记录
            + 总共技巧概要
            + 总共碳类
        )

        result_rows.append({
            '序号': account.index,
            '天数': 天数,
            '高阶物品占分等阶物品': f'{高阶物品占分等阶物品:.4%}',
            '平均每天白材料': f'{平均每天白材料:.6f}',
            '平均每天绿材料': f'{平均每天绿材料:.6f}',
            '平均每天材料': f'{平均每天材料:.6f}',
            '绿材料占材料': f'{绿材料占材料:.4%}',
            '平均每天龙门币': f'{平均每天龙门币:.6f}',
            '大龙门币占龙门币': f'{大龙门币占龙门币:.4%}',
            '平均每天家具零件': f'{平均每天家具零件:.6f}',
            '大家具零件占家具零件': f'{大家具零件占家具零件:.4%}',
            '平均每天作战记录': f'{平均每天作战记录:.6f}',
            '初级作战记录占作战记录': f'{初级作战记录占作战记录:.4%}',
            '平均每天技巧概要': f'{平均每天技巧概要:.6f}',
            '技巧概要卷·2占技巧概要': f'{技巧概要卷_2占技巧概要:.4%}',
            '平均每天碳类': f'{平均每天碳类:.6f}',
            '碳素占碳类': f'{碳素占碳类:.4%}',
            **{f'平均每天-{k}%数量': f'{v / 天数:.6f}' for k, v in discount_counter.items()},
            **{f'平均每天{k}': f'{v / 天数:.6f}' for k, v in item_counter.items()},
            **{f'{k}数量': v for k, v in item_counter.items()},
        })
    # result_rows.sort(key=lambda row: int(row['序号']))
    result_dict: dict[int, dict] = {row['序号']: row for row in result_rows}

    with open(output_result_csv_path, 'w', encoding='utf-8', newline='') as csvfile:
        csv_writer = csv.DictWriter(
            csvfile,
            # [
            #     '序号', '天数',
            #     '平均每天白材料', '平均每天绿材料', '绿材料占材料',
            #     '大龙门币占龙门币',
            #     '大家具零件占家具零件',
            #     *(f'平均每天{k}' for k in shop_items),
            #     *(f'{k}数量' for k in shop_items),
            # ],
            result_rows[0].keys(),
            delimiter='\t',
            quotechar='|',
        )
        csv_writer.writeheader()
        for account in filter_accounts(参与信用商店测试=True):
            index: int = account.index
            row: dict[str, str] = result_dict.get(index, {})
            csv_writer.writerow(row)

    data_rows.sort(key=lambda row: row['账号序号'])
    with open(output_data_csv_path, 'w', encoding='utf-8', newline='') as csvfile:
        csv_writer = csv.DictWriter(
            csvfile,
            data_rows[0].keys(),
            delimiter='\t',
            quotechar='|',
        )
        csv_writer.writeheader()
        for row in data_rows:
            csv_writer.writerow(row)


if __name__ == '__main__':
    set_level('INFO')
    root_folder = Path(r'D:\BioHazard\Documents\Arknights\信用商店统计')
    screenshots_folder = root_folder / '信用商店截图'
    output_json_folder = root_folder / '信用商店截图识别结果'
    output_images_folder = root_folder / '信用商店截图标记'
    output_csv_folder = root_folder / '信用商店按账号统计'

    result: dict[Path, CreditStore] = recognize_all(screenshots_folder,
                                                    output_json_folder=output_json_folder,
                                                    output_images_folder=output_images_folder)

    json_to_csv(output_json_folder, output_csv_folder)
    analyze(output_csv_folder, root_folder / '统计.csv', root_folder / '原始数据.csv')

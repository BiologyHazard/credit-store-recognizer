from __future__ import annotations

import csv
import datetime
import json
from pathlib import Path
from accounts import get_account_by_nickname

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
    date_string = path.stem[7:22]

    date_format = "%Y%m%d-%H%M%S"
    datetime_object = datetime.datetime.strptime(date_string, date_format)
    return datetime_object


def datetime_to_yj_date(t: datetime.datetime) -> datetime.date:
    return (t - datetime.timedelta(hours=4)).date()


def path_to_yj_date(path: Path) -> datetime.date:
    return datetime_to_yj_date(path_to_datetime(path))


def json_to_csv(recognize_result_folder: Path, output_csv_folder: Path, 忽略含有干员的商店: bool = True):
    output_csv_folder.mkdir(parents=True, exist_ok=True)
    for path in recognize_result_folder.iterdir():
        if not path.is_dir():
            continue
        person = path.name
        json_paths = list(path.glob('*.json'))
        json_paths.sort(key=path_to_datetime)
        date_to_path: dict[datetime.date, Path] = {}
        for json_path in json_paths:
            date_to_path[path_to_yj_date(json_path)] = json_path

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
                        f"{-item['discount']}%",
                        item['sold'],
                        data['credit'],
                    ])


def analyze(csv_folder: Path, output_csv_path: Path):
    rows = []
    for path in csv_folder.glob('*.csv'):
        nickname = path.stem.split('-', 1)[1]
        item_counter = {k: 0 for k in shop_items}
        count = 0
        with open(path, 'r', encoding='utf-8', newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile, delimiter='\t', quotechar='|')
            for row in csv_reader:
                count += 1
                item_counter[row['名称']] += 1

        assert count % 10 == 0
        天数 = count // 10
        if 天数 == 0:
            rows.append({'序号': get_account_by_nickname(nickname)['序号'], '天数': '0'})
            continue
        平均每天白材料 = sum(item_counter[k] for k in T0_materials) / 天数
        平均每天绿材料 = sum(item_counter[k] for k in T1_materials) / 天数
        平均每天材料 = 平均每天白材料 + 平均每天绿材料
        绿材料占材料 = 平均每天绿材料 / (平均每天白材料 + 平均每天绿材料)
        平均每天龙门币 = (item_counter["龙门币小"] + item_counter["龙门币大"]) / 天数
        大龙门币占龙门币 = item_counter["龙门币大"] / (item_counter["龙门币小"] + item_counter["龙门币大"] + 1e-10)
        平均每天家具零件 = (item_counter["家具零件小"] + item_counter["家具零件大"]) / 天数
        大家具零件占家具零件 = item_counter["家具零件大"] / (item_counter["家具零件小"] + item_counter["家具零件大"] + 1e-10)
        平均每天作战记录 = (item_counter["基础作战记录"] + item_counter["初级作战记录"]) / 天数
        初级作战记录占作战记录 = item_counter["初级作战记录"] / (item_counter["基础作战记录"] + item_counter["初级作战记录"] + 1e-10)
        平均每天技巧概要 = (item_counter["技巧概要·卷1"] + item_counter["技巧概要·卷2"]) / 天数
        技巧概要卷_2占技巧概要 = item_counter["技巧概要·卷2"] / (item_counter["技巧概要·卷1"] + item_counter["技巧概要·卷2"] + 1e-10)
        rows.append({
            '序号': get_account_by_nickname(nickname)['序号'],
            '天数': 天数,
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
            **{f'平均每天{k}': f'{v / 天数:.6f}' for k, v in item_counter.items()},
            **{f'{k}数量': v for k, v in item_counter.items()},
        })
    rows.sort(key=lambda row: int(row['序号']))

    with open(output_csv_path, 'w', encoding='utf-8', newline='') as csvfile:
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
            rows[0].keys(),
            delimiter='\t',
            quotechar='|',
        )
        csv_writer.writeheader()
        for row in rows:
            csv_writer.writerow(row)


if __name__ == '__main__':
    recognize_result_folder = Path(r'D:\BioHazard\Documents\Arknights\信用商店统计\信用商店截图识别结果')
    output_csv_folder = Path(r'D:\BioHazard\Documents\Arknights\信用商店统计\信用商店按账号统计')
    json_to_csv(recognize_result_folder, output_csv_folder)
    analyze(output_csv_folder, output_csv_folder.parent / '统计.csv')

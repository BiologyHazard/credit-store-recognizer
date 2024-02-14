import csv
from collections import defaultdict
from datetime import date, datetime, timedelta
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

from accounts import Account, filter_accounts, get_account_by_index, get_account_by_nickname
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
    '异铁',
    '装置',
    '酮凝集',
    '固源岩',
    '糖',
    '聚酸酯',
]

T0_materials = [
    '代糖',
    '异铁碎片',
    '酯原料',
    '双酮',
    '破损装置',
    '源岩',
]

operators = [
    '讯使',
    '嘉维尔',
    '坚雷',
]


def path_to_datetime(path: Path) -> datetime:
    if path.stem.startswith('CS'):
        date_string = path.stem.split('-')[2]
        date_format = "%m%d%H%M"
        datetime_object = datetime.strptime(date_string, date_format).replace(year=2023)
        return datetime_object

    if path.stem.startswith('CreditStore'):
        date_string = path.stem[12:27]
        date_format = "%Y%m%d-%H%M%S"
        datetime_object = datetime.strptime(date_string, date_format)
        return datetime_object

    date_string = path.stem[7:22]
    date_format = "%Y%m%d-%H%M%S"
    datetime_object = datetime.strptime(date_string, date_format)
    return datetime_object


def datetime_to_yj_date(t: datetime) -> date:
    return (t - timedelta(hours=4)).date()


def path_to_yj_date(path: Path) -> date:
    return datetime_to_yj_date(path_to_datetime(path))


# @lru_cache
def path_to_person(path: Path) -> str:
    if path.stem.startswith('CS'):
        return path.stem.split('-')[1]
    if path.stem.startswith('CreditStore'):
        return path.stem.split('-', maxsplit=4)[-1]
    return path.parts[-2]


def check(recognize_result_folder: Path):
    paths = recognize_result_folder.rglob('*.json')
    credit_stores: list[tuple[str, datetime, date, tuple[str, ...]]] = []
    for path in sorted(paths, key=path_to_datetime):
        person1 = path_to_person(path)
        datetime1 = path_to_datetime(path)
        date1 = path_to_yj_date(path)
        if path_to_person(path) in ('aa', 'ab', 'ac', 'ad', 'ae', 'af', 'ag', 'ah', 'ai'):
            continue
        credit_store: CreditStore = CreditStore.model_validate_json(path.read_text('utf-8'))
        item_names1 = tuple(item.name for item in credit_store.items)
        credit_stores.append((person1, datetime1, date1, item_names1))

    # for i in range(len(credit_stores)):
    #     path0, store0 = credit_stores[i]
    #     for j in range(i + 1, len(credit_stores)):
    #         path1, store1 = credit_stores[j]
    #         if CreditStore.is_same_store(store0, store1):
    #             datetime0 = path_to_datetime(path0)
    #             date0 = path_to_yj_date(path0)
    #             person0 = path_to_person(path0)
    #             datetime1 = path_to_datetime(path1)
    #             date1 = path_to_yj_date(path1)
    #             person1 = path_to_person(path1)
    #             if date0 == date1 and person0 == person1:
    #                 continue
    #             logger.warning(f'{datetime0}, {person0} and {datetime1}, {person1} are the same store')

    seen: dict[tuple[str, ...], tuple[str, datetime, date]] = {}
    for person1, datetime1, date1, item_names1 in credit_stores:
        if item_names1 in seen:
            person0, datetime0, date0 = seen[item_names1]
            if date0 == date1 and person0 == person1:
                continue
            logger.warning(f'({person0}, {datetime0}) is the same store as ({person1}, {datetime1})')
        else:
            seen[item_names1] = person1, datetime1, date1


def json_to_csv(recognize_result_folder: Path,
                output_csv_folder: Path,
                output_csv_path: Path,
                忽略含有干员的商店: bool = True) -> None:
    person_paths = defaultdict(list)
    person_rows: defaultdict[int, list[dict[str, Any]]] = defaultdict(list)

    for path in recognize_result_folder.rglob('*.json'):
        person: str = path_to_person(path)
        if person in ('aa', 'ab', 'ac', 'ad', 'ae', 'af', 'ag', 'ah', 'ai'):
            continue
        account: Account = get_account_by_nickname(person)
        person_paths[account.index].append(path)

    for person_index, json_paths in person_paths.items():
        json_paths.sort(key=path_to_datetime)
        date_to_path: dict[date, Path] = {}
        for json_path in json_paths:
            date_to_path[path_to_yj_date(json_path)] = json_path

        for date_, json_path in date_to_path.items():
            credit_store: CreditStore = CreditStore.model_validate_json(json_path.read_text('utf-8'))
            if 忽略含有干员的商店 and any(item.name in operators for item in credit_store.items):
                continue
            for i, item in enumerate(credit_store.items):
                person_rows[person_index].append({
                    '日期': date_.strftime('%Y-%m-%d'),
                    '序号': i,
                    '名称': item.name,
                    '折扣': item.discount,
                    '是否购买': item.sold,
                    '剩余信用': credit_store.credit,
                })

        with open(output_csv_folder / f'{person_index}.csv', 'w', encoding='utf-8', newline='') as csvfile:
            csv_writer = csv.DictWriter(
                csvfile,
                ['日期', '序号', '名称', '折扣', '是否购买', '剩余信用'],
                delimiter='\t',
            )
            csv_writer.writeheader()
            for row in person_rows[person_index]:
                csv_writer.writerow(row)

    with open(output_csv_path, 'w', encoding='utf-8', newline='') as csvfile:
        csv_writer = csv.DictWriter(
            csvfile,
            fieldnames=['账号序号', '日期', '序号', '名称', '折扣', '是否购买', '剩余信用'],
            delimiter='\t',
        )
        csv_writer.writeheader()
        for person_index, rows in sorted(person_rows.items(), key=lambda x: x[0]):
            for row in rows:
                csv_writer.writerow({'账号序号': person_index, **row})


def analyze(path: Path, output_result_csv_path: Path):
    result_rows: list[dict[str, Any]] = []
    for path in path.glob('*.csv'):
        index: int = int(path.stem)
        account: Account = get_account_by_index(index)
        item_counter: dict[str, int] = {k: 0 for k in shop_items}
        discount_counter: dict[int, int] = {0: 0, 50: 0, 75: 0, 95: 0, 99: 0}
        count = 0
        with open(path, 'r', encoding='utf-8', newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile, delimiter='\t')
            for row in csv_reader:
                count += 1
                item_counter[row['名称']] += 1
                discount_counter[int(row['折扣'])] += 1

        assert count % 10 == 0
        天数: int = count // 10
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
        总共龙门币 = item_counter['龙门币小'] + item_counter['龙门币大']
        平均每天龙门币 = 总共龙门币 / 天数
        大龙门币占龙门币 = item_counter['龙门币大'] / 总共龙门币 if 总共龙门币 != 0 else 0
        总共家具零件 = item_counter['家具零件小'] + item_counter['家具零件大']
        平均每天家具零件 = 总共家具零件 / 天数
        大家具零件占家具零件 = item_counter['家具零件大'] / 总共家具零件 if 总共家具零件 != 0 else 0
        总共作战记录 = item_counter['基础作战记录'] + item_counter['初级作战记录']
        平均每天作战记录 = 总共作战记录 / 天数
        初级作战记录占作战记录 = item_counter['初级作战记录'] / 总共作战记录 if 总共作战记录 != 0 else 0
        总共技巧概要 = item_counter['技巧概要·卷1'] + item_counter['技巧概要·卷2']
        平均每天技巧概要 = 总共技巧概要 / 天数
        技巧概要卷_2占技巧概要 = item_counter['技巧概要·卷2'] / 总共技巧概要 if 总共技巧概要 != 0 else 0
        总共碳类 = item_counter['碳'] + item_counter['碳素']
        平均每天碳类 = 总共碳类 / 天数
        碳素占碳类 = item_counter['碳素'] / 总共碳类 if 总共碳类 != 0 else 0
        高阶物品占分等阶物品 = (
            总共绿材料
            + item_counter['龙门币大']
            + item_counter['家具零件大']
            + item_counter['初级作战记录']
            + item_counter['技巧概要·卷2']
            + item_counter['碳素']
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
            '技巧概要·卷2占技巧概要': f'{技巧概要卷_2占技巧概要:.4%}',
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
        )
        csv_writer.writeheader()
        for account in filter_accounts(参与信用商店测试=True):
            index = account.index
            row: dict[str, str] = result_dict.get(index, {})
            csv_writer.writerow(row)


if __name__ == '__main__':
    set_level('INFO')
    credit_store_folder = Path(r'D:\BioHazard\Documents\Arknights\信用商店统计')

    result: dict[Path, CreditStore] = recognize_all(
        screenshots_folder=credit_store_folder / '信用商店截图',
        output_json_folder=credit_store_folder / '信用商店截图识别结果',
        output_images_folder=credit_store_folder / '信用商店截图标记',
    )

    check(credit_store_folder / '信用商店截图识别结果')

    json_to_csv(
        recognize_result_folder=credit_store_folder / '信用商店截图识别结果',
        output_csv_folder=credit_store_folder / '信用商店按账号统计',
        output_csv_path=credit_store_folder / '原始数据.csv',
        忽略含有干员的商店=True)

    analyze(credit_store_folder / '信用商店按账号统计', credit_store_folder / '统计.csv')

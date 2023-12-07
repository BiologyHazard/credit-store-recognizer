from pathlib import Path
import csv

output_path = Path('output')

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

for path in output_path.glob('*.csv'):
    with open(path, 'r', encoding='utf-8', newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter='\t', quotechar='|')

        person = path.stem
        T0_count = T1_count = 0
        count = 0
        for row in spamreader:
            count += 1
            date, index, name, discount, sold, credit = row
            if name in T0_materials:
                T0_count += 1
            elif name in T1_materials:
                T1_count += 1
        assert count % 10 == 0
        days = count // 10
        print(f'{person:15}    天数: {days:3}    平均每天白材料: {T0_count / days:6.4}    绿: {T1_count / days:6.4}    绿占比: {T1_count / (T0_count + T1_count):.2%}')

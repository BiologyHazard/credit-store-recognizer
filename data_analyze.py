import csv
from pathlib import Path
from collections import defaultdict, Counter


path = Path(r'D:\BioHazard\Documents\Arknights\信用商店统计\原始数据.csv')
折扣计数器 = defaultdict(lambda: defaultdict(int))
材料折扣计数器 = defaultdict(lambda: defaultdict(int))
折扣组合计数器 = defaultdict(lambda: defaultdict(int))
with open(path, 'r', encoding='utf-8', newline='') as csvfile:
    csv_reader = csv.DictReader(csvfile, delimiter='\t', quotechar='|')
    for row in csv_reader:
        折扣计数器[row['账号序号'], row['日期']][int(row['折扣'])] += 1
        材料折扣计数器[row['名称']][int(row['折扣'])] += 1
discounts = (tuple(v[x] for x in (0, 50, 75, 95, 99)) for v in 折扣计数器.values())
折扣组合计数器 = Counter(discounts)


print('0\t50\t75\t95\t99\tcount')
for k, v in 折扣组合计数器.items():
    print('\t'.join(map(str, k)), v, sep='\t')
# print(*(k for k, v in 折扣计数器.items() if dict(v) == {0: 6, 50: 2, 75: 2, 95: 0, 99: 0}))


# 总共数量 = sum(sum(v.values()) for v in 材料折扣计数器.values())
# print('名称\t0\t50\t75\t95\t99\t比例')
# for 材料名称, 材料折扣次数 in 材料折扣计数器.items():
#     该材料数量 = sum(材料折扣次数.values())
#     该材料占比 = 该材料数量 / 总共数量
#     print(材料名称, *(材料折扣次数[x] / 该材料数量 for x in (0, 50, 75, 95, 99)), 该材料占比, sep='\t')

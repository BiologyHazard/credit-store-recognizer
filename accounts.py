from __future__ import annotations

import csv
from pathlib import Path

accounts_path = Path(r"D:\BioHazard\Documents\Arknights\信用商店统计\accounts.csv")
with open(accounts_path, 'r', encoding='utf-8', newline='') as fp:
    csv_reader = csv.DictReader(fp, delimiter='\t')
    rows = list(csv_reader)


def get_account_by_nickname(nickname: str) -> dict[str, str]:
    for row in rows:
        if row.get('昵称') == nickname:
            return row
        if '-' in nickname and row.get('区服') == nickname.split('-', 1)[0] and row.get('昵称') == nickname.split('-', 1)[1]:
            return row
        if row.get('化名') == nickname:
            return row
    raise ValueError(f'No account named {nickname}')

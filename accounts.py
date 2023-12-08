from __future__ import annotations

import csv
from pathlib import Path

accounts_path = Path('accounts.csv')
with open(accounts_path, 'r', encoding='utf-8', newline='') as fp:
    csv_reader = csv.DictReader(fp, delimiter=',')
    rows = list(csv_reader)


def get_account_by_nickname(nickname: str) -> dict[str, str]:
    for row in rows:
        if row['昵称'] == nickname:
            return row
    raise ValueError(f'No account named {nickname}')

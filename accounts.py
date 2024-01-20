from __future__ import annotations

import csv
from pathlib import Path
from functools import lru_cache

# from dataclasses import dataclass, Field

# class Account():
#     index: str
#     owner: str
#     bilibili_nickname: str
#     server: str
#     username: str
#     password: str
#     id: str
#     nickname: str
#     is_credit_store_participator: bool
#     is_tailoring_participator: bool

#     @classmethod
#     def from_row(cls, row: dict[str, str]) -> Account:
#         return cls(
#             row['序号'],
#             row['号主'],
#             row['bilibili 昵称'],
#             row['区服'],
#             row['账号'],
#             row['密码'],
#             row['ID'],
#             row['昵称'],
#             row['参与信用商店测试'],
#             row['参与裁缝测试'],
#         )

accounts_path = Path(r"D:\BioHazard\Documents\Arknights\信用商店统计\accounts.csv")
with open(accounts_path, 'r', encoding='utf-8', newline='') as fp:
    csv_reader = csv.DictReader(fp, delimiter='\t')
    # accounts = [Account(**row) for row in csv_reader]
    rows = list(csv_reader)


@lru_cache
def get_account_by_nickname(nickname: str) -> dict[str, str]:
    for row in rows:
        if row.get('昵称') == nickname:
            return row
        if '-' in nickname and row.get('区服') == nickname.split('-', 1)[0] and row.get('昵称') == nickname.split('-', 1)[1]:
            return row
    for row in rows:
        if row.get('号主') == nickname:
            return row
    raise ValueError(f'No account named {nickname}')


@lru_cache
def filter_accounts(参与信用商店测试: bool | None = None, 参与裁缝测试: bool | None = None) -> list[dict[str, str]]:
    return [
        row for row in rows
        if (参与信用商店测试 is None or row.get('参与信用商店测试') == 参与信用商店测试)
        and (参与裁缝测试 is None and row.get('参与裁缝测试') == 参与信用商店测试)
    ]

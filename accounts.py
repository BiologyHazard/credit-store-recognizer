from __future__ import annotations

import csv
from pathlib import Path
from functools import lru_cache
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, Union


class Account(BaseModel):
    index: int = Field(alias='序号')
    owner: Optional[str] = Field(alias='号主')
    bilibili_nickname: Optional[str] = Field(alias='bilibili 昵称')
    server: Optional[Literal['官服', 'b服']] = Field(alias='区服')
    account: Optional[str] = Field(alias='账号')
    password: Optional[str] = Field(alias='密码')
    id: Optional[str] = Field(alias='ID')
    nickname: Optional[str] = Field(alias='昵称')
    # 参与信用商店测试: Optional[bool] = Field(alias='参与信用商店测试')
    # 参与裁缝测试: Optional[bool] = Field(alias='参与裁缝测试')

    @field_validator(
        'owner', 'bilibili_nickname', 'server', 'account', 'password', 'id', 'nickname',
        mode='before',
    )
    def empty_str_to_None(cls, v):
        return None if v == '' else v


accounts_path = Path(r"D:\BioHazard\Documents\Arknights\信用商店统计\accounts.csv")
with open(accounts_path, 'r', encoding='utf-8', newline='') as fp:
    csv_reader = csv.DictReader(fp, delimiter='\t', restval=None)
    accounts = [Account.model_validate(row) for row in csv_reader if row['序号'] != '']
    # rows = list(csv_reader)


@lru_cache
def get_account_by_nickname(nickname: str) -> Account:
    for account in accounts:
        if account.nickname == nickname:
            return account
        if '-' in nickname and nickname.split('-', 1) == [account.server, account.nickname]:
            return account
    for account in accounts:
        if account.owner == nickname:
            return account
    raise ValueError(f'No account named {nickname}')


# @lru_cache
# def filter_accounts(参与信用商店测试: bool | None = None, 参与裁缝测试: bool | None = None) -> list[Account]:
#     return [
#         account for account in accounts
#         if (参与信用商店测试 is None or account.参与信用商店测试 == 参与信用商店测试)
#         and (参与裁缝测试 is None or account.参与裁缝测试 == 参与信用商店测试)
#     ]

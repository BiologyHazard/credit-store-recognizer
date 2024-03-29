import csv
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Account(BaseModel):
    index: int = Field(alias='序号')
    owner: str | None = Field(alias='号主')
    bilibili_nickname: str | None = Field(alias='bilibili 昵称')
    server: Literal['官服', 'b服'] | None = Field(alias='区服')
    account: str | None = Field(alias='账号')
    password: str | None = Field(alias='密码')
    id: str | None = Field(alias='ID')
    nickname: str | None = Field(alias='昵称')
    参与信用商店测试: bool | None = Field(alias='参与信用商店测试')
    参与裁缝测试: bool | None = Field(alias='参与裁缝测试')

    @field_validator(
        'owner', 'bilibili_nickname', 'server', 'account', 'password',
        'id', 'nickname', '参与信用商店测试', '参与裁缝测试',
        mode='before',
    )
    @classmethod
    def empty_str_to_None(cls, v):
        return None if v == '' else v


accounts_path = Path(r"D:\BioHazard\Documents\Arknights\信用商店统计\accounts.csv")
with open(accounts_path, 'r', encoding='utf-8', newline='') as fp:
    csv_reader = csv.DictReader(fp, delimiter='\t', restval=None)
    accounts: list[Account] = [Account.model_validate(row) for row in csv_reader if row['序号'] != '']


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


@lru_cache
def get_account_by_index(index: int) -> Account:
    for account in accounts:
        if account.index == index:
            return account
    raise ValueError(f'No account with index {index}')


@lru_cache
def filter_accounts(参与信用商店测试: bool | None = None, 参与裁缝测试: bool | None = None) -> list[Account]:
    return [
        account for account in accounts
        if (参与信用商店测试 is None or account.参与信用商店测试 == 参与信用商店测试)
        and (参与裁缝测试 is None or account.参与裁缝测试 == 参与信用商店测试)
    ]

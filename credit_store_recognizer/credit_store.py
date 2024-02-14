from pydantic import BaseModel


class CreditStoreItem(BaseModel):
    name: str
    discount: int
    sold: bool


class CreditStore(BaseModel):
    credit: int
    items: list[CreditStoreItem]

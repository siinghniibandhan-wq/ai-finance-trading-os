# ============================================================
# FINANCIAL OS
# API SCHEMAS
# ============================================================

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


# ============================================================
# USER SCHEMAS
# ============================================================

class UserCreate(BaseModel):
    name: str
    email: str | None = None
    currency: str = "INR"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str | None
    currency: str
    is_active: bool


# ============================================================
# ACCOUNT SCHEMAS
# ============================================================

class AccountCreate(BaseModel):
    user_id: int
    name: str
    account_type: str
    institution: str | None = None
    account_number: str | None = None
    currency: str = "INR"
    balance: Decimal = Decimal("0.00")


class AccountUpdate(BaseModel):
    name: str | None = None
    account_type: str | None = None
    institution: str | None = None
    account_number: str | None = None
    currency: str | None = None
    balance: Decimal | None = None
    is_active: bool | None = None


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    account_type: str
    institution: str | None
    account_number: str | None
    currency: str
    balance: Decimal
    is_active: bool
    
# ============================================================
# CATEGORY SCHEMAS
# ============================================================

class CategoryCreate(BaseModel):
    user_id: int
    name: str
    category_type: str
    description: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = None
    category_type: str | None = None
    description: str | None = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    category_type: str
    description: str | None

# ============================================================
# TRANSACTION SCHEMAS
# ============================================================

class TransactionCreate(BaseModel):
    user_id: int
    account_id: int
    category_id: int | None = None
    transaction_type: str
    amount: Decimal
    description: str | None = None
    transaction_date: date
    reference: str | None = None


class TransactionUpdate(BaseModel):
    account_id: int | None = None
    category_id: int | None = None
    transaction_type: str | None = None
    amount: Decimal | None = None
    description: str | None = None
    transaction_date: date | None = None
    reference: str | None = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    account_id: int
    category_id: int | None
    transaction_type: str
    amount: Decimal
    description: str | None
    transaction_date: date
    reference: str | None

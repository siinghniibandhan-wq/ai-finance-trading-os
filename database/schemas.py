from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


# ============================================================
# COMMON
# ============================================================

class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# ACCOUNT
# ============================================================

class AccountBase(BaseModel):
    name: str
    account_type: str
    institution: str | None = None
    account_number: str | None = None
    currency: str = "INR"
    opening_balance: Decimal = Decimal("0")
    notes: str | None = None


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: str | None = None
    account_type: str | None = None
    institution: str | None = None
    account_number: str | None = None
    currency: str | None = None
    opening_balance: Decimal | None = None
    current_balance: Decimal | None = None
    notes: str | None = None
    is_active: bool | None = None


class AccountResponse(AccountBase, ORMBase):
    id: int
    current_balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ============================================================
# CATEGORY
# ============================================================

class CategoryBase(BaseModel):
    name: str
    category_type: str
    parent_id: int | None = None
    description: str | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = None
    category_type: str | None = None
    parent_id: int | None = None
    description: str | None = None
    is_active: bool | None = None


class CategoryResponse(CategoryBase, ORMBase):
    id: int
    is_active: bool
    created_at: datetime


# ============================================================
# TRANSACTION
# ============================================================

class TransactionBase(BaseModel):
    account_id: int
    category_id: int | None = None
    transaction_type: str
    amount: Decimal
    currency: str = "INR"
    description: str | None = None
    merchant: str | None = None
    reference_number: str | None = None
    transaction_date: datetime
    notes: str | None = None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    account_id: int | None = None
    category_id: int | None = None
    transaction_type: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    description: str | None = None
    merchant: str | None = None
    reference_number: str | None = None
    transaction_date: datetime | None = None
    notes: str | None = None
    is_reconciled: bool | None = None


class TransactionResponse(TransactionBase, ORMBase):
    id: int
    is_reconciled: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


# ============================================================
# ASSET
# ============================================================

class AssetBase(BaseModel):
    name: str
    asset_type: str
    institution: str | None = None
    quantity: Decimal | None = None
    purchase_value: Decimal = Decimal("0")
    current_value: Decimal = Decimal("0")
    currency: str = "INR"
    purchase_date: datetime | None = None
    notes: str | None = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: str | None = None
    asset_type: str | None = None
    institution: str | None = None
    quantity: Decimal | None = None
    purchase_value: Decimal | None = None
    current_value: Decimal | None = None
    currency: str | None = None
    purchase_date: datetime | None = None
    notes: str | None = None
    is_active: bool | None = None


class AssetResponse(AssetBase, ORMBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ============================================================
# LIABILITY
# ============================================================

class LiabilityBase(BaseModel):
    name: str
    liability_type: str
    lender: str | None = None

    # IMPORTANT:
    # These names must match database.models.Liability
    original_amount: Decimal = Decimal("0")
    outstanding_amount: Decimal = Decimal("0")

    interest_rate: Decimal | None = None
    emi_amount: Decimal | None = None

    currency: str = "INR"
    start_date: datetime | None = None
    notes: str | None = None


class LiabilityCreate(LiabilityBase):
    pass


class LiabilityUpdate(BaseModel):
    name: str | None = None
    liability_type: str | None = None
    lender: str | None = None

    # IMPORTANT:
    # These names must match database.models.Liability
    original_amount: Decimal | None = None
    outstanding_amount: Decimal | None = None

    interest_rate: Decimal | None = None
    emi_amount: Decimal | None = None

    currency: str | None = None
    start_date: datetime | None = None
    notes: str | None = None
    is_active: bool | None = None


class LiabilityResponse(LiabilityBase, ORMBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ============================================================
# DASHBOARD / NET WORTH
# ============================================================

class DashboardSummary(BaseModel):
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    total_income: Decimal
    total_expenses: Decimal
    total_investments: Decimal


class NetWorthResponse(BaseModel):
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal

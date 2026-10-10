# ============================================================
# FINANCIAL OS
# API SCHEMAS
# ============================================================

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


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
# BUDGET SCHEMAS
# ============================================================

class BudgetCreate(BaseModel):
    user_id: int
    month: str
    category_id: int
    amount: Decimal


class BudgetUpdate(BaseModel):
    month: str | None = None
    category_id: int | None = None
    amount: Decimal | None = None


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    month: str
    category_id: int
    amount: Decimal

# ============================================================
# TRANSACTION SCHEMAS
# ============================================================


class LoanDisbursementDetails(BaseModel):
    # Gross principal owed to the lender. Transaction amount is net amount received.
    name: str = Field(min_length=1, max_length=150)
    lender_name: str = Field(min_length=1, max_length=150)
    loan_type: str = Field(min_length=1, max_length=60)
    principal_amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    interest_rate: Decimal | None = Field(default=None, ge=0, le=100, max_digits=7, decimal_places=4)
    interest_type: str = "reducing_balance"
    tenure_months: int | None = Field(default=None, gt=0, le=600)
    emi_amount: Decimal | None = Field(default=None, gt=0, max_digits=18, decimal_places=2)
    first_payment_date: date | None = None
    repayment_frequency: str = "monthly"
    processing_fee: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)
    notes: str | None = None


class TransactionCreate(BaseModel):
    user_id: int
    account_id: int
    category_id: int | None = None
    transaction_type: str
    amount: Decimal
    description: str | None = None
    transaction_date: date
    reference: str | None = None
    loan_details: LoanDisbursementDetails | None = None


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

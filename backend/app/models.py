# ============================================================
# FINANCIAL OS
# DATABASE MODELS
# ============================================================

from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


# ============================================================
# USERS
# ============================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="INR",
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    accounts = relationship(
        "Account",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    transactions = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    categories = relationship(
        "Category",
        back_populates="user",
        cascade="all, delete-orphan",
    )


# ============================================================
# ACCOUNTS
# ============================================================

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    account_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    institution: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    account_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="INR",
        nullable=False,
    )

    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=0,
        nullable=False,
    )

    # Credit products use balance as the outstanding amount (positive = owed).
    # These nullable fields keep existing non-credit account records compatible.
    credit_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="accounts",
    )

    transactions = relationship(
        "Transaction",
        back_populates="account",
    )


# ============================================================
# CATEGORIES
# ============================================================

# ============================================================
# CHART OF ACCOUNTS — user-scoped accounting catalogue
# ============================================================
class ChartOfAccount(Base):
    __tablename__ = "chart_of_accounts"
    __table_args__ = (UniqueConstraint("user_id", "code", name="uq_chart_of_accounts_user_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("chart_of_accounts.id", ondelete="RESTRICT"), nullable=True, index=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tax_mapping_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    parent = relationship("ChartOfAccount", remote_side=[id], backref="children")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    category_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="categories",
    )

    transactions = relationship(
        "Transaction",
        back_populates="category",
    )


# ============================================================
# BUDGETS
# ============================================================

class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    month: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        index=True,
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

# ============================================================
# TRANSACTIONS
# ============================================================

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    transaction_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    reference: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    # Receivable/payable tracking fields. Settlements are separate transfer rows.
    party_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    settled_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    settles_transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Transfer rows are paired by this opaque group ID. The transfer target
    # is stored on the source row without creating a dependency on the diary.
    transfer_group_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    transfer_to_account_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="transactions",
    )

    account = relationship(
        "Account",
        back_populates="transactions",
    )

    category = relationship(
        "Category",
        back_populates="transactions",
  )


# ============================================================
# PERSISTENT DOUBLE-ENTRY LEDGER
# One journal header per source transaction; lines must balance.
# Existing transactions remain the source records.
# ============================================================

class JournalEntry(Base):
    __tablename__ = "journal_entries"
    __table_args__ = (UniqueConstraint("user_id", "transaction_id", name="uq_journal_user_transaction"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    lines = relationship("JournalLine", back_populates="entry", cascade="all, delete-orphan")


class JournalLine(Base):
    __tablename__ = "journal_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    journal_entry_id: Mapped[int] = mapped_column(ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    chart_of_account_id: Mapped[int] = mapped_column(ForeignKey("chart_of_accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    financial_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    debit: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    credit: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    entry_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    entry = relationship("JournalEntry", back_populates="lines")


# ============================================================
# FINANCIAL GOALS
# Persistent user-defined planning goals. These records do not
# alter account balances or transactions.
# ============================================================

class FinancialGoal(Base):
    __tablename__ = "financial_goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(60), default="Other", nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    current_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    monthly_contribution: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BrokerTradingControl(Base):
    """Persistent Financial OS live-order kill switch; missing row means OFF."""
    __tablename__ = "broker_trading_control"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


# ============================================================
# LOANS & LIABILITIES
# A loan is the detailed contract; its linked liability is the
# single balance used for consolidated debt/net-worth reporting.
# ============================================================

class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    lender_name: Mapped[str] = mapped_column(String(150), nullable=False)
    loan_type: Mapped[str] = mapped_column(String(60), nullable=False)
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    amount_disbursed: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    outstanding_principal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    deposit_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    linked_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    # Link the loan to the Income transaction that recorded its disbursement.
    disbursement_transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("transactions.id", ondelete="SET NULL"), unique=True, nullable=True, index=True
    )
    interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(7, 4), nullable=True)
    interest_type: Mapped[str] = mapped_column(String(40), default="reducing_balance", nullable=False)
    tenure_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    emi_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    first_payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    repayment_frequency: Mapped[str] = mapped_column(String(30), default="monthly", nullable=False)
    processing_fee: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(150), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    liability = relationship("Liability", back_populates="loan", uselist=False, cascade="all, delete-orphan")


class Liability(Base):
    __tablename__ = "liabilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    liability_type: Mapped[str] = mapped_column(String(60), default="other", nullable=False)
    original_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    outstanding_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    loan_id: Mapped[int | None] = mapped_column(ForeignKey("loans.id", ondelete="CASCADE"), unique=True, nullable=True, index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    loan = relationship("Loan", back_populates="liability")


# ============================================================
# LOAN RECEIVABLES & CASH MOVEMENTS
# Money lent to others is an asset, not an ordinary expense.
# LoanMovement records principal/interest/fees for one cash transaction.
# ============================================================

class LoanReceivable(Base):
    __tablename__ = "loan_receivables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    borrower_name: Mapped[str] = mapped_column(String(150), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    original_principal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    outstanding_principal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    source_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    disbursement_transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id", ondelete="SET NULL"), unique=True, nullable=True, index=True)
    interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(7, 4), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    reference_number: Mapped[str | None] = mapped_column(String(150), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class LoanMovement(Base):
    __tablename__ = "loan_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    loan_id: Mapped[int | None] = mapped_column(ForeignKey("loans.id", ondelete="CASCADE"), nullable=True, index=True)
    receivable_id: Mapped[int | None] = mapped_column(ForeignKey("loan_receivables.id", ondelete="CASCADE"), nullable=True, index=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    movement_type: Mapped[str] = mapped_column(String(30), nullable=False)
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    interest_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


# ============================================================
# AUTHENTICATION CREDENTIALS
# Kept separate from User to avoid changing existing user rows.
# ============================================================

class UserCredential(Base):
    __tablename__ = "user_credentials"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )


# ============================================================
# TAX DEDUCTION CLAIMS (USER-ENTERED, NOT AUTO-VERIFIED)
# ============================================================

class TaxDeductionClaim(Base):
    __tablename__ = "tax_deduction_claims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    financial_year: Mapped[str] = mapped_column(String(9), nullable=False, index=True)
    tax_regime: Mapped[str] = mapped_column(String(10), nullable=False)
    deduction_key: Mapped[str] = mapped_column(String(60), nullable=False)
    claimed_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    evidence_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="pending_review", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# ============================================================
# TAX SALARY INCOME SOURCE (USER-ENTERED, NOT AUTO-VERIFIED)
# One annual record per user and financial year. HRA inputs are retained
# alongside gross salary so an exemption can only be applied against a
# salary source the user has explicitly verified with evidence.
# ============================================================

class TaxSalaryIncomeRecord(Base):
    __tablename__ = "tax_salary_income_records"
    __table_args__ = (UniqueConstraint("user_id", "financial_year", name="uq_tax_salary_user_fy"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    financial_year: Mapped[str] = mapped_column(String(9), nullable=False, index=True)
    gross_salary: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    annual_basic_salary: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    annual_da_forming_retirement_benefits: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    annual_commission_on_turnover_at_fixed_percentage: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    annual_hra_received: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    annual_rent_paid: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    # Explicit user confirmations; legacy rows migrate to False and cannot
    # qualify for HRA until the user re-confirms these facts.
    accommodation_owned_by_taxpayer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rent_actually_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="pending_review", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# ============================================================
# HOUSE PROPERTY INCOME RECORDS
# ============================================================

class TaxHousePropertyRecord(Base):
    __tablename__ = "tax_house_property_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    financial_year: Mapped[str] = mapped_column(String(9), nullable=False, index=True)
    property_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # let_out | self_occupied | none (confirms no house property income)
    property_type: Mapped[str] = mapped_column(String(16), nullable=False)
    annual_rent_received: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    municipal_taxes_paid: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    interest_on_housing_loan: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    evidence_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="pending_review", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# ============================================================
# BUSINESS / PROFESSIONAL INCOME RECORDS
# ============================================================

class TaxBusinessIncomeRecord(Base):
    __tablename__ = "tax_business_income_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    financial_year: Mapped[str] = mapped_column(String(9), nullable=False, index=True)
    record_type: Mapped[str] = mapped_column(String(16), nullable=False)  # receipt or expense
    income_type: Mapped[str] = mapped_column(String(24), nullable=False)  # business, profession, freelance
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    evidence_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Optional explicit link to the Money transaction representing this record.
    # Unlinked tax-only records are not automatically included in final taxable income.
    source_transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending_review")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


# ============================================================
# TAX CREDIT ENTRIES (SELF-REPORTED UNTIL VERIFIED)
# ============================================================

class TaxCreditEntry(Base):
    __tablename__ = "tax_credit_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    financial_year: Mapped[str] = mapped_column(String(9), nullable=False, index=True)
    credit_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(24), default="pending_review", nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )



# ============================================================
# TAX REVIEW CONFIRMATIONS
# The owner's own statement that a section is complete for a year.
# It is not document verification by the application.
# ============================================================

class TaxReviewConfirmation(Base):
    __tablename__ = "tax_review_confirmations"
    __table_args__ = (
        UniqueConstraint("user_id", "financial_year", "section", name="uq_tax_review_confirmation"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    financial_year: Mapped[str] = mapped_column(String(9), nullable=False, index=True)
    section: Mapped[str] = mapped_column(String(40), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


# ============================================================
# FINANCE DIARY — APPEND-ONLY MASTER HISTORY
# No foreign keys to business records: history survives deletion.
# ============================================================

class FinanceDiaryEntry(Base):
    __tablename__ = "finance_diary_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


# ============================================================
# INSTRUMENT MASTER — canonical investment identities
# ============================================================

class InstrumentMaster(Base):
    __tablename__ = "instrument_master"
    __table_args__ = (UniqueConstraint("canonical_key", name="uq_instrument_master_canonical_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    canonical_key: Mapped[str] = mapped_column(String(220), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    symbol: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    exchange: Mapped[str | None] = mapped_column(String(50), nullable=True)
    isin: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    asset_class: Mapped[str] = mapped_column(String(80), nullable=False, default="Other")
    product_type: Mapped[str] = mapped_column(String(80), nullable=False, default="Other")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


# ============================================================
# USER ACCOUNT COMPLETION PROFILE
# One private profile document per authenticated user. Sensitive
# identity verification is NOT inferred from matching text fields.
# ============================================================

class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_profiles_user_id"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    profile_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# ============================================================
# AUTHENTICATION SESSIONS (server-side revocation)
# ============================================================

class AuthSession(Base):
    __tablename__ = "auth_sessions"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


# ============================================================
# PUBLIC WEBSITE CHECKOUT PAYMENTS
# Razorpay orders and verified payment receipts. Subscription
# activation is handled separately from payment verification.
# ============================================================

class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    razorpay_order_id: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True, index=True)
    plan: Mapped[str] = mapped_column(String(40), nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    customer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    customer_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


# ============================================================
# DURABLE BROKER ORDER IDEMPOTENCY
# ============================================================
class BrokerOrderSubmission(Base):
    __tablename__ = "broker_order_submissions"
    __table_args__ = (UniqueConstraint("user_id", "client_id", name="uq_broker_order_user_client_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Nullable for legacy/API callers that do not yet send an explicit investment.
    # Reconciliation must never infer an investment when this is NULL.
    investment_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    symbol: Mapped[str | None] = mapped_column(String(100), nullable=True)
    exchange: Mapped[str | None] = mapped_column(String(10), nullable=True)
    side: Mapped[str | None] = mapped_column(String(10), nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    client_id: Mapped[str] = mapped_column(String(120), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="SUBMITTING")
    gateway_order_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

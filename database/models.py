from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


# ============================================================
# ACCOUNT
# ============================================================

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    institution: Mapped[str | None] = mapped_column(String(150), nullable=True)
    account_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0"), nullable=False
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    transactions = relationship(
        "Transaction",
        back_populates="account",
        cascade="all, delete-orphan",
    )


# ============================================================
# CATEGORY
# ============================================================

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category_type: Mapped[str] = mapped_column(String(30), nullable=False)

    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    parent = relationship(
        "Category",
        remote_side=[id],
        back_populates="children",
    )

    children = relationship(
        "Category",
        back_populates="parent",
    )

    transactions = relationship(
        "Transaction",
        back_populates="category",
    )


# ============================================================
# TRANSACTION
# ============================================================

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=False,
    )

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"),
        nullable=True,
    )

    transaction_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="INR",
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    merchant: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    reference_number: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    transaction_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_reconciled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
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
# ASSET
# ============================================================

class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    asset_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
    )

    institution: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 8),
        nullable=True,
    )

    purchase_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0"),
        nullable=False,
    )

    current_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0"),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="INR",
        nullable=False,
    )

    purchase_date: Mapped[datetime | None] = mapped_column(
        Date

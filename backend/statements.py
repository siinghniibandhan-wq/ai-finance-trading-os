# =====================================================
# AI FINANCE TRADING OS
# STATEMENTS / IMPORT BACKEND
# =====================================================
#
# PURPOSE:
# - Import bank/credit-card CSV statements
# - Store imported statement data safely
# - Keep imported rows separate from Transactions
# - Prepare the system for AI classification/reconciliation
#
# IMPORTANT:
# This module DOES NOT automatically create transactions.
# Transactions will be created only after preview/reconciliation.
# =====================================================


# =====================================================
# IMPORTS
# =====================================================

import csv
import io
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.database import get_db


# =====================================================
# ROUTER
# =====================================================

router = APIRouter(
    prefix="/api/statements",
    tags=["Statements / Import"]
)


# =====================================================
# DATABASE TABLE CREATION
# =====================================================

def ensure_statements_tables(db: Session):
    """
    Create statement import tables if they do not exist.

    We intentionally keep statement imports separate from
    the existing transactions system.
    """

    # -------------------------------------------------
    # STATEMENT IMPORTS
    # -------------------------------------------------

    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS statement_imports (
                id SERIAL PRIMARY KEY,

                file_name VARCHAR(255) NOT NULL,

                file_type VARCHAR(50) NOT NULL,

                account_id INTEGER NULL,

                source VARCHAR(100) NULL,

                status VARCHAR(50) NOT NULL DEFAULT 'imported',

                total_rows INTEGER NOT NULL DEFAULT 0,

                imported_rows INTEGER NOT NULL DEFAULT 0,

                duplicate_rows INTEGER NOT NULL DEFAULT 0,

                error_rows INTEGER NOT NULL DEFAULT 0,

                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )

    # -------------------------------------------------
    # STATEMENT ROWS
    # -------------------------------------------------

    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS statement_rows (
                id SERIAL PRIMARY KEY,

                statement_import_id INTEGER NOT NULL,

                row_number INTEGER NOT NULL,

                transaction_date VARCHAR(50) NULL,

                description TEXT NULL,

                reference VARCHAR(255) NULL,

                debit NUMERIC(14,2) NULL,

                credit NUMERIC(14,2) NULL,

                amount NUMERIC(14,2) NULL,

                balance NUMERIC(14,2) NULL,

                currency VARCHAR(10) DEFAULT 'INR',

                raw_data TEXT NULL,

                classification VARCHAR(50) NULL,

                transaction_id INTEGER NULL,

                is_duplicate BOOLEAN NOT NULL DEFAULT FALSE,

                is_reconciled BOOLEAN NOT NULL DEFAULT FALSE,

                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )

    db.commit()


# =====================================================
# HELPER — DECIMAL CONVERSION
# =====================================================

def parse_decimal(value):
    """
    Convert common Indian/financial number formats
    into Decimal safely.

    Examples:
    1,499.00
    ₹499.00
    -500
    500.25
    """

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    # -------------------------------------------------
    # REMOVE COMMON CURRENCY SYMBOLS / SEPARATORS
    # -------------------------------------------------

    value = (
        value
        .replace(",", "")
        .replace("₹", "")
        .replace("$", "")
        .replace("INR", "")
        .strip()
    )

    # -------------------------------------------------
    # HANDLE BRACKET NEGATIVE FORMAT
    # Example: (500.00)
    # -------------------------------------------------

    if value.startswith("(") and value.endswith(")"):
        value = "-" + value[1:-1]

    try:
        return Decimal(value)

    except (InvalidOperation, ValueError):
        return None


# =====================================================
# HELPER — FIND COLUMN
# =====================================================

def find_column(headers, possible_names):
    """
    Find a matching CSV column using common bank
    statement naming variations.
    """

    normalized = {}

    for header in headers:
        key = str(header).strip().lower()
        normalized[key] = header

    # -------------------------------------------------
    # EXACT MATCH FIRST
    # -------------------------------------------------

    for name in possible_names:

        name_lower = name.lower()

        if name_lower in normalized:
            return normalized[name_lower]

    # -------------------------------------------------
    # PARTIAL MATCH
    # -------------------------------------------------

    for header in headers:

        header_lower = str(header).strip().lower()

        for name in possible_names:

            if name.lower() in header_lower:
                return header

    return None


# =====================================================
# HELPER — NORMALIZE CSV ROW
# =====================================================

def normalize_statement_row(row, headers):
    """
    Convert different bank CSV formats into a
    common internal structure.
    """

    # -------------------------------------------------
    # FIND COMMON COLUMNS
    # -------------------------------------------------

    date_column = find_column(
        headers,
        [
            "date",
            "transaction date",
            "txn date",
            "value date",
            "posting date"
        ]
    )

    description_column = find_column(
        headers,
        [
            "description",
            "narration",
            "transaction details",
            "details",
            "particulars",
            "remarks"
        ]
    )

    reference_column = find_column(
        headers,
        [
            "reference",
            "reference no",
            "reference number",
            "transaction id",
            "txn id",
            "ref no"
        ]
    )

    debit_column = find_column(
        headers,
        [
            "debit",
            "withdrawal",
            "withdrawals",
            "debit amount",
            "withdrawal amount"
        ]
    )

    credit_column = find_column(
        headers,
        [
            "credit",
            "deposit",
            "deposits",
            "credit amount",
            "deposit amount"
        ]
    )

    amount_column = find_column(
        headers,
        [
            "amount",
            "transaction amount",
            "txn amount"
        ]
    )

    balance_column = find_column(
        headers,
        [
            "balance",
            "closing balance",
            "available balance"
        ]
    )

    # -------------------------------------------------
    # READ VALUES
    # -------------------------------------------------

    transaction_date = (
        row.get(date_column)
        if date_column
        else None
    )

    description = (
        row.get(description_column)
        if description_column
        else None
    )

    reference = (
        row.get(reference_column)
        if reference_column
        else None
    )

    debit = (
        parse_decimal(row.get(debit_column))
        if debit_column
        else None
    )

    credit = (
        parse_decimal(row.get(credit_column))
        if credit_column
        else None
    )

    amount = (
        parse_decimal(row.get(amount_column))
        if amount_column
        else None
    )

    balance = (
        parse_decimal(row.get(balance_column))
        if balance_column
        else None
    )

    # -------------------------------------------------
    # IF AMOUNT EXISTS BUT DEBIT/CREDIT DOES NOT,
    # KEEP THE AMOUNT AS-IS.
    # -------------------------------------------------

    if amount is not None and debit is None and credit is None:

        # Negative amount = debit
        if amount < 0:
            debit = abs(amount)

        # Positive amount = credit
        elif amount > 0:
            credit = amount

    # -------------------------------------------------
    # CONVERT RAW DATA TO JSON
    # -------------------------------------------------

    try:
        raw_data = json.dumps(
            row,
            ensure_ascii=False,
            default=str
        )

    except Exception:
        raw_data = str(row)

    return {
        "transaction_date": transaction_date,
        "description": description,
        "reference": reference,
        "debit": debit,
        "credit": credit,
        "amount": amount,
        "balance": balance,
        "raw_data": raw_data
    }


# =====================================================
# GET — LIST STATEMENT IMPORTS
# =====================================================

@router.get("/")
def get_statement_imports(
    db: Session = Depends(get_db)
):

    ensure_statements_tables(db)

    result = db.execute(
        text(
            """
            SELECT
                id,
                file_name,
                file_type,
                account_id,
                source,
                status,
                total_rows,
                imported_rows,
                duplicate_rows,
                error_rows,
                created_at,
                updated_at
            FROM statement_imports
            ORDER BY id DESC
            """
        )
    )

    return [
        dict(row)
        for row in result.mappings().all()
    ]


# =====================================================
# GET — SINGLE STATEMENT IMPORT
# =====================================================

@router.get("/{statement_id}")
def get_statement_import(
    statement_id: int,
    db: Session = Depends(get_db)
):

    ensure_statements_tables(db)

    result = db.execute(
        text(
            """
            SELECT
                id,
                file_name,
                file_type,
                account_id,
                source,
                status,
                total_rows,
                imported_rows,
                duplicate_rows,
                error_rows,
                created_at,
                updated_at
            FROM statement_imports
            WHERE id = :statement_id
            """
        ),
        {
            "statement_id": statement_id
        }
    )

    statement = result.mappings().first()

    if not statement:
        raise HTTPException(
            status_code=404,
            detail="Statement import not found."
        )

    return dict(statement)


# =====================================================
# GET — STATEMENT ROWS
# =====================================================

@router.get("/{statement_id}/rows")
def get_statement_rows(
    statement_id: int,
    db: Session = Depends(get_db)
):

    ensure_statements_tables(db)

    # -------------------------------------------------
    # VERIFY IMPORT EXISTS
    # -------------------------------------------------

    statement_result = db.execute(
        text(
            """
            SELECT id
            FROM statement_imports
            WHERE id = :statement_id
            """
        ),
        {
            "statement_id": statement_id
        }
    )

    if not statement_result.first():
        raise HTTPException(
            status_code=404,
            detail="Statement import not found."
        )

    # -------------------------------------------------
    # LOAD ROWS
    # -------------------------------------------------

    result = db.execute(
        text(
            """
            SELECT
                id,
                statement_import_id,
                row_number,
                transaction_date,
                description,
                reference,
                debit,
                credit,
                amount,
                balance,
                currency,
                raw_data,
                classification,
                transaction_id,
                is_duplicate,
                is_reconciled,
                created_at
            FROM statement_rows
            WHERE statement_import_id = :statement_id
            ORDER BY row_number ASC
            """
        ),
        {
            "statement_id": statement_id
        }
    )

    return [
        dict(row)
        for row in result.mappings().all()
    ]


# =====================================================
# POST — IMPORT CSV STATEMENT
# =====================================================

@router.post("/import")
async def import_statement(
    file: UploadFile = File(...),

    account_id: int | None = Form(
        default=None
    ),

    source: str | None = Form(
        default=None
    ),

    db: Session = Depends(get_db)
):

    ensure_statements_tables(db)

    # -------------------------------------------------
    # VALIDATE FILE NAME
    # -------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="A statement file is required."
        )

    # -------------------------------------------------
    # CURRENT VERSION SUPPORTS CSV
    # -------------------------------------------------

    filename = file.filename.lower()

    if not filename.endswith(".csv"):

        raise HTTPException(
            status_code=400,
            detail=(
                "CSV import is currently supported. "
                "Excel and PDF import will be added in "
                "the next statement-import stage."
            )
        )

    # -------------------------------------------------
    # READ FILE
    # -------------------------------------------------

    try:

        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty."
            )

        # -------------------------------------------------
        # TRY UTF-8
        # -------------------------------------------------

        try:

            decoded = content.decode(
                "utf-8-sig"
            )

        except UnicodeDecodeError:

            decoded = content.decode(
                "latin-1"
            )

        # -------------------------------------------------
        # CREATE CSV READER
        # -------------------------------------------------

        csv_file = io.StringIO(
            decoded
        )

        reader = csv.DictReader(
            csv_file
        )

        headers = reader.fieldnames or []

        if not headers:

            raise HTTPException(
                status_code=400,
                detail="Unable to detect CSV columns."
            )

        rows = list(reader)

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unable to read CSV file: "
                + str(error)
            )
        )

    # -------------------------------------------------
    # CREATE IMPORT RECORD
    # -------------------------------------------------

    import_result = db.execute(
        text(
            """
            INSERT INTO statement_imports (
                file_name,
                file_type,
                account_id,
                source,
                status,
                total_rows,
                imported_rows,
                duplicate_rows,
                error_rows
            )
            VALUES (
                :file_name,
                :file_type,
                :account_id,
                :source,
                'imported',
                :total_rows,
                0,
                0,
                0
            )
            RETURNING id
            """
        ),
        {
            "file_name": file.filename,
            "file_type": "csv",
            "account_id": account_id,
            "source": source,
            "total_rows": len(rows)
        }
    )

    statement_id = import_result.scalar()

    # -------------------------------------------------
    # IMPORT ROWS
    # -------------------------------------------------

    imported_rows = 0
    error_rows = 0

    for row_number, row in enumerate(
        rows,
        start=1
    ):

        try:

            normalized = normalize_statement_row(
                row,
                headers
            )

            db.execute(
                text(
                    """
                    INSERT INTO statement_rows (
                        statement_import_id,
                        row_number,
                        transaction_date,
                        description,
                        reference,
                        debit,
                        credit,
                        amount,
                        balance,
                        currency,
                        raw_data
                    )
                    VALUES (
                        :statement_import_id,
                        :row_number,
                        :transaction_date,
                        :description,
                        :reference,
                        :debit,
                        :credit,
                        :amount,
                        :balance,
                        'INR',
                        :raw_data
                    )
                    """
                ),
                {
                    "statement_import_id": statement_id,
                    "row_number": row_number,
                    "transaction_date": normalized[
                        "transaction_date"
                    ],
                    "description": normalized[
                        "description"
                    ],
                    "reference": normalized[
                        "reference"
                    ],
                    "debit": normalized[
                        "debit"
                    ],
                    "credit": normalized[
                        "credit"
                    ],
                    "amount": normalized[
                        "amount"
                    ],
                    "balance": normalized[
                        "balance"
                    ],
                    "raw_data": normalized[
                        "raw_data"
                    ]
                }
            )

            imported_rows += 1

        except Exception:

            error_rows += 1

    # -------------------------------------------------
    # UPDATE IMPORT SUMMARY
    # -------------------------------------------------

    status = (
        "imported"
        if error_rows == 0
        else "imported_with_errors"
    )

    db.execute(
        text(
            """
            UPDATE statement_imports
            SET
                status = :status,
                imported_rows = :imported_rows,
                error_rows = :error_rows,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :statement_id
            """
        ),
        {
            "status": status,
            "imported_rows": imported_rows,
            "error_rows": error_rows,
            "statement_id": statement_id
        }
    )

    db.commit()

    # -------------------------------------------------
    # RETURN IMPORT RESULT
    # -------------------------------------------------

    return {
        "success": True,
        "statement_id": statement_id,
        "file_name": file.filename,
        "file_type": "csv",
        "total_rows": len(rows),
        "imported_rows": imported_rows,
        "error_rows": error_rows,
        "status": status,
        "message": (
            "Statement imported successfully. "
            "No transactions were created automatically."
        )
    }


# =====================================================
# DELETE — STATEMENT IMPORT
# =====================================================

@router.delete("/{statement_id}")
def delete_statement_import(
    statement_id: int,
    db: Session = Depends(get_db)
):

    ensure_statements_tables(db)

    # -------------------------------------------------
    # DELETE ROWS FIRST
    # -------------------------------------------------

    db.execute(
        text(
            """
            DELETE FROM statement_rows
            WHERE statement_import_id = :statement_id
            """
        ),
        {
            "statement_id": statement_id
        }
    )

    # -------------------------------------------------
    # DELETE IMPORT RECORD
    # -------------------------------------------------

    result = db.execute(
        text(
            """
            DELETE FROM statement_imports
            WHERE id = :statement_id
            """
        ),
        {
            "statement_id": statement_id
        }
    )

    if result.rowcount == 0:

        db.rollback()

        raise HTTPException(
            status_code=404,
            detail="Statement import not found."
        )

    db.commit()

    return {
        "success": True,
        "statement_id": statement_id,
        "message": "Statement import deleted successfully."
    }

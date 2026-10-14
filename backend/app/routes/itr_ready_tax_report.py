"""
ITR-Ready Tax Report Engine v1.0

Purpose:
- Consolidate the existing tax engines into one structured report.
- Provide ITR-preparation data in a read-only format.
- Do not write anything to the database.
- Clearly identify unavailable income heads and unverified deductions.

This is NOT an ITR filing engine.
It prepares structured tax data for further ITR filing/review.
"""

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
import re

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.routes.ownership import require_matching_user_id
from app.routes.final_tax_liability import calculate_surcharge
from app.models import TaxBusinessIncomeRecord, TaxDeductionClaim, TaxCreditEntry, TaxSalaryIncomeRecord, TaxHousePropertyRecord
from app.house_property_calc import compute_house_property
from app.routes.deductions_exempt_income import (
    DEDUCTION_CATALOG,
    EXEMPT_INCOME_CATALOG,
    HRAInputs,
    calculate_hra_exemption,
    regime_available,
)


router = APIRouter(
    prefix="/api/itr-ready-tax-report",
    tags=["ITR Ready Tax Report"],
)


# ============================================================
# CONSTANTS
# ============================================================

STCG_111A_RATE = Decimal("0.20")
LTCG_112A_RATE = Decimal("0.125")
LTCG_112A_EXEMPTION = Decimal("125000")

CESS_RATE = Decimal("0.04")

NEW_REGIME_REBATE_LIMIT = Decimal("1200000")
NEW_REGIME_REBATE_MAX = Decimal("60000")

OLD_REGIME_REBATE_LIMIT = Decimal("500000")
OLD_REGIME_REBATE_MAX = Decimal("12500")


# ============================================================
# BASIC HELPERS
# ============================================================

def decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")

    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")




def summarize_verified_business_records(records):
    """Summarize reviewed business records without treating pending claims as taxable profit."""
    receipts = Decimal("0")
    expenses = Decimal("0")
    count = 0
    for record in records:
        if getattr(record, "status", None) != "verified":
            continue
        amount = max(decimal(getattr(record, "amount", 0)), Decimal("0"))
        record_type = getattr(record, "record_type", None)
        if record_type == "receipt":
            receipts += amount
            count += 1
        elif record_type == "expense":
            expenses += amount
            count += 1
    return {
        "verified_receipts": receipts,
        "verified_expenses": expenses,
        "net_profit_before_tax_rules": receipts - expenses,
        "verified_record_count": count,
    }


def extract_gross_salary(description) -> Decimal | None:
    """Extract the gross salary saved alongside a net salary transaction."""
    match = re.search(
        r"gross\s+salary\s*:\s*(?:₹|INR)?\s*([0-9,]+(?:\.[0-9]{1,2})?)",
        str(description or ""),
        re.IGNORECASE,
    )
    if not match:
        return None
    try:
        return Decimal(match.group(1).replace(",", ""))
    except Exception:
        return None


def money(value) -> float:
    return float(
        decimal(value).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
    )


def apply_verified_annual_salary_record(other_income: dict, salary_record):
    """Use one verified annual gross salary amount without counting bank credits twice."""
    if salary_record is None:
        return other_income

    gross_salary = decimal(salary_record.gross_salary)
    other_income["salary"] = gross_salary
    other_income["details"] = [
        item for item in other_income["details"] if item.get("tax_head") != "salary"
    ]
    other_income["details"].append({
        "transaction_id": None,
        "type": "annual_salary_record",
        "amount": money(gross_salary),
        "date": None,
        "category": "Verified annual salary",
        "description": "Gross salary from verified annual salary record; linked bank credits are not counted again.",
        "tax_head": "salary",
        "tax_amount": money(gross_salary),
        "classification_source": "verified_annual_salary_record",
    })
    other_income["classification_review"] = [
        item for item in other_income["classification_review"]
        if "Salary receipt has no saved Gross salary metadata" not in str(item.get("reason", ""))
        and "Saved gross salary is lower than the transaction receipt" not in str(item.get("reason", ""))
    ]
    other_income["total"] = sum(
        (decimal(other_income[key]) for key in ("salary", "income", "interest", "dividend")),
        Decimal("0"),
    )
    other_income["other_sources_total"] = sum(
        (decimal(other_income[key]) for key in ("income", "interest", "dividend")),
        Decimal("0"),
    )
    return other_income


def get_financial_year_dates(financial_year: str):
    """
    Convert:
        2026-27
    into:
        2026-04-01 to 2027-03-31
    """

    start_year = int(financial_year.split("-")[0])

    start_date = date(start_year, 4, 1)
    end_date = date(start_year + 1, 3, 31)

    return start_date, end_date


def classify_asset(investment_type):
    """
    Read-only asset classification.

    Current supported mapping follows the existing
    Financial OS tax classification approach.
    """

    value = str(investment_type or "").strip().lower()

    if value in {
        "stock",
        "stocks",
        "equity",
        "listed equity",
        "listed_equity",
    }:
        return "listed_equity"

    if value in {
        "equity mutual fund",
        "equity mutual funds",
        "equity_mf",
        "equity_mf_fund",
        "equity oriented mf",
    }:
        return "equity_oriented_mf"

    if value in {
        "etf",
        "listed other security",
        "listed_other_security",
    }:
        return "listed_other_security"

    if value in {
        "unlisted equity",
        "unlisted_equity",
    }:
        return "unlisted_equity"

    if value in {
        "unlisted other security",
        "unlisted_other_security",
    }:
        return "unlisted_other_security"

    return "unclassified"


def long_term_threshold(asset_class):
    if asset_class in {
        "listed_equity",
        "equity_oriented_mf",
        "listed_other_security",
    }:
        return 365

    if asset_class in {
        "unlisted_equity",
        "unlisted_other_security",
    }:
        return 730

    return None


# ============================================================
# INVESTMENT DATA
# ============================================================

def load_investments(db: Session, user_id: int):
    query = text(
        """
        SELECT
            id,
            name,
            investment_type,
            symbol,
            quantity,
            buy_price,
            current_price,
            price_source,
            price_updated_at,
            buy_date,
            broker,
            fees
        FROM investments
        WHERE user_id = :user_id
        ORDER BY id
        """
    )

    rows = db.execute(
        query,
        {"user_id": user_id},
    ).mappings().all()

    return rows


def load_investment_transactions(db: Session, user_id: int):
    query = text(
        """
        SELECT
            id,
            investment_id,
            transaction_type,
            quantity,
            price,
            fees,
            transaction_date
        FROM investment_transactions
        WHERE user_id = :user_id
        ORDER BY transaction_date, id
        """
    )

    rows = db.execute(
        query,
        {"user_id": user_id},
    ).mappings().all()

    return rows


# ============================================================
# CAPITAL GAINS
# ============================================================

def calculate_capital_gains(
    db: Session,
    user_id: int,
    start_date: date,
    end_date: date,
):
    investments = load_investments(db, user_id)
    investment_transactions = load_investment_transactions(
        db,
        user_id,
    )

    investment_map = {
        int(row["id"]): row
        for row in investments
    }

    # FIFO buy lots per investment.
    lots = defaultdict(list)

    for row in investment_transactions:
        investment_id = int(row["investment_id"])

        quantity = decimal(row["quantity"])
        price = decimal(row["price"])
        fees = decimal(row["fees"])

        transaction_type = str(
            row["transaction_type"] or ""
        ).upper()

        transaction_date = row["transaction_date"]

        if transaction_type == "BUY":
            lots[investment_id].append(
                {
                    "transaction_id": int(row["id"]),
                    "quantity": quantity,
                    "remaining_quantity": quantity,
                    "price": price,
                    "fees": fees,
                    "transaction_date": transaction_date,
                }
            )

    sales = []

    for row in investment_transactions:
        transaction_type = str(
            row["transaction_type"] or ""
        ).upper()

        if transaction_type != "SELL":
            continue

        sale_date = row["transaction_date"]

        if sale_date is None:
            continue

        if isinstance(sale_date, datetime):
            sale_date = sale_date.date()

        if sale_date < start_date or sale_date > end_date:
            continue

        investment_id = int(row["investment_id"])

        sale_quantity = decimal(row["quantity"])
        sale_price = decimal(row["price"])
        sale_fees = decimal(row["fees"])

        investment = investment_map.get(investment_id)

        if not investment:
            continue

        asset_class = classify_asset(
            investment["investment_type"]
        )

        threshold = long_term_threshold(asset_class)

        remaining_sale_quantity = sale_quantity
        matched_lots = []

        total_cost_basis = Decimal("0")
        total_gain = Decimal("0")

        while remaining_sale_quantity > 0 and lots[investment_id]:

            lot = lots[investment_id][0]

            available_quantity = decimal(
                lot["remaining_quantity"]
            )

            matched_quantity = min(
                remaining_sale_quantity,
                available_quantity,
            )

            buy_price = decimal(lot["price"])
            buy_fees = decimal(lot["fees"])

            original_quantity = decimal(
                lot["quantity"]
            )

            # Allocate BUY fees proportionally.
            allocated_buy_fees = Decimal("0")

            if original_quantity > 0:
                allocated_buy_fees = (
                    buy_fees
                    * matched_quantity
                    / original_quantity
                )

            cost_basis = (
                matched_quantity * buy_price
            ) + allocated_buy_fees

            proceeds_before_fees = (
                matched_quantity * sale_price
            )

            # Allocate SELL fees proportionally.
            allocated_sale_fees = Decimal("0")

            if sale_quantity > 0:
                allocated_sale_fees = (
                    sale_fees
                    * matched_quantity
                    / sale_quantity
                )

            proceeds_after_fees = (
                proceeds_before_fees
                - allocated_sale_fees
            )

            gain = (
                proceeds_after_fees
                - cost_basis
            )

            buy_date = lot["transaction_date"]

            if isinstance(buy_date, datetime):
                buy_date = buy_date.date()

            holding_days = None

            if buy_date and sale_date:
                holding_days = (
                    sale_date - buy_date
                ).days

            if threshold is None:
                classification = "UNCLASSIFIED"

            elif holding_days >= threshold:
                classification = "LTCG"

            else:
                classification = "STCG"

            matched_lots.append(
                {
                    "buy_transaction_id": lot["transaction_id"],
                    "buy_date": str(buy_date),
                    "quantity": money(matched_quantity),
                    "price": money(buy_price),
                    "cost_basis": money(cost_basis),
                    "holding_days": holding_days,
                    "classification": classification,
                }
            )

            total_cost_basis += cost_basis
            total_gain += gain

            lot["remaining_quantity"] -= matched_quantity
            remaining_sale_quantity -= matched_quantity

            if lot["remaining_quantity"] <= 0:
                lots[investment_id].pop(0)

        if remaining_sale_quantity > 0:
            unmatched_quantity = remaining_sale_quantity
        else:
            unmatched_quantity = Decimal("0")

        if matched_lots:
            sale_classifications = {
                item["classification"]
                for item in matched_lots
            }

            if sale_classifications == {"LTCG"}:
                sale_classification = "LTCG"

            elif sale_classifications == {"STCG"}:
                sale_classification = "STCG"

            else:
                sale_classification = "MIXED"

        else:
            sale_classification = "UNCLASSIFIED"

        sales.append(
            {
                "sale_transaction_id": int(row["id"]),
                "investment_id": investment_id,
                "name": investment["name"],
                "symbol": investment["symbol"],
                "investment_type": investment["investment_type"],
                "asset_class": asset_class,
                "sale_date": str(sale_date),
                "quantity": money(sale_quantity),
                "sale_price": money(sale_price),
                "cost_basis": money(total_cost_basis),
                "gain": money(total_gain),
                "classification": sale_classification,
                "matched_lots": matched_lots,
                "unmatched_quantity": money(
                    unmatched_quantity
                ),
            }
        )

    stcg = Decimal("0")
    ltcg = Decimal("0")
    unclassified_gain = Decimal("0")

    for sale in sales:
        gain = decimal(sale["gain"])

        if sale["classification"] == "STCG":
            stcg += gain

        elif sale["classification"] == "LTCG":
            ltcg += gain

        else:
            unclassified_gain += gain

    return {
        "sales": sales,
        "stcg": stcg,
        "ltcg": ltcg,
        "unclassified_gain": unclassified_gain,
    }


# ============================================================
# OTHER INCOME
# ============================================================

def load_other_income(
    db: Session,
    user_id: int,
    start_date: date,
    end_date: date,
):
    """Classify existing Money transactions for tax reporting.

    This is read-only. Loan/borrowing proceeds are excluded first.
    A specific category or transaction type is respected unless it is
    a generic income entry; descriptive keywords can then fill gaps.
    Conflicts are returned for review rather than silently overwritten.
    """
    query = text(
        """
        SELECT
            t.id,
            t.transaction_type,
            t.amount,
            t.transaction_date,
            t.description,
            COALESCE(c.name, '') AS category_name,
            COALESCE(c.description, '') AS category_description,
            t.party_name,
            t.due_date,
            COALESCE(t.settled_amount, 0) AS settled_amount,
            COALESCE(t.status, 'open') AS receivable_status
        FROM transactions AS t
        LEFT JOIN categories AS c
          ON c.id = t.category_id AND c.user_id = t.user_id
        WHERE t.user_id = :user_id
          AND t.transaction_date >= :start_date
          AND t.transaction_date <= :end_date
          AND LOWER(COALESCE(t.transaction_type, '')) IN (
              'income', 'interest', 'dividend', 'receivable'
          )
        ORDER BY t.transaction_date, t.id
        """
    )
    rows = db.execute(
        query,
        {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    ).mappings().all()

    totals = {
        "salary": Decimal("0"),
        "income": Decimal("0"),
        "interest": Decimal("0"),
        "dividend": Decimal("0"),
    }
    details = []
    excluded_loan_proceeds = []
    classification_review = []
    receivable_review = []

    loan_terms = (
        "loan disbursement", "loan disbursed", "loan received", "loan proceeds",
        "home loan received", "personal loan received", "borrowed",
        "borrowing", "loan credit", "loan amount received",
    )
    keyword_heads = {
        "salary": ("salary", "payroll", "wages", "form 16"),
        "interest": ("interest income", "bank interest", "savings interest", "fd interest", "fixed deposit interest"),
        "dividend": ("dividend",),
    }

    for row in rows:
        amount = decimal(row["amount"])
        transaction_type = str(row["transaction_type"] or "").strip().lower()
        category = str(row["category_name"] or "").strip().lower()
        category_description = str(row["category_description"] or "").strip().lower()
        description = str(row["description"] or "").strip().lower()
        searchable = " ".join((category, category_description, description))
        category_looks_like_borrowing = (
            "loan" in category
            and "interest" not in category
            and "repayment" not in category
        )
        original = {
            "transaction_id": int(row["id"]),
            "type": transaction_type,
            "amount": money(amount),
            "date": str(row["transaction_date"]),
            "category": row["category_name"] or None,
            "description": row["description"],
        }

        # Receivables represent earned/claimed amounts not yet collected. The
        # accounting entry alone does not establish the applicable tax head or
        # the taxpayer's accounting method. Surface them for reconciliation,
        # rather than silently omitting them or treating every receivable as
        # taxable Other Sources income. Settlement transfers are intentionally
        # excluded by this query, so collection cannot double-count income.
        if transaction_type == "receivable":
            # Category mapping is a review hint only. It must not independently
            # determine taxability: the taxpayer's accounting method, source
            # documents, and applicable tax rules still need confirmation.
            suggested_head = None
            if any(term in searchable for term in (
                "business", "professional", "freelance", "gig", "customer invoice",
                "service income", "business revenue",
            )):
                suggested_head = "business_profession"
            elif any(term in searchable for term in ("rental", "rent", "house property")):
                suggested_head = "house_property"
            elif any(term in searchable for term in ("salary", "payroll", "wages")):
                suggested_head = "salary"
            elif any(term in searchable for term in ("interest", "dividend", "other sources")):
                suggested_head = "other_sources"

            settled_amount = max(decimal(row.get("settled_amount", 0)), Decimal("0"))
            outstanding_amount = max(amount - settled_amount, Decimal("0"))
            receivable_review.append({
                **original,
                "party_name": row.get("party_name"),
                "due_date": str(row.get("due_date")) if row.get("due_date") else None,
                "settled_amount": money(settled_amount),
                "outstanding_amount": money(outstanding_amount),
                "status": row.get("receivable_status") or "open",
                "tax_head": None,
                "suggested_tax_head": suggested_head,
                "included_in_taxable_totals": False,
                "reason": (
                    "Suggested tax head is based on the category/description only. "
                    "Confirm source documents and the applicable accounting method "
                    "before including this receivable in taxable income. Collections "
                    "against this receivable must not be counted as income a second time."
                ),
            })
            continue

        # Loan proceeds are not income, even when entered through Money > Income.
        if category_looks_like_borrowing or any(term in searchable for term in loan_terms):
            excluded_loan_proceeds.append({**original, "reason": "Likely loan/borrowing proceeds; excluded from taxable income and flagged for review."})
            continue

        # Rent receipts belong to the house-property head, which is computed only
        # from verified house-property records. Show them for review and never
        # count them as other-source income.
        if "house property" in category:
            classification_review.append({**original, "suggested_head": "house_property", "reason": "Rent receipt belongs to house property income. It is counted only through a verified house property record."})
            continue

        detected = None
        for head, terms in keyword_heads.items():
            if any(term in searchable for term in terms):
                detected = head
                break

        # A specific existing transaction type wins unless the entry is generic income.
        if transaction_type in ("interest", "dividend"):
            selected_head = transaction_type
            if detected and detected != selected_head:
                classification_review.append({**original, "suggested_head": detected, "reason": "Description/category conflicts with transaction type; review classification."})
        elif detected:
            selected_head = detected
        else:
            selected_head = "income"

        # Salary is taxable on gross salary, not the net bank credit. The
        # Money transaction remains the actual net receipt; salary metadata
        # supplies gross salary as the tax-reporting amount.
        gross_salary = extract_gross_salary(row["description"]) if selected_head == "salary" else None
        if selected_head == "salary":
            if gross_salary is None:
                classification_review.append({
                    **original,
                    "suggested_head": "salary",
                    "reason": "Salary receipt has no saved Gross salary metadata. Net receipt was not treated as taxable gross salary; add salary components/Form 16 data.",
                })
                continue
            if gross_salary < 0 or gross_salary < amount:
                classification_review.append({
                    **original,
                    "suggested_head": "salary",
                    "reason": "Saved gross salary is lower than the transaction receipt or invalid; review salary metadata before using it for tax.",
                })
                continue
            tax_amount = gross_salary
        else:
            tax_amount = amount

        totals[selected_head] += tax_amount
        details.append({
            **original,
            "tax_head": selected_head,
            "tax_amount": money(tax_amount),
            "classification_source": "salary_metadata" if selected_head == "salary" else ("keyword/category" if detected else "transaction_type"),
        })

    return {
        **totals,
        "total": totals["salary"] + totals["income"] + totals["interest"] + totals["dividend"],
        "other_sources_total": totals["income"] + totals["interest"] + totals["dividend"],
        "details": details,
        "excluded_loan_proceeds": excluded_loan_proceeds,
        "classification_review": classification_review,
        "receivable_review": receivable_review,
        "transaction_count": len(details),
    }


# ============================================================
# TAX CALCULATION
# ============================================================

def calculate_new_regime_slab_tax(
    taxable_income: Decimal,
):
    income = max(taxable_income, Decimal("0"))
    tax = Decimal("0")

    slabs = [
        (Decimal("400000"), Decimal("0.00")),
        (Decimal("800000"), Decimal("0.05")),
        (Decimal("1200000"), Decimal("0.10")),
        (Decimal("1600000"), Decimal("0.15")),
        (Decimal("2000000"), Decimal("0.20")),
        (Decimal("2400000"), Decimal("0.25")),
        (None, Decimal("0.30")),
    ]

    previous = Decimal("0")

    for upper, rate in slabs:
        if upper is None:
            taxable_amount = max(
                income - previous,
                Decimal("0"),
            )
        else:
            taxable_amount = max(
                min(income, upper) - previous,
                Decimal("0"),
            )

        tax += taxable_amount * rate

        if upper is None or income <= upper:
            break

        previous = upper

    return tax


def calculate_old_regime_slab_tax(
    taxable_income: Decimal,
):
    income = max(taxable_income, Decimal("0"))
    tax = Decimal("0")

    if income > Decimal("1000000"):
        tax += (
            income - Decimal("1000000")
        ) * Decimal("0.30")

        income = Decimal("1000000")

    if income > Decimal("500000"):
        tax += (
            income - Decimal("500000")
        ) * Decimal("0.20")

        income = Decimal("500000")

    if income > Decimal("250000"):
        tax += (
            income - Decimal("250000")
        ) * Decimal("0.05")

    return tax


# ============================================================
# FINAL REPORT
# ============================================================

@router.get("/", dependencies=[Depends(require_matching_user_id)])
def get_itr_ready_tax_report(
    user_id: int = Query(..., ge=1),
    financial_year: str = Query("2026-27"),
    regime: str = Query("new"),
    stt_confirmed: bool = Query(False),
    db: Session = Depends(get_db),
):
    """
    Generate consolidated ITR-ready tax report.

    Read-only:
    - No database INSERT
    - No database UPDATE
    - No database DELETE
    """

    regime = str(regime or "").strip().lower()
    if regime not in {"old", "new"}:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="regime must be 'old' or 'new'.")

    try:
        start_date, end_date = get_financial_year_dates(financial_year)
    except (ValueError, TypeError, IndexError):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="financial_year must use YYYY-YY format, for example 2026-27.")

    # --------------------------------------------------------
    # 1. OTHER SOURCE INCOME
    # --------------------------------------------------------

    # The verified annual salary record is authoritative for the selected FY.
    # Bank salary credits are cash-flow entries, not additional taxable salary.
    salary_record = db.query(TaxSalaryIncomeRecord).filter_by(
        user_id=user_id, financial_year=financial_year, status="verified"
    ).first()
    other_income = load_other_income(
        db,
        user_id,
        start_date,
        end_date,
    )
    other_income = apply_verified_annual_salary_record(other_income, salary_record)

    # --------------------------------------------------------
    # 2. CAPITAL GAINS
    # --------------------------------------------------------

    capital_gains = calculate_capital_gains(
        db,
        user_id,
        start_date,
        end_date,
    )

    stcg_before_setoff = capital_gains["stcg"]
    ltcg_before_setoff = capital_gains["ltcg"]

    # --------------------------------------------------------
    # 3. LOSS SET-OFF
    # --------------------------------------------------------

    stcg_loss = (
        abs(stcg_before_setoff)
        if stcg_before_setoff < 0
        else Decimal("0")
    )

    ltcg_loss = (
        abs(ltcg_before_setoff)
        if ltcg_before_setoff < 0
        else Decimal("0")
    )

    positive_stcg = max(
        stcg_before_setoff,
        Decimal("0"),
    )

    positive_ltcg = max(
        ltcg_before_setoff,
        Decimal("0"),
    )

    # STCL → STCG first.
    stcg_setoff = min(
        stcg_loss,
        positive_stcg,
    )

    remaining_stcg = (
        positive_stcg - stcg_setoff
    )

    remaining_stcg_loss = (
        stcg_loss - stcg_setoff
    )

    # Remaining STCL can be used against LTCG.
    stcl_against_ltcg = min(
        remaining_stcg_loss,
        positive_ltcg,
    )

    remaining_ltcg = (
        positive_ltcg
        - stcl_against_ltcg
    )

    # LTCL → LTCG.
    ltcl_against_ltcg = min(
        ltcg_loss,
        remaining_ltcg,
    )

    remaining_ltcg = (
        remaining_ltcg
        - ltcl_against_ltcg
    )

    remaining_ltcg_loss = (
        ltcg_loss
        - ltcl_against_ltcg
    )

    # --------------------------------------------------------
    # 4. DEDUCTIONS / EXEMPT INCOME
    # --------------------------------------------------------

    # Only verified claims for this user/FY/regime may reduce taxable income.
    # The statutory salary standard deduction is applied automatically when
    # there is a live gross-salary source; it is not a user-entered expense.
    verified_claims = (
        db.query(TaxDeductionClaim)
        .filter(
            TaxDeductionClaim.user_id == user_id,
            TaxDeductionClaim.financial_year == financial_year,
            TaxDeductionClaim.tax_regime == regime.lower(),
            TaxDeductionClaim.status == "verified",
        )
        .all()
    )
    exempt_keys = set(EXEMPT_INCOME_CATALOG)
    claims_by_key = {}
    for claim in verified_claims:
        if claim.deduction_key in exempt_keys:
            continue
        item = DEDUCTION_CATALOG.get(claim.deduction_key)
        if not item or not regime_available(item, regime.lower()):
            continue
        claims_by_key[claim.deduction_key] = claims_by_key.get(
            claim.deduction_key, Decimal("0")
        ) + decimal(claim.claimed_amount)

    verified_deductions = Decimal("0")
    deduction_details = []
    for key, claimed in claims_by_key.items():
        item = DEDUCTION_CATALOG[key]
        limits = item.get("maximum_amount_by_regime", {})
        limit = limits.get(regime.lower(), item.get("maximum_amount"))
        applied = min(claimed, Decimal(str(limit))) if limit is not None else claimed
        # Standard deduction is statutory/automatic and calculated below.
        if key == "STANDARD_DEDUCTION_SALARY":
            continue
        verified_deductions += applied
        deduction_details.append({
            "deduction_key": key,
            "section": item.get("section"),
            "claimed_amount": money(claimed),
            "applied_amount": money(applied),
        })

    salary_record = db.query(TaxSalaryIncomeRecord).filter_by(
        user_id=user_id, financial_year=financial_year, status="verified"
    ).first()
    standard_deduction = Decimal("0")
    verified_exempt_income = Decimal("0")
    exempt_claim_details = []

    # --------------------------------------------------------
    # 5. INCOME HEAD AVAILABILITY
    # --------------------------------------------------------

    salary_available = other_income["salary"] > 0
    house_property_records_verified = db.query(TaxHousePropertyRecord).filter_by(
        user_id=user_id, financial_year=financial_year, status="verified"
    ).all()
    house_property_result = (
        compute_house_property(house_property_records_verified, regime)
        if house_property_records_verified
        else None
    )
    house_property_available = house_property_result is not None
    business_available = False

    salary_income = other_income["salary"]
    # Statutory standard deduction for salary/pension, based on the current
    # regime's catalogue limit. It applies only when gross salary was parsed
    # from a linked transaction; it is never manufactured from a net receipt.
    if salary_income > 0:
        standard_item = DEDUCTION_CATALOG.get("STANDARD_DEDUCTION_SALARY", {})
        standard_limits = standard_item.get("maximum_amount_by_regime", {})
        standard_deduction = min(
            salary_income,
            Decimal(str(standard_limits.get(regime.lower(), 0))),
        )
        verified_deductions += standard_deduction
        deduction_details.append({
            "deduction_key": "STANDARD_DEDUCTION_SALARY",
            "section": standard_item.get("section", "Section 16(ia)"),
            "claimed_amount": money(standard_deduction),
            "applied_amount": money(standard_deduction),
            "automatic": True,
        })
    house_property_income = (
        Decimal(str(house_property_result["counted_amount"]))
        if house_property_result is not None
        else Decimal("0")
    )
    business_income = Decimal("0")
    business_summary = summarize_verified_business_records(
        db.query(TaxBusinessIncomeRecord).filter_by(
            user_id=user_id, financial_year=financial_year
        ).all()
    )
    # Only reviewed records are included. Pending/self-reported records remain
    # disclosed but do not affect taxable income. A positive net profit is added
    # to the provisional total; a loss is not silently set off without the
    # applicable business-loss rules and supporting schedules.
    if business_summary["verified_record_count"] > 0:
        business_available = True
        business_income = max(
            business_summary["net_profit_before_tax_rules"], Decimal("0")
        )

    # HRA exemption is applied only against transaction-backed gross salary,
    # with a verified annual salary/HRA record, and only under the old regime.
    for claim in verified_claims:
        if claim.deduction_key not in EXEMPT_INCOME_CATALOG:
            continue
        item = EXEMPT_INCOME_CATALOG[claim.deduction_key]
        if not regime_available(item, regime.lower()):
            continue
        claimed_amount = max(decimal(claim.claimed_amount), Decimal("0"))
        applied_amount = Decimal("0")
        application_status = "disclosed_not_applied_without_matching_income_source"
        if (
            claim.deduction_key == "hra_exemption"
            and regime.lower() == "old"
            and salary_income > 0
            and salary_record is not None
        ):
            try:
                hra_inputs = HRAInputs(
                    annual_basic_salary=salary_record.annual_basic_salary,
                    annual_da_forming_retirement_benefits=salary_record.annual_da_forming_retirement_benefits,
                    annual_commission_on_turnover_at_fixed_percentage=salary_record.annual_commission_on_turnover_at_fixed_percentage,
                    annual_hra_received=salary_record.annual_hra_received,
                    annual_rent_paid=salary_record.annual_rent_paid,
                    accommodation_owned_by_taxpayer=salary_record.accommodation_owned_by_taxpayer,
                    rent_actually_paid=salary_record.rent_actually_paid,
                    city=salary_record.city,
                )
                hra_limit = decimal(calculate_hra_exemption(hra_inputs, "old", financial_year)["calculated_exemption"])
                applied_amount = min(claimed_amount, hra_limit, salary_income)
                application_status = "applied_to_salary_capped_by_verified_hra_calculation" if applied_amount > 0 else "not_applied_calculated_limit_zero"
            except (ValueError, TypeError):
                application_status = "not_applied_hra_inputs_invalid"
        verified_exempt_income += applied_amount
        exempt_claim_details.append({
            "exemption_key": claim.deduction_key,
            "section": item.get("section"),
            "claimed_amount": money(claimed_amount),
            "applied_amount": money(applied_amount),
            "application_status": application_status,
        })

    # --------------------------------------------------------
    # 6. PROVISIONAL TAXABLE INCOME
    # --------------------------------------------------------

    capital_gain_income = (
        remaining_stcg
        + remaining_ltcg
    )

    normal_income = (
        other_income["other_sources_total"]
        + salary_income
        + house_property_income
        + business_income
    )

    gross_provisional_income = (
        normal_income
        + capital_gain_income
    )

    provisional_taxable_income = max(
        gross_provisional_income
        - verified_deductions
        - verified_exempt_income,
        Decimal("0"),
    )

    # --------------------------------------------------------
    # 7. SPECIAL-RATE TAX
    # --------------------------------------------------------

    if stt_confirmed:
        stcg_tax = (
            remaining_stcg
            * STCG_111A_RATE
        )
    else:
        stcg_tax = Decimal("0")

    taxable_ltcg_112a = max(
        remaining_ltcg
        - LTCG_112A_EXEMPTION,
        Decimal("0"),
    )

    ltcg_tax = (
        taxable_ltcg_112a
        * LTCG_112A_RATE
    )

    special_rate_tax = (
        stcg_tax
        + ltcg_tax
    )

    # --------------------------------------------------------
    # 8. NORMAL SLAB TAX
    # --------------------------------------------------------

    # Deduction claims are currently unavailable in this repository, so
    # verified_deductions remains zero until a verified claims workflow is
    # implemented. When verified claims become available, apply them to
    # normal-rate income before calculating slab tax; do not calculate slab
    # tax on gross normal income and report a different taxable-income figure.
    normal_taxable_income = max(
        normal_income - verified_deductions - verified_exempt_income,
        Decimal("0"),
    )

    if regime == "old":
        normal_tax = calculate_old_regime_slab_tax(
            normal_taxable_income
        )

        rebate_limit = OLD_REGIME_REBATE_LIMIT
        rebate_max = OLD_REGIME_REBATE_MAX

    else:
        normal_tax = calculate_new_regime_slab_tax(
            normal_taxable_income
        )

        rebate_limit = NEW_REGIME_REBATE_LIMIT
        rebate_max = NEW_REGIME_REBATE_MAX

    # 87A rebate is applied only against normal slab tax.
    # Capital gains special-rate tax is kept separate.
    if provisional_taxable_income <= rebate_limit:
        rebate_87a = min(
            normal_tax,
            rebate_max,
        )
    else:
        rebate_87a = Decimal("0")

    tax_after_rebate = max(
        normal_tax - rebate_87a,
        Decimal("0"),
    )

    tax_before_surcharge = (
        tax_after_rebate
        + special_rate_tax
    )

    # --------------------------------------------------------
    # 9. SURCHARGE
    # --------------------------------------------------------

    # Use the shared surcharge/marginal-relief rules rather than assuming
    # surcharge is always zero. Keep the breakdown visible for review.
    surcharge_calculation = calculate_surcharge(
        provisional_taxable_income,
        tax_after_rebate,
        special_rate_tax,
        regime.lower(),
    )
    surcharge = decimal(surcharge_calculation.get("total", 0))

    tax_after_surcharge = tax_before_surcharge + surcharge

    # --------------------------------------------------------
    # 10. CESS
    # --------------------------------------------------------

    cess = (
        tax_after_surcharge
        * CESS_RATE
    )

    total_tax_payable = (
        tax_after_surcharge
        + cess
    )

    # --------------------------------------------------------
    # TAX CREDITS: TDS/TCS/advance/self-assessment tax
    # --------------------------------------------------------
    credit_rows = (
        db.query(TaxCreditEntry)
        .filter(
            TaxCreditEntry.user_id == user_id,
            TaxCreditEntry.financial_year == financial_year,
        )
        .all()
    )
    credit_aliases = {
        "tds": "tds",
        "tax_deducted_at_source": "tds",
        "tcs": "tcs",
        "tax_collected_at_source": "tcs",
        "advance_tax": "advance_tax",
        "self_assessment_tax": "self_assessment_tax",
    }
    verified_credits = {key: Decimal("0") for key in ("tds", "tcs", "advance_tax", "self_assessment_tax")}
    pending_credits = {key: Decimal("0") for key in verified_credits}
    credit_details = []
    for entry in credit_rows:
        raw_type = str(entry.credit_type or "").strip().lower().replace(" ", "_").replace("-", "_")
        normalized_type = credit_aliases.get(raw_type)
        amount = decimal(entry.amount)
        status = str(entry.status or "pending_review").lower()
        if normalized_type and amount > 0:
            if status == "verified":
                verified_credits[normalized_type] += amount
            else:
                pending_credits[normalized_type] += amount
        credit_details.append({
            "id": entry.id,
            "credit_type": entry.credit_type,
            "amount": money(amount),
            "status": status,
            "source_reference": entry.source_reference,
        })
    total_verified_credits = sum(verified_credits.values(), Decimal("0"))
    balance_after_verified_credits = total_tax_payable - total_verified_credits

    # --------------------------------------------------------
    # 11. COMPLETENESS CHECK
    # --------------------------------------------------------

    missing_income_heads = []

    if not salary_available:
        missing_income_heads.append(
            "salary"
        )

    if not house_property_available:
        missing_income_heads.append(
            "house_property"
        )

    if not business_available:
        missing_income_heads.append(
            "business_or_profession"
        )

    # A generated report is not complete merely because the income-head
    # placeholders are populated. This endpoint currently has no verified
    # deduction-claim ledger, tax-credit reconciliation, residential-status
    # confirmation, or complete personal/filing details. Keep readiness
    # conservative until those inputs are genuinely connected and validated.
    missing_required_sections = [
        "verified_deductions_and_exemptions",
        "tds_and_advance_tax_reconciliation",
        "residential_status",
        "personal_and_filing_details",
        "itr_form_eligibility_validation",
    ]

    if not salary_available:
        missing_required_sections.append("salary_income")
    if not house_property_available:
        missing_required_sections.append("house_property_income")
    if not business_available:
        missing_required_sections.append("business_or_professional_income")

    # This report is preparatory only; it cannot claim final-review readiness
    # while required sections above are unavailable or unverified.
    report_complete = len(missing_required_sections) == 0
    report_status = (
        "ready_for_review"
        if report_complete
        else "incomplete_missing_required_data"
    )

    # --------------------------------------------------------
    # 12. ITR-READY REPORT
    # --------------------------------------------------------

    return {
        "status": "success",

        "engine": "ITR-Ready Tax Report Engine",
        "version": "1.0",
        "read_only": True,

        "financial_year": financial_year,
        "assessment_year": (
            f"AY {int(financial_year[:4]) + 1}-"
            f"{str(int(financial_year[:4]) + 2)[-2:]}"
        ),

        "period": {
            "start_date": str(start_date),
            "end_date": str(end_date),
        },

        "taxpayer": {
            "user_id": user_id,
            "taxpayer_type": "individual",
            "regime": regime.lower(),
            "stt_confirmed": stt_confirmed,
        },

        "income": {
            "salary": {
                "amount": money(salary_income),
                "available": salary_available,
            },
            "house_property": {
                "amount": money(house_property_income),
                "available": house_property_available,
            },
            "business_or_profession": {
                "amount": money(business_income),
                "available": business_available,
                "verified_receipts": money(business_summary["verified_receipts"]),
                "verified_expenses": money(business_summary["verified_expenses"]),
                "net_profit_before_tax_rules": money(business_summary["net_profit_before_tax_rules"]),
                "verified_record_count": business_summary["verified_record_count"],
                "note": "Only verified business records are included. Loss set-off and presumptive taxation require separate validated schedules.",
            },
            "other_sources": {
                "income": money(other_income["income"]),
                "interest": money(other_income["interest"]),
                "dividend": money(other_income["dividend"]),
                "total": money(other_income["other_sources_total"]),
            },
            "money_transaction_details": other_income["details"],
            "excluded_loan_proceeds": other_income["excluded_loan_proceeds"],
            "classification_review": other_income["classification_review"],
            "receivable_review": other_income["receivable_review"],
        },

        "capital_gains": {
            "stcg_before_setoff": money(
                stcg_before_setoff
            ),
            "ltcg_before_setoff": money(
                ltcg_before_setoff
            ),
            "stcl_setoff_against_stcg": money(
                stcg_setoff
            ),
            "stcl_setoff_against_ltcg": money(
                stcl_against_ltcg
            ),
            "ltcl_setoff_against_ltcg": money(
                ltcl_against_ltcg
            ),
            "stcg_after_setoff": money(
                remaining_stcg
            ),
            "ltcg_after_setoff": money(
                remaining_ltcg
            ),
            "unclassified_gain": money(
                capital_gains["unclassified_gain"]
            ),
            "sales_count": len(
                capital_gains["sales"]
            ),
            "sales": capital_gains["sales"],
        },

        "deductions": {
            "regime": regime.lower(),
            "verified_amount": money(verified_deductions),
            "data_available": True,
            "status": "verified_claims_and_automatic_standard_deduction_applied",
            "automatic_adjustment": True,
            "items": deduction_details,
            "reason": "Only verified claims are applied. Salary standard deduction is applied automatically when transaction-backed gross salary is available. Ordinary expenses are not inferred as deductions.",
        },

        "exempt_income": {
            "verified_amount": money(verified_exempt_income),
            "data_available": bool(exempt_claim_details),
            "status": "verified_hra_applied_where_supported_other_claims_disclosed",
            "items": exempt_claim_details,
        },

        "taxable_income": {
            "normal_income": money(normal_income),
            "capital_gain_income": money(
                capital_gain_income
            ),
            "gross_provisional_income": money(
                gross_provisional_income
            ),
            "deductions": money(
                verified_deductions
            ),
            "exempt_income": money(
                verified_exempt_income
            ),
            "provisional_taxable_income": money(
                provisional_taxable_income
            ),
            "normal_taxable_income_for_slab_tax": money(
                normal_taxable_income
            ),
        },

        "tax_liability": {
            "normal_slab_tax": money(
                normal_tax
            ),
            "stcg_111a_tax": money(
                stcg_tax
            ),
            "ltcg_112a_tax": money(
                ltcg_tax
            ),
            "special_rate_tax": money(
                special_rate_tax
            ),
            "rebate_87a": money(
                rebate_87a
            ),
            "surcharge": money(surcharge),
            "surcharge_details": {
                "rate": str(surcharge_calculation.get("rate", 0)),
                "normal_income_surcharge": money(surcharge_calculation.get("normal_income_surcharge", 0)),
                "special_rate_surcharge": money(surcharge_calculation.get("special_rate_surcharge", 0)),
                "marginal_relief": money(surcharge_calculation.get("marginal_relief", 0)),
                "marginal_relief_threshold": surcharge_calculation.get("marginal_relief_threshold"),
                "marginal_relief_review_required": bool(surcharge_calculation.get("marginal_relief_review_required", False)),
            },
            "cess": money(cess),
            "total_tax_payable": money(
                total_tax_payable
            ),
        },

        "tax_credits": {
            "tds": money(verified_credits["tds"]),
            "tcs": money(verified_credits["tcs"]),
            "advance_tax": money(verified_credits["advance_tax"]),
            "self_assessment_tax": money(verified_credits["self_assessment_tax"]),
            "verified_total": money(total_verified_credits),
            "pending_review": {key: money(value) for key, value in pending_credits.items()},
            "entries": credit_details,
            "data_available": bool(credit_rows),
            "balance_payable_or_refund": money(balance_after_verified_credits),
            "status": "verified_credits_applied_pending_credits_disclosed" if credit_rows else "no_tax_credit_entries",
        },

        "deduction_rules": {
            "financial_year": financial_year,
            "regime": regime.lower(),
            "catalogue_endpoint": "/api/deductions-exempt-income/",
            "claims_auto_applied": False,
            "reason": "No verified deduction claim ledger exists yet; regime catalogue is informational until claim evidence and year-specific calculation are connected.",
        },

        "report_status": report_status,

        "missing_data": {
            "required_sections": missing_required_sections,
            "income_heads": missing_income_heads,
            "deductions": True,
            "tax_credits_tds_advance_tax": True,
            "loan_interest_eligibility_and_evidence": True,
            "residential_status": True,
            "personal_and_filing_details": True,
            "salary": not salary_available,
            "house_property": not house_property_available,
            "business_or_profession": not business_available,
        },

        "itr_forms": {
            "ITR-1": {"status": "eligibility_not_confirmed", "note": "Generally for eligible resident individuals with limited income sources; capital gains or other disqualifying conditions may make this form unavailable."},
            "ITR-2": {"status": "possible_if_no_business_income", "note": "May apply where ITR-1 is not available and there is no business/professional income; verify all statutory conditions."},
            "ITR-3": {"status": "requires_business_income_details", "note": "Generally relevant when business/professional income is present."},
            "actual_e_filing": "not_supported_by_this_report_endpoint",
        },
        "filing_readiness": {
            "itr_filed": False,
            "database_write": False,
            "report_complete": report_complete,
            "ready_for_final_review": report_complete,
            "ready_to_file": False,
        },

        "next_step": (
            "Review missing income heads and verify "
            "deductions/exempt income before actual ITR filing."
        ),
    }

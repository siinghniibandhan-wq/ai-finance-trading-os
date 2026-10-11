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

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.database import get_db


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


def money(value) -> float:
    return float(
        decimal(value).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
    )


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
            COALESCE(c.description, '') AS category_description
        FROM transactions AS t
        LEFT JOIN categories AS c
          ON c.id = t.category_id AND c.user_id = t.user_id
        WHERE t.user_id = :user_id
          AND t.transaction_date >= :start_date
          AND t.transaction_date <= :end_date
          AND LOWER(COALESCE(t.transaction_type, '')) IN (
              'income', 'interest', 'dividend'
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

        # Loan proceeds are not income, even when entered through Money > Income.
        if category_looks_like_borrowing or any(term in searchable for term in loan_terms):
            excluded_loan_proceeds.append({**original, "reason": "Likely loan/borrowing proceeds; excluded from taxable income and flagged for review."})
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

        totals[selected_head] += amount
        details.append({**original, "tax_head": selected_head, "classification_source": "keyword/category" if detected else "transaction_type"})

    return {
        **totals,
        "total": totals["salary"] + totals["income"] + totals["interest"] + totals["dividend"],
        "other_sources_total": totals["income"] + totals["interest"] + totals["dividend"],
        "details": details,
        "excluded_loan_proceeds": excluded_loan_proceeds,
        "classification_review": classification_review,
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

@router.get("/")
def get_itr_ready_tax_report(
    user_id: int = Query(1),
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

    other_income = load_other_income(
        db,
        user_id,
        start_date,
        end_date,
    )

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

    # Existing Module 10 confirms that there are currently
    # no verified deduction claims or exempt-income claims.
    verified_deductions = Decimal("0")
    verified_exempt_income = Decimal("0")

    # --------------------------------------------------------
    # 5. INCOME HEAD AVAILABILITY
    # --------------------------------------------------------

    salary_available = other_income["salary"] > 0
    house_property_available = False
    business_available = False

    salary_income = other_income["salary"]
    house_property_income = Decimal("0")
    business_income = Decimal("0")

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

    # Deductions/exemptions currently come only from verified claims.
    # Keep them against normal-rate income in this provisional engine;
    # do not silently reduce special-rate capital gains with general deductions.
    taxable_normal_income = max(
        normal_income
        - verified_deductions
        - verified_exempt_income,
        Decimal("0"),
    )

    provisional_taxable_income = (
        taxable_normal_income
        + max(capital_gain_income, Decimal("0"))
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

    if regime.lower() == "old":
        normal_tax = calculate_old_regime_slab_tax(
            taxable_normal_income
        )

        rebate_limit = OLD_REGIME_REBATE_LIMIT
        rebate_max = OLD_REGIME_REBATE_MAX

    else:
        normal_tax = calculate_new_regime_slab_tax(
            taxable_normal_income
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

    # Current taxpayer data is far below surcharge thresholds.
    # Keep surcharge zero unless taxable income crosses the
    # applicable thresholds in a future data set.
    surcharge = Decimal("0")

    tax_after_surcharge = (
        tax_before_surcharge
        + surcharge
    )

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
            "verified_amount": money(
                verified_deductions
            ),
            "data_available": False,
            "status": (
                "catalogue_available_claim_ledger_missing"
            ),
            "automatic_adjustment": False,
            "reason": "Eligible claim amounts and evidence are not stored in a verified claims ledger; do not infer them from ordinary expenses.",
        },

        "exempt_income": {
            "verified_amount": money(
                verified_exempt_income
            ),
            "data_available": False,
            "status": (
                "framework_ready_no_verified_claims"
            ),
        },

        "taxable_income": {
            "normal_income": money(normal_income),
            "taxable_normal_income_after_verified_deductions": money(
                taxable_normal_income
            ),
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
            "surcharge": money(
                surcharge
            ),
            "cess": money(cess),
            "total_tax_payable": money(
                total_tax_payable
            ),
        },

        "tax_credits": {
            "tds": None,
            "advance_tax": None,
            "self_assessment_tax": None,
            "data_available": False,
            "balance_payable_or_refund": None,
            "status": "tax_credit_data_not_connected",
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

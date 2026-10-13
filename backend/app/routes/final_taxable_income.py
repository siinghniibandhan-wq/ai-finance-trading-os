# ============================================================
# FINANCIAL OS
# FINAL TAXABLE INCOME ENGINE
# ============================================================
#
# Version: 1.0
#
# Purpose:
#   Build the final taxable-income framework for a Tax Year.
#
# IMPORTANT:
#   This engine is READ-ONLY.
#
#   It does NOT:
#   - modify transactions
#   - modify investments
#   - modify holdings
#   - modify tax data
#   - create deduction records
#   - calculate final tax liability
#
# Current scope:
#   1. Other-source income
#   2. Capital gains
#   3. Capital-loss set-off
#   4. Verified deductions
#   5. Verified exempt income
#   6. Provisional taxable income
#
# Missing income heads remain explicitly unavailable.
#
# Next engine:
#   Final Tax Liability Engine
#
# ============================================================


from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from sqlalchemy import func

from app.database.database import get_db
from app.routes.ownership import require_matching_user_id
from app.models import Transaction, Category, LoanMovement, TaxDeductionClaim, TaxSalaryIncomeRecord, TaxBusinessIncomeRecord, User
from app.routes.auth import get_current_user
from app.routes.deductions_exempt_income import (
    DEDUCTION_CATALOG, EXEMPT_INCOME_CATALOG, HRAInputs, calculate_hra_exemption, regime_available,
)

# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/final-taxable-income",
    tags=["Final Taxable Income"],
)


# ============================================================
# ENGINE VERSION
# ============================================================

ENGINE_VERSION = "1.0"


# ============================================================
# CONSTANTS
# ============================================================

INCOME_TRANSACTION_TYPES = {
    "income",
    "interest",
    "dividend",
}


# ============================================================
# MONEY HELPER
# ============================================================

def money(value):
    """
    Convert a value into a monetary Decimal rounded
    to two decimal places.
    """

    if value is None:
        value = 0

    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


# ============================================================
# DECIMAL HELPER
# ============================================================

def decimal(value):
    """
    Safely convert a database value to Decimal.
    """

    if value is None:
        return Decimal("0")

    return Decimal(str(value))


def load_salary_income_from_transactions(db, user_id, start_date, end_date):
    """
    Transaction ledger is the source of truth for transaction-linked salary.
    A standalone verified annual salary snapshot must not create salary income
    when no salary-category transaction exists.
    Salary component details are stored in the transaction description.
    """
    import re

    rows = db.execute(
        text("""
            SELECT t.id, t.transaction_date, t.description
            FROM transactions AS t
            LEFT JOIN categories AS c ON c.id = t.category_id
            WHERE t.user_id = :user_id
              AND LOWER(TRIM(COALESCE(t.transaction_type, ''))) = 'income'
              AND t.transaction_date >= :start_date
              AND t.transaction_date <= :end_date
              AND (
                    LOWER(TRIM(COALESCE(c.name, ''))) IN ('salary', 'salary & wages', 'salaries')
                    OR LOWER(COALESCE(t.description, '')) LIKE '%gross salary:%'
                  )
            ORDER BY t.transaction_date ASC, t.id ASC
        """),
        {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    ).fetchall()

    total = Decimal("0")
    found = False
    for row in rows:
        description = row.description or ""
        match = re.search(
            r"Gross\s+salary\s*:\s*(?:₹|INR)?\s*([0-9,]+(?:\.[0-9]{1,2})?)",
            description,
            re.IGNORECASE,
        )
        if not match:
            continue
        total += Decimal(match.group(1).replace(",", ""))
        found = True

    return total if found else None


# ============================================================
# FINANCIAL YEAR
# ============================================================

def get_financial_year_dates(financial_year):
    """
    Convert:

        2026-27

    into:

        2026-04-01
        2027-03-31
    """

    try:
        start_year = int(
            financial_year.split("-")[0]
        )
    except Exception:
        raise ValueError(
            "financial_year must use format YYYY-YY, "
            "for example 2026-27."
        )

    return (
        date(
            start_year,
            4,
            1,
        ),
        date(
            start_year + 1,
            3,
            31,
        ),
    )


# ============================================================
# ASSET CLASS RESOLVER
# ============================================================

def resolve_asset_class(investment_type):
    """
    Resolve the existing investment_type into a tax
    asset class.

    Unknown values remain unclassified.
    """

    if investment_type is None:
        return "unclassified"

    value = str(
        investment_type
    ).strip().lower()

    mapping = {

        # Listed equity
        "stock": "listed_equity",
        "stocks": "listed_equity",
        "equity": "listed_equity",
        "share": "listed_equity",
        "shares": "listed_equity",
        "listed equity": "listed_equity",
        "listed stock": "listed_equity",
        "listed shares": "listed_equity",

        # Equity mutual funds
        "equity mutual fund": "equity_oriented_mf",
        "equity mutual funds": "equity_oriented_mf",
        "equity mf": "equity_oriented_mf",
        "equity-oriented mutual fund":
            "equity_oriented_mf",
        "equity-oriented mutual funds":
            "equity_oriented_mf",

        # Unlisted equity
        "unlisted equity": "unlisted_equity",
        "unlisted stock": "unlisted_equity",
        "unlisted shares": "unlisted_equity",

        # Listed other securities
        "listed security":
            "listed_other_security",
        "listed securities":
            "listed_other_security",
        "bond":
            "listed_other_security",
        "bonds":
            "listed_other_security",

        # Unlisted other securities
        "unlisted security":
            "unlisted_other_security",
        "unlisted securities":
            "unlisted_other_security",
    }

    return mapping.get(
        value,
        "unclassified",
    )


# ============================================================
# HOLDING PERIOD CLASSIFICATION
# ============================================================

def classify_gain(
    holding_days,
    asset_class,
):
    """
    Classify capital gains using the same thresholds
    already established in the Financial OS tax engines.

    Listed equity / equity-oriented MF:
        365 days

    Unlisted equity:
        730 days

    Listed other security:
        365 days

    Unlisted other security:
        730 days
    """

    if asset_class in {
        "listed_equity",
        "equity_oriented_mf",
        "listed_other_security",
    }:
        threshold = 365

    elif asset_class in {
        "unlisted_equity",
        "unlisted_other_security",
    }:
        threshold = 730

    else:
        return {
            "classification": "UNCLASSIFIED",
            "threshold_days": None,
        }

    if holding_days >= threshold:
        classification = "LTCG"
    else:
        classification = "STCG"

    return {
        "classification": classification,
        "threshold_days": threshold,
    }


# ============================================================
# LOAD INVESTMENTS
# ============================================================

def load_investments(
    db,
    user_id,
):
    """
    Load investments from the existing investments table.
    """

    result = db.execute(
        text(
            """
            SELECT
                id,
                user_id,
                name,
                investment_type,
                symbol,
                quantity,
                buy_price,
                current_price,
                buy_date,
                broker,
                fees,
                notes
            FROM investments
            WHERE user_id = :user_id
            ORDER BY id ASC
            """
        ),
        {
            "user_id": user_id,
        },
    )

    return [
        type(
            "InvestmentRecord",
            (),
            dict(row._mapping),
        )()
        for row in result
    ]


# ============================================================
# LOAD INVESTMENT TRANSACTIONS
# ============================================================

def load_investment_transactions(
    db,
    user_id,
):
    """
    Load all BUY/SELL investment transactions
    from the existing investment_transactions table.
    """

    result = db.execute(
        text(
            """
            SELECT
                id,
                user_id,
                investment_id,
                transaction_type,
                quantity,
                price,
                fees,
                transaction_date,
                notes
            FROM investment_transactions
            WHERE user_id = :user_id
            ORDER BY transaction_date ASC, id ASC
            """
        ),
        {
            "user_id": user_id,
        },
    )

    return [
        type(
            "InvestmentTransactionRecord",
            (),
            dict(row._mapping),
        )()
        for row in result
    ]


# ============================================================
# CAPITAL GAINS ENGINE
# ============================================================

def calculate_capital_gains(
    db,
    user_id,
    start_date,
    end_date,
):
    """
    Calculate current-year realised capital gains using
    FIFO.

    Only SELL transactions inside the requested Tax Year
    are treated as current-year realised gains.

    BUY transactions before the Tax Year are retained so
    that FIFO can correctly match current-year sales.
    """

    investments = load_investments(
        db,
        user_id,
    )

    investment_transactions = (
        load_investment_transactions(
            db,
            user_id,
        )
    )

    investment_map = {
        investment.id: investment
        for investment in investments
    }

    lots = {}

    sales = []

    # --------------------------------------------------------
    # BUILD FIFO LOTS
    # --------------------------------------------------------

    for transaction in investment_transactions:

        investment_id = (
            transaction.investment_id
        )

        if investment_id not in investment_map:
            continue

        transaction_type = str(
            transaction.transaction_type
        ).upper()

        quantity = decimal(
            transaction.quantity
        )

        price = decimal(
            transaction.price
        )

        fees = decimal(
            transaction.fees
        )

        transaction_date = (
            transaction.transaction_date
        )

        if transaction_type == "BUY":

            gross_value = (
                quantity * price
            )

            lots.setdefault(
                investment_id,
                [],
            ).append(
                {
                    "buy_transaction_id":
                        transaction.id,
                    "buy_date":
                        transaction_date,
                    "quantity_remaining":
                        quantity,
                    "unit_price":
                        price,
                    "gross_buy_value":
                        gross_value,
                    "total_buy_fee":
                        fees,
                }
            )

        elif transaction_type == "SELL":

            # ------------------------------------------------
            # Ignore sales outside current Tax Year.
            # ------------------------------------------------

            if (
                transaction_date is None
                or transaction_date < start_date
                or transaction_date > end_date
            ):
                continue

            remaining_quantity = quantity

            sale_proceeds = (
                quantity * price
            )

            sale_fee = fees

            matched_cost = Decimal("0")

            matched_buy_fees = Decimal("0")

            matched_quantity = Decimal("0")

            matched_lots = []

            holding_days_weighted = (
                Decimal("0")
            )

            investment = investment_map[
                investment_id
            ]

            asset_class = resolve_asset_class(
                investment.investment_type
            )

            # ----------------------------------------------
            # FIFO CONSUMPTION
            # ----------------------------------------------

            while (
                remaining_quantity > 0
                and lots.get(
                    investment_id,
                    [],
                )
            ):

                lot = lots[
                    investment_id
                ][0]

                available_quantity = decimal(
                    lot[
                        "quantity_remaining"
                    ]
                )

                consumed_quantity = min(
                    remaining_quantity,
                    available_quantity,
                )

                if consumed_quantity <= 0:
                    break

                buy_date = lot[
                    "buy_date"
                ]

                holding_days = None

                if (
                    buy_date is not None
                    and transaction_date is not None
                ):
                    holding_days = (
                        transaction_date
                        - buy_date
                    ).days

                # ------------------------------------------
                # COST
                # ------------------------------------------

                lot_unit_price = decimal(
                    lot["unit_price"]
                )

                lot_cost = (
                    consumed_quantity
                    * lot_unit_price
                )

                matched_cost += lot_cost

                # ------------------------------------------
                # BUY FEE ALLOCATION
                # ------------------------------------------

                lot_original_quantity = (
                    decimal(
                        lot["quantity_remaining"]
                    )
                    + consumed_quantity
                )

                if (
                    lot_original_quantity > 0
                    and lot["total_buy_fee"]
                ):
                    allocated_buy_fee = (
                        decimal(
                            lot[
                                "total_buy_fee"
                            ]
                        )
                        * consumed_quantity
                        / lot_original_quantity
                    )
                else:
                    allocated_buy_fee = (
                        Decimal("0")
                    )

                matched_buy_fees += (
                    allocated_buy_fee
                )

                # ------------------------------------------
                # HOLDING PERIOD
                # ------------------------------------------

                if holding_days is not None:
                    holding_days_weighted += (
                        Decimal(
                            holding_days
                        )
                        * consumed_quantity
                    )

                matched_quantity += (
                    consumed_quantity
                )

                matched_lots.append(
                    {
                        "buy_transaction_id":
                            lot[
                                "buy_transaction_id"
                            ],
                        "buy_date":
                            buy_date,
                        "quantity":
                            consumed_quantity,
                        "buy_price":
                            lot_unit_price,
                        "holding_days":
                            holding_days,
                    }
                )

                # ------------------------------------------
                # REDUCE LOT
                # ------------------------------------------

                lot[
                    "quantity_remaining"
                ] = (
                    available_quantity
                    - consumed_quantity
                )

                remaining_quantity -= (
                    consumed_quantity
                )

                if (
                    lot[
                        "quantity_remaining"
                    ] <= 0
                ):
                    lots[
                        investment_id
                    ].pop(0)

            # ------------------------------------------------
            # UNMATCHED QUANTITY
            # ------------------------------------------------

            unmatched_quantity = (
                remaining_quantity
            )

            # ------------------------------------------------
            # ALLOCATE SALE FEE
            # ------------------------------------------------

            if quantity > 0:
                allocated_sale_fee = (
                    sale_fee
                )
            else:
                allocated_sale_fee = (
                    Decimal("0")
                )

            # ------------------------------------------------
            # REALISED GAIN
            # ------------------------------------------------

            realised_gain = (
                sale_proceeds
                - allocated_sale_fee
                - matched_cost
                - matched_buy_fees
            )

            # ------------------------------------------------
            # WEIGHTED HOLDING PERIOD
            # ------------------------------------------------

            if matched_quantity > 0:
                weighted_holding_days = (
                    holding_days_weighted
                    / matched_quantity
                )
            else:
                weighted_holding_days = None

            classification_result = (
                classify_gain(
                    int(
                        weighted_holding_days
                    )
                    if weighted_holding_days
                    is not None
                    else 0,
                    asset_class,
                )
            )

            sales.append(
                {
                    "sale_transaction_id":
                        transaction.id,
                    "investment_id":
                        investment_id,
                    "investment_name":
                        investment.name,
                    "investment_type":
                        investment.investment_type,
                    "symbol":
                        investment.symbol,
                    "asset_class":
                        asset_class,
                    "sale_date":
                        transaction_date,
                    "quantity":
                        quantity,
                    "sale_price":
                        price,
                    "sale_proceeds":
                        money(
                            sale_proceeds
                        ),
                    "sale_fees":
                        money(
                            allocated_sale_fee
                        ),
                    "matched_quantity":
                        matched_quantity,
                    "unmatched_quantity":
                        unmatched_quantity,
                    "cost_basis":
                        money(
                            matched_cost
                            + matched_buy_fees
                        ),
                    "realised_gain_loss":
                        money(
                            realised_gain
                        ),
                    "holding_days":
                        (
                            int(
                                weighted_holding_days
                            )
                            if weighted_holding_days
                            is not None
                            else None
                        ),
                    "classification":
                        classification_result[
                            "classification"
                        ],
                    "threshold_days":
                        classification_result[
                            "threshold_days"
                        ],
                    "matched_lots":
                        matched_lots,
                }
            )

    return sales


# ============================================================
# CAPITAL GAIN TOTALS
# ============================================================

def calculate_capital_gain_totals(
    sales,
):
    """
    Aggregate capital gains and losses by
    STCG / LTCG / STCL / LTCL.
    """

    stcg = Decimal("0")
    ltcg = Decimal("0")
    stcl = Decimal("0")
    ltcl = Decimal("0")
    unclassified = Decimal("0")

    for sale in sales:

        gain = decimal(
            sale[
                "realised_gain_loss"
            ]
        )

        classification = sale[
            "classification"
        ]

        if classification == "STCG":

            if gain >= 0:
                stcg += gain
            else:
                stcl += abs(gain)

        elif classification == "LTCG":

            if gain >= 0:
                ltcg += gain
            else:
                ltcl += abs(gain)

        else:

            unclassified += gain

    return {
        "stcg": money(stcg),
        "ltcg": money(ltcg),
        "stcl": money(stcl),
        "ltcl": money(ltcl),
        "unclassified": money(
            unclassified
        ),
    }


# ============================================================
# LOSS SET-OFF
# ============================================================

def apply_loss_setoff(
    stcg,
    ltcg,
    stcl,
    ltcl,
):
    """
    Apply current-year capital losses using the same
    rules already established by the Financial OS.

    STCL:
        first against STCG
        then remaining STCL against LTCG

    LTCL:
        against LTCG only
    """

    stcg = decimal(stcg)
    ltcg = decimal(ltcg)
    stcl = decimal(stcl)
    ltcl = decimal(ltcl)

    # --------------------------------------------------------
    # STCL AGAINST STCG
    # --------------------------------------------------------

    stcl_against_stcg = min(
        stcl,
        stcg,
    )

    remaining_stcl = (
        stcl
        - stcl_against_stcg
    )

    remaining_stcg = (
        stcg
        - stcl_against_stcg
    )

    # --------------------------------------------------------
    # STCL AGAINST LTCG
    # --------------------------------------------------------

    stcl_against_ltcg = min(
        remaining_stcl,
        ltcg,
    )

    remaining_stcl = (
        remaining_stcl
        - stcl_against_ltcg
    )

    remaining_ltcg = (
        ltcg
        - stcl_against_ltcg
    )

    # --------------------------------------------------------
    # LTCL AGAINST LTCG
    # --------------------------------------------------------

    ltcl_against_ltcg = min(
        ltcl,
        remaining_ltcg,
    )

    remaining_ltcl = (
        ltcl
        - ltcl_against_ltcg
    )

    remaining_ltcg = (
        remaining_ltcg
        - ltcl_against_ltcg
    )

    return {
        "stcl_against_stcg":
            money(
                stcl_against_stcg
            ),
        "stcl_against_ltcg":
            money(
                stcl_against_ltcg
            ),
        "ltcl_against_ltcg":
            money(
                ltcl_against_ltcg
            ),
        "remaining_stcg":
            money(
                remaining_stcg
            ),
        "remaining_ltcg":
            money(
                remaining_ltcg
            ),
        "unabsorbed_stcl":
            money(
                remaining_stcl
            ),
        "unabsorbed_ltcl":
            money(
                remaining_ltcl
            ),
    }


# ============================================================
# LOAD OTHER-SOURCE INCOME
# ============================================================

def load_other_source_income(
    db,
    user_id,
    start_date,
    end_date,
    excluded_transaction_ids=None,
):
    """
    Load explicitly classified other-source income while excluding
    loan principal from taxable-income estimates.

    Loan Disbursement category rows are borrowing proceeds, not earned
    income. For a linked loan recovery, only the amount above recovered
    principal is counted here; interest and fees remain visible for
    review rather than treating the full recovery as income.
    """

    excluded_transaction_ids = set(excluded_transaction_ids or [])
    rows = (
        db.query(Transaction, LoanMovement)
        .outerjoin(
            LoanMovement,
            LoanMovement.transaction_id == Transaction.id,
        )
        .outerjoin(
            Category,
            Category.id == Transaction.category_id,
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type.in_(INCOME_TRANSACTION_TYPES),
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
            *([Transaction.id.notin_(excluded_transaction_ids)] if excluded_transaction_ids else []),
            # Borrowed money is not income. Salary-category transactions are
            # handled exclusively by load_salary_income_from_transactions(),
            # which reads gross salary from the saved salary details. Excluding
            # them here prevents the net bank receipt being counted as a second
            # taxable income amount.
            (Category.id.is_(None))
            | (
                func.lower(func.trim(func.coalesce(Category.name, ""))).notin_(
                    ("loan disbursement", "salary", "salary & wages", "salaries")
                )
            ),
            # Salary component metadata marks a salary receipt even if the
            # user selected a differently named Income category. It is loaded
            # once as gross salary by load_salary_income_from_transactions.
            ~func.lower(func.coalesce(Transaction.description, "")).like("%gross salary:%"),
        )
        .all()
    )

    income = Decimal("0")
    interest = Decimal("0")
    dividend = Decimal("0")
    included_transaction_count = 0

    for row, movement in rows:
        amount = decimal(row.amount)
        transaction_type = str(row.transaction_type or "").lower()

        # A loan recovery transaction contains principal + interest + fees.
        # Remove only the principal portion from ordinary income totals.
        if movement is not None and movement.movement_type == "recovery":
            amount = max(Decimal("0"), amount - decimal(movement.principal_amount))

        if amount <= 0:
            continue

        included_transaction_count += 1

        if transaction_type == "income":
            income += amount
        elif transaction_type == "interest":
            interest += amount
        elif transaction_type == "dividend":
            dividend += amount

    return {
        "income": money(income),
        "interest": money(interest),
        "dividend": money(dividend),
        "total": money(income + interest + dividend),
        "transaction_count": included_transaction_count,
    }


def aggregate_verified_exempt_claims(claims, tax_regime):
    """Aggregate only verified, known, regime-eligible exemption claims.

    Amounts are user-confirmed claims, not independently validated tax advice.
    """
    by_key = {}
    for claim in claims:
        item = EXEMPT_INCOME_CATALOG.get(claim.deduction_key)
        if not item or not regime_available(item, tax_regime):
            continue
        by_key[claim.deduction_key] = (
            by_key.get(claim.deduction_key, Decimal("0"))
            + decimal(claim.claimed_amount)
        )

    details = []
    for key, amount in by_key.items():
        item = EXEMPT_INCOME_CATALOG[key]
        details.append({
            "deduction_key": key,
            "section": item.get("section"),
            "verified_claimed_amount": str(amount),
            "applied_amount": str(amount),
            "user_confirmed_not_independently_validated": True,
            "calculation_note": (
                "HRA claims should be created through the HRA calculator; the app does not independently verify supporting documents or legal eligibility."
                if key == "hra_exemption" else
                "Exempt amount is user-confirmed and evidence-referenced; confirm eligibility under the applicable law before filing."
            ),
        })
    return sum(by_key.values(), Decimal("0")), details


# ============================================================
# SALARY INCOME SOURCE — CREATE / UPDATE / VERIFY
# ============================================================

class TaxSalaryIncomeInput(BaseModel):
    financial_year: str = Field(pattern=r"^\d{4}-\d{2}$")
    gross_salary: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    annual_basic_salary: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    annual_da_forming_retirement_benefits: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)
    annual_commission_on_turnover_at_fixed_percentage: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)
    annual_hra_received: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    annual_rent_paid: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    accommodation_owned_by_taxpayer: bool = False
    rent_actually_paid: bool = False
    city: str = Field(min_length=2, max_length=100)
    evidence_reference: str | None = Field(default=None, max_length=2000)


def calculate_salary_record_hra_exemption(record, financial_year: str):
    """Calculate HRA from the verified salary record, including explicit eligibility confirmations."""
    hra_inputs = HRAInputs(
        annual_basic_salary=record.annual_basic_salary,
        annual_da_forming_retirement_benefits=record.annual_da_forming_retirement_benefits,
        annual_commission_on_turnover_at_fixed_percentage=record.annual_commission_on_turnover_at_fixed_percentage,
        annual_hra_received=record.annual_hra_received,
        annual_rent_paid=record.annual_rent_paid,
        accommodation_owned_by_taxpayer=bool(record.accommodation_owned_by_taxpayer),
        rent_actually_paid=bool(record.rent_actually_paid),
        city=record.city,
    )
    return calculate_hra_exemption(hra_inputs, "old", financial_year)


def _salary_record_summary(record):
    return {
        "id": record.id,
        "user_id": record.user_id,
        "financial_year": record.financial_year,
        "gross_salary": str(record.gross_salary),
        "annual_basic_salary": str(record.annual_basic_salary),
        "annual_da_forming_retirement_benefits": str(record.annual_da_forming_retirement_benefits),
        "annual_commission_on_turnover_at_fixed_percentage": str(record.annual_commission_on_turnover_at_fixed_percentage),
        "annual_hra_received": str(record.annual_hra_received),
        "annual_rent_paid": str(record.annual_rent_paid),
        "accommodation_owned_by_taxpayer": bool(record.accommodation_owned_by_taxpayer),
        "rent_actually_paid": bool(record.rent_actually_paid),
        "city": record.city,
        "evidence_reference": record.evidence_reference,
        "status": record.status,
        "affects_taxable_income": record.status == "verified",
        "verification_notice": "Verification is the user's confirmation that the figures reconcile to supporting records; the app does not independently inspect documents.",
    }


@router.put("/salary-income", status_code=200)
def upsert_tax_salary_income(payload: TaxSalaryIncomeInput, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create/update annual gross salary separately from bank deposits; starts pending."""
    eligible_salary = payload.annual_basic_salary + payload.annual_da_forming_retirement_benefits + payload.annual_commission_on_turnover_at_fixed_percentage
    if eligible_salary <= 0 and payload.annual_hra_received > 0:
        raise HTTPException(status_code=400, detail="Eligible basic salary/DA/commission must be positive when recording HRA.")
    if eligible_salary > payload.gross_salary:
        raise HTTPException(status_code=400, detail="Eligible basic salary, DA and commission cannot exceed recorded gross salary.")
    if payload.annual_hra_received > payload.gross_salary:
        raise HTTPException(status_code=400, detail="HRA received cannot exceed recorded gross salary.")
    if payload.annual_rent_paid > 0 and payload.accommodation_owned_by_taxpayer:
        raise HTTPException(status_code=400, detail="HRA cannot be claimed for accommodation you own. Confirm eligible rented accommodation and actual rent paid.")
    if payload.annual_rent_paid > 0 and not payload.rent_actually_paid:
        raise HTTPException(status_code=400, detail="Confirm that rent was actually paid before recording HRA rent details.")
    record = db.query(TaxSalaryIncomeRecord).filter_by(user_id=current_user.id, financial_year=payload.financial_year).first()
    if record is None:
        record = TaxSalaryIncomeRecord(user_id=current_user.id, financial_year=payload.financial_year)
        db.add(record)
    for field, value in payload.model_dump().items():
        setattr(record, field, value)
    record.status = "pending_review"
    db.commit()
    db.refresh(record)
    result = _salary_record_summary(record)
    result["message"] = "Salary record saved as pending. It will not affect taxable income until you confirm it with an evidence reference."
    return result


@router.get("/salary-income")
def get_tax_salary_income(financial_year: str = Query("2026-27", pattern=r"^\d{4}-\d{2}$"), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.query(TaxSalaryIncomeRecord).filter_by(user_id=current_user.id, financial_year=financial_year).first()
    if record is None:
        return {"status": "missing", "financial_year": financial_year, "salary_income_available": False}
    return _salary_record_summary(record)


@router.post("/salary-income/verify")
def verify_tax_salary_income(financial_year: str = Query(..., pattern=r"^\d{4}-\d{2}$"), evidence_reference: str = Query(..., min_length=1, max_length=2000), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """User-confirm verification after reconciling the annual salary statement/Form 16."""
    record = db.query(TaxSalaryIncomeRecord).filter_by(user_id=current_user.id, financial_year=financial_year).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Salary income record not found for this financial year.")
    evidence = evidence_reference.strip()
    if not evidence:
        raise HTTPException(status_code=400, detail="An evidence reference is required.")
    record.evidence_reference = evidence
    record.status = "verified"
    db.commit()
    db.refresh(record)
    return _salary_record_summary(record)


# ============================================================
# ENDPOINT
# ============================================================

@router.get("/", dependencies=[Depends(require_matching_user_id)])
def get_final_taxable_income(
    user_id: int = Query(
        ...,
        ge=1,
    ),
    financial_year: str = Query(
        "2026-27"
    ),
    tax_regime: str = Query(
        "new"
    ),
    db: Session = Depends(get_db),
):
    """
    Build the final taxable-income framework.

    Example:

    /api/final-taxable-income/
    ?user_id=1
    &financial_year=2026-27
    &tax_regime=new
    """

    # ========================================================
    # VALIDATE REGIME
    # ========================================================

    tax_regime = str(
        tax_regime
    ).lower()

    if tax_regime not in {
        "new",
        "old",
    }:

        return {
            "status": "error",
            "message": (
                "tax_regime must be 'new' "
                "or 'old'."
            ),
        }

    # ========================================================
    # FINANCIAL YEAR
    # ========================================================

    try:

        start_date, end_date = (
            get_financial_year_dates(
                financial_year
            )
        )

    except ValueError as error:

        return {
            "status": "error",
            "message": str(error),
        }

    # ========================================================
    # VERIFIED BUSINESS / PROFESSIONAL RECEIPTS
    # ========================================================
    # A tax receipt is included only when it is verified and explicitly linked
    # to the user's matching Money transaction. Require matching date and
    # amount so a stale/mismatched link cannot inflate taxable income.
    # Only exclude a Money transaction from Other Sources after its business
    # receipt has passed every eligibility check below. Pending, unlinked, or
    # mismatched records must not suppress otherwise eligible transaction income.
    business_records_for_year = db.query(TaxBusinessIncomeRecord).filter_by(
        user_id=user_id, financial_year=financial_year, record_type="receipt"
    ).all()
    linked_business_transaction_ids = set()
    verified_business_receipts = []
    for record in business_records_for_year:
        if record.status != "verified" or record.source_transaction_id is None:
            continue
        transaction = db.query(Transaction).filter_by(
            id=record.source_transaction_id, user_id=user_id
        ).first()
        if transaction is None:
            continue
        if transaction.transaction_date != record.transaction_date:
            continue
        if decimal(transaction.amount) != decimal(record.amount):
            continue
        if not (start_date <= record.transaction_date <= end_date):
            continue
        verified_business_receipts.append(record)
        linked_business_transaction_ids.add(transaction.id)

    business_profession_income = sum(
        (decimal(record.amount) for record in verified_business_receipts),
        Decimal("0"),
    )

    # ========================================================
    # OTHER SOURCES
    # ========================================================

    other_sources = load_other_source_income(
        db,
        user_id,
        start_date,
        end_date,
        excluded_transaction_ids=linked_business_transaction_ids,
    )

    # ========================================================
    # CAPITAL GAINS
    # ========================================================

    sales = calculate_capital_gains(
        db,
        user_id,
        start_date,
        end_date,
    )

    capital_gain_totals = (
        calculate_capital_gain_totals(
            sales
        )
    )

    # ========================================================
    # CAPITAL LOSS SET-OFF
    # ========================================================

    loss_setoff = apply_loss_setoff(
        capital_gain_totals["stcg"],
        capital_gain_totals["ltcg"],
        capital_gain_totals["stcl"],
        capital_gain_totals["ltcl"],
    )

    # ========================================================
    # VERIFIED DEDUCTIONS
    # ========================================================
    #
    # Module 10 currently reports:
    #
    #   verified deductions = 0
    #
    # because there is no dedicated verified deduction
    # ledger yet.
    #
    # We intentionally DO NOT infer deductions from
    # ordinary transactions.
    #
    # ========================================================

    # Only explicitly verified claims for this user, FY, and regime
    # can reduce taxable income. Pending/rejected claims are excluded.
    verified_claims = (
        db.query(TaxDeductionClaim)
        .filter(
            TaxDeductionClaim.user_id == user_id,
            TaxDeductionClaim.financial_year == financial_year,
            TaxDeductionClaim.tax_regime == tax_regime,
            TaxDeductionClaim.status == "verified",
        )
        .all()
    )

    # Aggregate by deduction key and cap where the catalogue defines
    # a limit. Unknown/unavailable deductions never reduce income.
    verified_by_key = {}
    for claim in verified_claims:
        item = DEDUCTION_CATALOG.get(claim.deduction_key)
        if claim.deduction_key == "STANDARD_DEDUCTION_SALARY":
            # Applied automatically from live gross salary below; never allow
            # a manual claim to duplicate the statutory standard deduction.
            continue
        if not item or not regime_available(item, tax_regime):
            continue
        verified_by_key[claim.deduction_key] = (
            verified_by_key.get(claim.deduction_key, Decimal("0"))
            + decimal(claim.claimed_amount)
        )

    verified_deductions = Decimal("0")
    applied_verified_deductions = []
    for deduction_key, amount in verified_by_key.items():
        item = DEDUCTION_CATALOG[deduction_key]
        regime_limits = item.get("maximum_amount_by_regime", {})
        limit = regime_limits.get(tax_regime, item.get("maximum_amount"))
        applied_amount = min(amount, Decimal(str(limit))) if limit is not None else amount
        verified_deductions += applied_amount
        applied_verified_deductions.append({
            "deduction_key": deduction_key,
            "section": item.get("section"),
            "verified_claimed_amount": str(amount),
            "applied_amount": str(applied_amount),
            "limit_applied": limit is not None,
        })

    # ========================================================
    # VERIFIED EXEMPT INCOME
    # ========================================================
    #
    # Verified exempt claims are surfaced separately. They are not applied
    # to taxable income until the matching income head is available.
    #
    # ========================================================

    verified_exempt_claimed_amount, verified_exempt_claims = aggregate_verified_exempt_claims(
        verified_claims, tax_regime
    )

    # ========================================================
    # SAFE APPLICATION GUARD
    # ========================================================
    # A verified annual salary record is the authoritative tax source for this
    # user/FY. Net salary bank transactions remain cash-flow records and must
    # not be added again as taxable salary. Legacy transaction metadata is only
    # a fallback when no verified annual record exists.
    # Keep the verified record as the only annual-record source for tax
    # computation, but separately inspect the saved record so the response can
    # explain why salary is unavailable instead of implying no record exists.
    salary_record_any_status = db.query(TaxSalaryIncomeRecord).filter_by(
        user_id=user_id, financial_year=financial_year
    ).first()
    salary_record = (
        salary_record_any_status
        if salary_record_any_status is not None
        and salary_record_any_status.status == "verified"
        else None
    )
    salary_income = (
        decimal(salary_record.gross_salary)
        if salary_record is not None
        else load_salary_income_from_transactions(db, user_id, start_date, end_date)
    )
    standard_deduction = Decimal("0")
    if salary_income is not None and salary_income > 0:
        standard_item = DEDUCTION_CATALOG.get("STANDARD_DEDUCTION_SALARY", {})
        standard_limits = standard_item.get("maximum_amount_by_regime", {})
        standard_deduction = min(
            salary_income,
            Decimal(str(standard_limits.get(tax_regime, 0))),
        )
        verified_deductions += standard_deduction
        applied_verified_deductions.append({
            "deduction_key": "STANDARD_DEDUCTION_SALARY",
            "section": standard_item.get("section", "Section 16(ia)"),
            "verified_claimed_amount": str(standard_deduction),
            "applied_amount": str(standard_deduction),
            "limit_applied": True,
            "automatic": True,
        })
    verified_exempt_income = Decimal("0")
    hra_applied = False
    for exempt_claim in verified_exempt_claims:
        claimed = decimal(exempt_claim.get("applied_amount", "0"))
        exempt_claim["eligible_verified_claimed_amount"] = str(claimed)
        if exempt_claim.get("deduction_key") == "hra_exemption" and salary_record and salary_income is not None and tax_regime == "old":
            try:
                allowed_hra = decimal(
                    calculate_salary_record_hra_exemption(
                        salary_record, financial_year
                    )["calculated_exemption"]
                )
            except ValueError as exc:
                allowed_hra = Decimal("0")
                exempt_claim["eligibility_block_reason"] = str(exc)
            applied = min(claimed, allowed_hra)
            exempt_claim["applied_amount"] = str(applied)
            exempt_claim["application_status"] = "applied_to_verified_salary_capped_by_salary_record_calculation" if applied > 0 else "not_applied_salary_record_calculation_zero"
            exempt_claim["salary_record_calculated_limit"] = str(allowed_hra)
            if applied < claimed:
                exempt_claim["calculation_note"] += " Applied amount capped to the HRA exemption recalculated from the verified salary-income record."
            verified_exempt_income += applied
            hra_applied = hra_applied or applied > 0
        else:
            exempt_claim["applied_amount"] = "0"
            exempt_claim["application_status"] = "not_applied_salary_income_source_unavailable" if not salary_record else "not_applied_claim_not_eligible_for_salary_source"
            exempt_claim["calculation_note"] += " This claim was not deducted because a verified matching salary source is required."

    # ========================================================
    # MISSING INCOME HEADS
    # ========================================================
    #
    # These cannot be safely inferred from the current
    # transaction structure.
    #
    # ========================================================

    house_property_income = None

    # ========================================================
    # AVAILABLE GROSS INCOME
    # ========================================================

    available_other_income = (
        decimal(
            other_sources["total"]
        )
    )

    available_stcg = decimal(
        loss_setoff[
            "remaining_stcg"
        ]
    )

    available_ltcg = decimal(
        loss_setoff[
            "remaining_ltcg"
        ]
    )

    available_capital_gains = (
        available_stcg
        + available_ltcg
    )

    available_gross_income = (
        available_other_income
        + available_capital_gains
        + business_profession_income
        + (salary_income if salary_income is not None else Decimal("0"))
    )

    # ========================================================
    # PROVISIONAL TAXABLE INCOME
    # ========================================================

    provisional_taxable_income = (
        available_gross_income
        - verified_deductions
        - verified_exempt_income
    )

    if provisional_taxable_income < 0:
        provisional_taxable_income = (
            Decimal("0")
        )

    # ========================================================
    # COMPLETENESS
    # ========================================================

    missing_income_heads = []

    if salary_income is None:
        missing_income_heads.append(
            "salary"
        )

    if house_property_income is None:
        missing_income_heads.append(
            "house_property"
        )

    if business_profession_income is None:
        missing_income_heads.append(
            "business_or_profession"
        )

    # ========================================================
    # FINAL STATUS
    # ========================================================

    if missing_income_heads:

        taxable_income_status = (
            "not_final"
        )

        engine_status = (
            "incomplete_missing_income_heads"
        )

    elif (
        verified_deductions == 0
        and verified_exempt_income == 0
    ):

        taxable_income_status = (
            "provisional"
        )

        engine_status = (
            "provisional_no_verified_claims"
        )

    else:

        taxable_income_status = (
            "final_framework_ready"
        )

        engine_status = (
            "framework_ready"
        )

    # ========================================================
    # RETURN
    # ========================================================

    return {

        "status": "success",

        "user_id": user_id,

        "engine": {
            "name":
                "Final Taxable Income Engine",
            "version":
                ENGINE_VERSION,
            "read_only":
                True,
        },

        # ----------------------------------------------------
        # TAX YEAR
        # ----------------------------------------------------

        "tax_year": {
            "financial_year":
                financial_year,
            "start_date":
                start_date,
            "end_date":
                end_date,
            "tax_regime":
                tax_regime,
        },

        # ----------------------------------------------------
        # ENGINE STATUS
        # ----------------------------------------------------

        "engine_status":
            engine_status,

        # ----------------------------------------------------
        # INCOME HEADS
        # ----------------------------------------------------

        "income_heads": {

            "salary": {
                "available": salary_income is not None,
                "amount": money(salary_income) if salary_income is not None else None,
                "record_exists": salary_record_any_status is not None,
                "record_status": salary_record_any_status.status if salary_record_any_status is not None else None,
                "source": "Verified annual salary record or eligible salary transaction metadata; net salary receipts are excluded from other-source income",
                "reason": (
                    None if salary_income is not None else
                    f"A salary record exists with status '{salary_record_any_status.status}' and is excluded from taxable income until verified."
                    if salary_record_any_status is not None else
                    "No verified annual salary record or eligible salary transaction with saved gross-salary details exists for this financial year."
                ),
            },

            "house_property": {
                "available":
                    False,
                "amount":
                    None,
                "reason":
                    "No dedicated house-property "
                    "income source is currently available.",
            },

            "business_or_profession": {
                "available": bool(verified_business_receipts),
                "amount": money(business_profession_income) if verified_business_receipts else None,
                "verified_linked_receipt_count": len(verified_business_receipts),
                "linked_receipt_count": len(linked_business_transaction_ids),
                "source": "Verified tax business receipts explicitly linked to matching Money transactions; linked transactions are excluded from Other Sources.",
                "reason": (
                    None if verified_business_receipts else
                    "No verified business/profession receipt with a matching linked Money transaction, date, and amount exists for this financial year. Unlinked, pending, or mismatched records are excluded."
                ),
            },

            "other_sources": {
                "available":
                    True,
                "income":
                    other_sources[
                        "income"
                    ],
                "interest":
                    other_sources[
                        "interest"
                    ],
                "dividend":
                    other_sources[
                        "dividend"
                    ],
                "total":
                    other_sources[
                        "total"
                    ],
            },

            "capital_gains": {

                "available":
                    True,

                "stcg_after_setoff":
                    loss_setoff[
                        "remaining_stcg"
                    ],

                "ltcg_after_setoff":
                    loss_setoff[
                        "remaining_ltcg"
                    ],

                "total_after_setoff":
                    money(
                        available_capital_gains
                    ),
            },
        },

        # ----------------------------------------------------
        # CAPITAL LOSS SET-OFF
        # ----------------------------------------------------

        "capital_loss_setoff": {

            "stcl":
                capital_gain_totals[
                    "stcl"
                ],

            "ltcl":
                capital_gain_totals[
                    "ltcl"
                ],

            "stcl_against_stcg":
                loss_setoff[
                    "stcl_against_stcg"
                ],

            "stcl_against_ltcg":
                loss_setoff[
                    "stcl_against_ltcg"
                ],

            "ltcl_against_ltcg":
                loss_setoff[
                    "ltcl_against_ltcg"
                ],

            "unabsorbed_stcl":
                loss_setoff[
                    "unabsorbed_stcl"
                ],

            "unabsorbed_ltcl":
                loss_setoff[
                    "unabsorbed_ltcl"
                ],
        },

        # ----------------------------------------------------
        # DEDUCTIONS
        # ----------------------------------------------------

        "deductions": {

            "verified_amount":
                money(
                    verified_deductions
                ),

            "status":
                "verified_claims_applied" if verified_deductions > 0 else "no_verified_claims",

            "verified_claims": applied_verified_deductions,

            "source":
                "tax_deduction_claims (status=verified), regime-eligible deduction catalogue",

            "data_available":
                True,

            "database_write":
                False,
        },

        # ----------------------------------------------------
        # EXEMPT INCOME
        # ----------------------------------------------------

        "exempt_income": {

            "verified_amount":
                money(
                    verified_exempt_income
                ),

            "status": (
                "verified_claims_applied" if verified_exempt_income > 0
                else "verified_claims_not_applied_missing_salary_source" if verified_exempt_claimed_amount > 0 and salary_record is None
                else "verified_claims_not_applied_or_zero" if verified_exempt_claimed_amount > 0
                else "no_verified_claims"
            ),

            "verified_claimed_amount": money(verified_exempt_claimed_amount),

            "verified_claims": verified_exempt_claims,

            "source":
                "transaction-backed salary income plus verified tax_deduction_claims; legacy salary snapshots cannot create income without a matching salary transaction",

            "data_available":
                True,

            "database_write":
                False,
        },

        # ----------------------------------------------------
        # TAXABLE INCOME
        # ----------------------------------------------------

        "taxable_income": {

            "available_gross_income":
                money(
                    available_gross_income
                ),

            "verified_deductions":
                money(
                    verified_deductions
                ),

            "verified_exempt_income":
                money(
                    verified_exempt_income
                ),

            "provisional_taxable_income":
                money(
                    provisional_taxable_income
                ),

            "final_taxable_income":
                None,

            "status":
                taxable_income_status,

            "reason":
                (
                    "Final taxable income cannot be "
                    "marked final until all applicable "
                    "income heads and verified claims "
                    "are available."
                ),
        },

        # ----------------------------------------------------
        # TRANSACTION SUMMARY
        # ----------------------------------------------------

        "transaction_summary": {

            "other_source_transactions":
                other_sources[
                    "transaction_count"
                ],

            "capital_gain_sales":
                len(sales),
        },

        # ----------------------------------------------------
        # CAPITAL-GAIN SALES
        # ----------------------------------------------------

        "capital_gain_sales":
            sales,

        # ----------------------------------------------------
        # COMPLETENESS
        # ----------------------------------------------------

        "completeness": {

            "salary_income":
                False,

            "house_property_income":
                False,

            "business_profession_income":
                False,

            "other_sources_income":
                True,

            "capital_gains":
                True,

            "deductions":
                False,

            "exempt_income":
                False,

            "final_taxable_income":
                False,
        },

        # ----------------------------------------------------
        # SCOPE
        # ----------------------------------------------------

        "scope": {

            "read_only":
                True,

            "database_write":
                False,

            "income_inferred":
                False,

            "deductions_inferred":
                False,

            "exempt_income_inferred":
                False,

            "final_tax_calculated":
                False,

            "surcharge_calculated":
                False,

            "cess_calculated":
                False,

            "rebate_calculated":
                False,
        },

        # ----------------------------------------------------
        # NEXT ENGINE
        # ----------------------------------------------------

        "next_engine":
            "Final Tax Liability Engine",
    }

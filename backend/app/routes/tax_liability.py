# ============================================================
# FINANCIAL OS
# TAX LIABILITY ENGINE
# ============================================================
#
# Version: 1.1
#
# Purpose:
#   Calculate indicative capital-gains tax liability using:
#   - FIFO realised gains
#   - Asset classification
#   - STCG / LTCG classification
#   - Section 111A
#   - Section 112A
#   - LTCG threshold
#   - 4% cess
#
# IMPORTANT:
#   This engine is READ-ONLY.
#
#   It does NOT modify:
#   - Transactions
#   - Investments
#   - Investment transactions
#   - Holdings
#   - Tax records
#   - Database structure
#
#   Final total income-tax liability is intentionally NOT
#   calculated because complete income, deductions, losses,
#   surcharge and TDS/TCS data are not yet available.
#
# ============================================================


from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.routes.ownership import require_matching_user_id


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/tax-liability",
    tags=["Tax Liability Engine"],
)


# ============================================================
# TAX CONSTANTS
# ============================================================

STCG_RATE = Decimal("0.20")

LTCG_RATE = Decimal("0.125")

CESS_RATE = Decimal("0.04")

LTCG_THRESHOLD = Decimal("125000")


# ============================================================
# 87A CONTEXT
# ============================================================

NEW_REGIME_87A_INCOME_LIMIT = Decimal(
    "1200000"
)

NEW_REGIME_87A_MAX_REBATE = Decimal(
    "60000"
)

OLD_REGIME_87A_INCOME_LIMIT = Decimal(
    "500000"
)

OLD_REGIME_87A_MAX_REBATE = Decimal(
    "12500"
)


# ============================================================
# CAPITAL-GAIN ASSET RULES
# ============================================================

ASSET_CLASS_RULES = {

    "listed_equity": {
        "threshold_days": 365,
        "threshold_months": 12,
    },

    "equity_oriented_mf": {
        "threshold_days": 365,
        "threshold_months": 12,
    },

    "unlisted_equity": {
        "threshold_days": 730,
        "threshold_months": 24,
    },

    "listed_other_security": {
        "threshold_days": 365,
        "threshold_months": 12,
    },

    "unlisted_other_security": {
        "threshold_days": 730,
        "threshold_months": 24,
    },
}


# ============================================================
# DECIMAL HELPER
# ============================================================

def to_decimal(value):

    if value is None:
        return Decimal("0")

    return Decimal(str(value))


# ============================================================
# MONEY HELPER
# ============================================================

def money(value):

    return to_decimal(value).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


# ============================================================
# FINANCIAL YEAR
# ============================================================

def get_financial_year_dates(
    financial_year,
):
    """
    Convert:

        2026-27

    into:

        01-Apr-2026
        31-Mar-2027
    """

    if (
        not financial_year
        or len(financial_year) != 7
        or financial_year[4] != "-"
    ):
        raise ValueError(
            "financial_year must use YYYY-YY format."
        )

    try:

        start_year = int(
            financial_year[:4]
        )

        end_year_suffix = int(
            financial_year[5:]
        )

    except ValueError:

        raise ValueError(
            "financial_year must use YYYY-YY format."
        )

    expected_suffix = (
        (start_year + 1) % 100
    )

    if end_year_suffix != expected_suffix:

        raise ValueError(
            "Invalid financial year. Example: 2026-27."
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
# ASSET CLASSIFICATION
# ============================================================

def resolve_asset_class(
    investment_type,
):
    """
    Resolve existing investment_type into a tax asset class.

    Unknown values remain unclassified.
    """

    value = str(
        investment_type or ""
    ).strip().lower()

    mapping = {

        # ----------------------------------------------------
        # LISTED EQUITY
        # ----------------------------------------------------

        "stock":
            "listed_equity",

        "stocks":
            "listed_equity",

        "equity":
            "listed_equity",

        "share":
            "listed_equity",

        "shares":
            "listed_equity",

        "listed equity":
            "listed_equity",

        "listed stock":
            "listed_equity",

        "listed shares":
            "listed_equity",

        # ----------------------------------------------------
        # EQUITY MUTUAL FUNDS
        # ----------------------------------------------------

        "equity mutual fund":
            "equity_oriented_mf",

        "equity mutual funds":
            "equity_oriented_mf",

        "equity mf":
            "equity_oriented_mf",

        "equity-oriented mutual fund":
            "equity_oriented_mf",

        "equity-oriented mutual funds":
            "equity_oriented_mf",

        # ----------------------------------------------------
        # UNLISTED EQUITY
        # ----------------------------------------------------

        "unlisted equity":
            "unlisted_equity",

        "unlisted stock":
            "unlisted_equity",

        "unlisted shares":
            "unlisted_equity",

        # ----------------------------------------------------
        # LISTED OTHER SECURITIES
        # ----------------------------------------------------

        "listed security":
            "listed_other_security",

        "listed securities":
            "listed_other_security",

        "bond":
            "listed_other_security",

        "bonds":
            "listed_other_security",

        # ----------------------------------------------------
        # UNLISTED OTHER SECURITIES
        # ----------------------------------------------------

        "unlisted security":
            "unlisted_other_security",

        "unlisted securities":
            "unlisted_other_security",
    }

    return mapping.get(
        value
    )


# ============================================================
# LOAD INVESTMENTS
# ============================================================

def load_investments(
    db: Session,
    user_id: int,
):
    """
    Load investment metadata required for classification.
    """

    result = db.execute(
        text(
            """
            SELECT
                id,
                name,
                investment_type,
                symbol
            FROM investments
            WHERE user_id = :user_id
            ORDER BY id ASC
            """
        ),
        {
            "user_id": user_id,
        },
    )

    investments = {}

    for row in result.mappings().all():

        investment = dict(row)

        investments[
            investment["id"]
        ] = investment

    return investments


# ============================================================
# LOAD INVESTMENT TRANSACTIONS
# ============================================================

def load_investment_transactions(
    db: Session,
    user_id: int,
    end_date: date,
):
    """
    Load all BUY/SELL investment transactions up to FY end.

    Earlier BUY transactions are required because a current
    FY SELL can consume an older FIFO lot.
    """

    result = db.execute(
        text(
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
            WHERE
                user_id = :user_id
                AND transaction_date <= :end_date
            ORDER BY
                investment_id ASC,
                transaction_date ASC,
                id ASC
            """
        ),
        {
            "user_id": user_id,
            "end_date": end_date,
        },
    )

    return [
        dict(row)
        for row in result.mappings().all()
    ]


# ============================================================
# FIFO CALCULATION
# ============================================================

def calculate_fifo_sales(
    investments,
    transactions,
    start_date,
    end_date,
):
    """
    Calculate realised capital gains using FIFO.

    FIFO is maintained separately for every investment_id.
    """

    lots_by_investment = {}

    sales = []

    # --------------------------------------------------------
    # PROCESS TRANSACTIONS
    # --------------------------------------------------------

    for transaction in transactions:

        investment_id = (
            transaction[
                "investment_id"
            ]
        )

        transaction_type = str(
            transaction[
                "transaction_type"
            ] or ""
        ).strip().upper()

        quantity = to_decimal(
            transaction[
                "quantity"
            ]
        )

        price = to_decimal(
            transaction[
                "price"
            ]
        )

        fees = to_decimal(
            transaction[
                "fees"
            ]
        )

        transaction_date = (
            transaction[
                "transaction_date"
            ]
        )

        # ----------------------------------------------------
        # BUY
        # ----------------------------------------------------

        if transaction_type == "BUY":

            lots_by_investment.setdefault(
                investment_id,
                [],
            )

            lots_by_investment[
                investment_id
            ].append(
                {
                    "buy_transaction_id":
                        transaction["id"],

                    "buy_date":
                        transaction_date,

                    "quantity_remaining":
                        quantity,

                    "unit_price":
                        price,

                    "total_buy_fee":
                        fees,
                }
            )

            continue

        # ----------------------------------------------------
        # ONLY SELL TRANSACTIONS CREATE REALISED GAINS
        # ----------------------------------------------------

        if transaction_type != "SELL":
            continue

        # ----------------------------------------------------
        # ONLY SALES INSIDE SELECTED FY
        # ----------------------------------------------------

        if transaction_date < start_date:
            continue

        if transaction_date > end_date:
            continue

        remaining_quantity = quantity

        gross_sale_value = (
            quantity * price
        )

        sale_fee = fees

        cost_basis = Decimal("0")

        matched_lots = []

        lots = lots_by_investment.setdefault(
            investment_id,
            [],
        )

        # ----------------------------------------------------
        # CONSUME FIFO LOTS
        # ----------------------------------------------------

        while (
            remaining_quantity > 0
            and lots
        ):

            lot = lots[0]

            available_quantity = (
                to_decimal(
                    lot[
                        "quantity_remaining"
                    ]
                )
            )

            if available_quantity <= 0:

                lots.pop(0)

                continue

            matched_quantity = min(
                remaining_quantity,
                available_quantity,
            )

            buy_fee_remaining = (
                to_decimal(
                    lot[
                        "total_buy_fee"
                    ]
                )
            )

            allocated_buy_fee = Decimal(
                "0"
            )

            if available_quantity > 0:

                allocated_buy_fee = (
                    buy_fee_remaining
                    * matched_quantity
                    / available_quantity
                )

            matched_cost = (
                matched_quantity
                * to_decimal(
                    lot[
                        "unit_price"
                    ]
                )
                + allocated_buy_fee
            )

            cost_basis += matched_cost

            holding_days = (
                transaction_date
                - lot["buy_date"]
            ).days

            matched_lots.append(
                {
                    "buy_transaction_id":
                        lot[
                            "buy_transaction_id"
                        ],

                    "buy_date":
                        lot["buy_date"],

                    "quantity":
                        matched_quantity,

                    "buy_price":
                        to_decimal(
                            lot[
                                "unit_price"
                            ]
                        ),

                    "allocated_buy_fee":
                        allocated_buy_fee,

                    "holding_days":
                        holding_days,
                }
            )

            # ------------------------------------------------
            # REDUCE LOT
            # ------------------------------------------------

            lot[
                "quantity_remaining"
            ] = (
                available_quantity
                - matched_quantity
            )

            lot[
                "total_buy_fee"
            ] = (
                buy_fee_remaining
                - allocated_buy_fee
            )

            remaining_quantity -= (
                matched_quantity
            )

            if (
                lot[
                    "quantity_remaining"
                ]
                <= 0
            ):

                lots.pop(0)

        # ----------------------------------------------------
        # UNMATCHED QUANTITY
        # ----------------------------------------------------

        unmatched_quantity = max(
            remaining_quantity,
            Decimal("0"),
        )

        # ----------------------------------------------------
        # NET SALE PROCEEDS
        # ----------------------------------------------------

        net_sale_proceeds = (
            gross_sale_value
            - sale_fee
        )

        # ----------------------------------------------------
        # REALISED GAIN / LOSS
        # ----------------------------------------------------

        realised_gain_loss = (
            net_sale_proceeds
            - cost_basis
        )

        # ----------------------------------------------------
        # WEIGHTED HOLDING PERIOD
        # ----------------------------------------------------

        if matched_lots:

            total_matched_quantity = sum(
                (
                    lot["quantity"]
                    for lot in matched_lots
                ),
                Decimal("0"),
            )

            weighted_days = (
                sum(
                    (
                        lot["holding_days"]
                        * lot["quantity"]
                    )
                    for lot in matched_lots
                )
                / total_matched_quantity
            )

            holding_days = int(
                weighted_days
            )

        else:

            holding_days = None

        # ----------------------------------------------------
        # INVESTMENT DETAILS
        # ----------------------------------------------------

        investment = investments.get(
            investment_id,
            {},
        )

        sales.append(
            {
                "sell_transaction_id":
                    transaction["id"],

                "investment_id":
                    investment_id,

                "investment_name":
                    investment.get(
                        "name"
                    ),

                "symbol":
                    investment.get(
                        "symbol"
                    ),

                "investment_type":
                    investment.get(
                        "investment_type"
                    ),

                "sale_date":
                    transaction_date,

                "quantity":
                    quantity,

                "sale_price":
                    price,

                "gross_sale_value":
                    gross_sale_value,

                "sell_fee":
                    sale_fee,

                "net_sale_proceeds":
                    net_sale_proceeds,

                "cost_basis":
                    cost_basis,

                "realised_gain_loss":
                    realised_gain_loss,

                "holding_days":
                    holding_days,

                "matched_lots":
                    matched_lots,

                "unmatched_quantity":
                    unmatched_quantity,
            }
        )

    return sales


# ============================================================
# CLASSIFY SALE
# ============================================================

def classify_sale(
    sale,
):
    """
    Classify realised gain as STCG/LTCG.
    """

    asset_class = resolve_asset_class(
        sale[
            "investment_type"
        ]
    )

    result = {
        "asset_class":
            asset_class,

        "asset_class_source":
            "investment_type",

        "classification":
            "UNCLASSIFIED",

        "classification_reason":
            None,

        "threshold_days":
            None,

        "threshold_months":
            None,
    }

    # --------------------------------------------------------
    # UNKNOWN ASSET CLASS
    # --------------------------------------------------------

    if not asset_class:

        result[
            "classification_reason"
        ] = "asset_class_required"

        return result

    rules = ASSET_CLASS_RULES[
        asset_class
    ]

    result[
        "threshold_days"
    ] = rules[
        "threshold_days"
    ]

    result[
        "threshold_months"
    ] = rules[
        "threshold_months"
    ]

    holding_days = sale[
        "holding_days"
    ]

    if holding_days is None:

        result[
            "classification_reason"
        ] = "holding_period_unavailable"

        return result

    # --------------------------------------------------------
    # LTCG
    # --------------------------------------------------------

    if (
        holding_days
        >= rules[
            "threshold_days"
        ]
    ):

        result[
            "classification"
        ] = "LTCG"

        result[
            "classification_reason"
        ] = "holding_period_reached"

    # --------------------------------------------------------
    # STCG
    # --------------------------------------------------------

    else:

        result[
            "classification"
        ] = "STCG"

        result[
            "classification_reason"
        ] = "holding_period_below_threshold"

    return result


# ============================================================
# TAX LIABILITY ENDPOINT
# ============================================================

@router.get("/", dependencies=[Depends(require_matching_user_id)])
def get_tax_liability(
    user_id: int,
    financial_year: str = "2026-27",
    taxpayer_type: str = "individual",
    residential_status: str = "resident",
    tax_regime: str = "new",
    stt_confirmed: bool = False,
    db: Session = Depends(get_db),
):
    """
    Return a read-only indicative capital-gains tax liability.

    Current scope:

        FIFO capital gains
        STCG/LTCG classification
        Section 111A STCG
        Section 112A LTCG
        LTCG threshold
        4% cess
        87A context

    Not yet included:

        Salary income
        Business income
        Other income
        Deductions
        Loss set-off
        Loss carry-forward
        Surcharge
        Marginal relief
        TDS/TCS
        Advance tax
        Final ITR liability
    """

    # ========================================================
    # NORMALIZE INPUT
    # ========================================================

    taxpayer_type = str(
        taxpayer_type
    ).strip().lower()

    residential_status = str(
        residential_status
    ).strip().lower()

    tax_regime = str(
        tax_regime
    ).strip().lower()

    # ========================================================
    # VALIDATION
    # ========================================================

    if taxpayer_type not in {
        "individual",
        "huf",
    }:

        return {
            "status": "error",
            "message":
                "taxpayer_type must be individual or huf.",
        }

    if residential_status not in {
        "resident",
        "non_resident",
    }:

        return {
            "status": "error",
            "message":
                "residential_status must be resident or non_resident.",
        }

    if tax_regime not in {
        "new",
        "old",
    }:

        return {
            "status": "error",
            "message":
                "tax_regime must be new or old.",
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
    # LOAD DATA
    # ========================================================

    investments = load_investments(
        db,
        user_id,
    )

    transactions = (
        load_investment_transactions(
            db,
            user_id,
            end_date,
        )
    )

    # ========================================================
    # FIFO SALES
    # ========================================================

    sales = calculate_fifo_sales(
        investments,
        transactions,
        start_date,
        end_date,
    )

    # ========================================================
    # CLASSIFICATION TOTALS
    # ========================================================

    stcg_gain = Decimal("0")

    ltcg_gain = Decimal("0")

    unclassified_gain = Decimal("0")

    classified_sale_count = 0

    unclassified_sale_count = 0

    classified_sales = []

    # ========================================================
    # CLASSIFY EACH SALE
    # ========================================================

    for sale in sales:

        classification = classify_sale(
            sale
        )

        gain = to_decimal(
            sale[
                "realised_gain_loss"
            ]
        )

        enriched_sale = {
            **sale,
            **classification,
        }

        classified_sales.append(
            enriched_sale
        )

        classification_name = (
            classification[
                "classification"
            ]
        )

        if classification_name == "STCG":

            stcg_gain += gain

            classified_sale_count += 1

        elif classification_name == "LTCG":

            ltcg_gain += gain

            classified_sale_count += 1

        else:

            unclassified_gain += gain

            unclassified_sale_count += 1

    # ========================================================
    # STCG TAX
    # ========================================================

    stcg_tax = Decimal("0")

    stcg_status = "not_applicable"

    if stcg_gain > 0:

        if stt_confirmed:

            stcg_tax = (
                stcg_gain
                * STCG_RATE
            )

            stcg_status = "calculated"

        else:

            stcg_status = (
                "requires_stt_confirmation"
            )

    # ========================================================
    # LTCG TAX
    # ========================================================

    taxable_ltcg = max(
        ltcg_gain
        - LTCG_THRESHOLD,
        Decimal("0"),
    )

    ltcg_tax = (
        taxable_ltcg
        * LTCG_RATE
    )

    # ========================================================
    # BASE TAX
    # ========================================================

    base_tax = (
        stcg_tax
        + ltcg_tax
    )

    # ========================================================
    # CESS
    # ========================================================

    cess = (
        base_tax
        * CESS_RATE
    )

    special_rate_tax_total = (
        base_tax
        + cess
    )

    # ========================================================
    # 87A CONTEXT
    # ========================================================

    if tax_regime == "new":

        rebate_context = {
            "possible": True,

            "income_limit":
                NEW_REGIME_87A_INCOME_LIMIT,

            "maximum_rebate":
                NEW_REGIME_87A_MAX_REBATE,

            "calculated": False,

            "reason":
                "Complete total income is required before applying 87A rebate.",
        }

    else:

        rebate_context = {
            "possible": True,

            "income_limit":
                OLD_REGIME_87A_INCOME_LIMIT,

            "maximum_rebate":
                OLD_REGIME_87A_MAX_REBATE,

            "calculated": False,

            "reason":
                "Complete total income is required before applying 87A rebate.",
        }

    # ========================================================
    # ENGINE STATUS
    # ========================================================

    if unclassified_sale_count > 0:

        engine_status = (
            "requires_asset_classification"
        )

    elif (
        stcg_gain > 0
        and not stt_confirmed
    ):

        engine_status = (
            "requires_stt_confirmation"
        )

    else:

        engine_status = (
            "capital_gain_liability_calculated"
        )

    # ========================================================
    # SERIALIZE SALES
    # ========================================================

    serialized_sales = []

    for sale in classified_sales:

        serialized_lots = []

        for lot in sale[
            "matched_lots"
        ]:

            serialized_lots.append(
                {
                    "buy_transaction_id":
                        lot[
                            "buy_transaction_id"
                        ],

                    "buy_date":
                        lot[
                            "buy_date"
                        ],

                    "quantity":
                        lot[
                            "quantity"
                        ],

                    "buy_price":
                        money(
                            lot[
                                "buy_price"
                            ]
                        ),

                    "allocated_buy_fee":
                        money(
                            lot[
                                "allocated_buy_fee"
                            ]
                        ),

                    "holding_days":
                        lot[
                            "holding_days"
                        ],
                }
            )

        serialized_sales.append(
            {
                "sell_transaction_id":
                    sale[
                        "sell_transaction_id"
                    ],

                "investment_id":
                    sale[
                        "investment_id"
                    ],

                "investment_name":
                    sale[
                        "investment_name"
                    ],

                "symbol":
                    sale[
                        "symbol"
                    ],

                "investment_type":
                    sale[
                        "investment_type"
                    ],

                "asset_class":
                    sale[
                        "asset_class"
                    ],

                "classification":
                    sale[
                        "classification"
                    ],

                "classification_reason":
                    sale[
                        "classification_reason"
                    ],

                "sale_date":
                    sale[
                        "sale_date"
                    ],

                "quantity":
                    sale[
                        "quantity"
                    ],

                "sale_price":
                    money(
                        sale[
                            "sale_price"
                        ]
                    ),

                "gross_sale_value":
                    money(
                        sale[
                            "gross_sale_value"
                        ]
                    ),

                "sell_fee":
                    money(
                        sale[
                            "sell_fee"
                        ]
                    ),

                "net_sale_proceeds":
                    money(
                        sale[
                            "net_sale_proceeds"
                        ]
                    ),

                "cost_basis":
                    money(
                        sale[
                            "cost_basis"
                        ]
                    ),

                "realised_gain_loss":
                    money(
                        sale[
                            "realised_gain_loss"
                        ]
                    ),

                "holding_days":
                    sale[
                        "holding_days"
                    ],

                "threshold_days":
                    sale[
                        "threshold_days"
                    ],

                "threshold_months":
                    sale[
                        "threshold_months"
                    ],

                "unmatched_quantity":
                    sale[
                        "unmatched_quantity"
                    ],

                "matched_lots":
                    serialized_lots,
            }
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "status": "success",

        "user_id": user_id,

        "engine": {
            "name":
                "Tax Liability Engine",

            "version":
                "1.1",

            "read_only":
                True,

            "status":
                engine_status,
        },

        "taxpayer_context": {

            "taxpayer_type":
                taxpayer_type,

            "residential_status":
                residential_status,

            "tax_regime":
                tax_regime,

            "financial_year":
                financial_year,

            "period": {

                "start_date":
                    start_date,

                "end_date":
                    end_date,
            },

            "stt_confirmed":
                stt_confirmed,
        },

        "capital_gains": {

            "sale_count":
                len(sales),

            "classified_sale_count":
                classified_sale_count,

            "unclassified_sale_count":
                unclassified_sale_count,

            "stcg_realised_gain_loss":
                money(
                    stcg_gain
                ),

            "ltcg_realised_gain_loss":
                money(
                    ltcg_gain
                ),

            "unclassified_gain_loss":
                money(
                    unclassified_gain
                ),
        },

        "tax_calculation": {

            "stcg": {

                "section":
                    "111A",

                "rate":
                    STCG_RATE,

                "gain":
                    money(
                        stcg_gain
                    ),

                "tax":
                    money(
                        stcg_tax
                    ),

                "stt_confirmed":
                    stt_confirmed,

                "status":
                    stcg_status,
            },

            "ltcg": {

                "section":
                    "112A",

                "rate":
                    LTCG_RATE,

                "aggregate_threshold":
                    LTCG_THRESHOLD,

                "gain":
                    money(
                        ltcg_gain
                    ),

                "taxable_gain_after_threshold":
                    money(
                        taxable_ltcg
                    ),

                "tax":
                    money(
                        ltcg_tax
                    ),
            },

            "base_tax":
                money(
                    base_tax
                ),

            "surcharge": {

                "calculated":
                    False,

                "amount":
                    Decimal("0"),

                "reason":
                    "Complete total income is required before calculating surcharge.",
            },

            "cess": {

                "rate":
                    CESS_RATE,

                "amount":
                    money(
                        cess
                    ),
            },

            "special_rate_tax_total":
                money(
                    special_rate_tax_total
                ),
        },

        "rebate_87a_context":
            rebate_context,

        "sales":
            serialized_sales,

        "final_liability": {

            "status":
                "incomplete_total_income_required",

            "amount":
                None,

            "reason":
                "Final income-tax liability requires complete total income, deductions, loss set-off/carry-forward, surcharge, rebate applicability, TDS/TCS and other tax inputs.",
        },

        "scope": {

            "capital_gains":
                True,

            "salary_income":
                False,

            "business_income":
                False,

            "other_income":
                False,

            "deductions":
                False,

            "loss_setoff":
                False,

            "loss_carry_forward":
                False,

            "surcharge":
                False,

            "marginal_relief":
                False,

            "tds_tcs":
                False,

            "advance_tax":
                False,

            "itr_calculation":
                False,
        },

        "next_engine":
            "Income Tax & Loss Set-off Engine",
    }

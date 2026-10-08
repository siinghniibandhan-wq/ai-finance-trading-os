# ============================================================
# FINANCIAL OS
# ASSET CLASSIFICATION RESOLVER v1.0
# ============================================================
#
# Purpose:
# - Resolve investment records into tax asset classes
# - Use existing investment_type data
# - Provide a safe bridge for Capital Gains Classification
#
# IMPORTANT:
# - READ-ONLY
# - Does NOT modify investments
# - Does NOT modify investment_transactions
# - Does NOT modify capital_gains.py
# - Does NOT calculate tax
# - Does NOT guess ambiguous asset types
#
# ============================================================


from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.database import get_db


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/asset-classification",
    tags=["Asset Classification"],
)


# ============================================================
# ASSET TYPE MAPPING
# ============================================================
#
# Only explicit / recognizable labels are mapped.
#
# Anything else remains UNCLASSIFIED.
#
# ============================================================

ASSET_TYPE_MAP = {

    # --------------------------------------------------------
    # EQUITY
    # --------------------------------------------------------

    "stock": "listed_equity",
    "stocks": "listed_equity",
    "equity": "listed_equity",
    "share": "listed_equity",
    "shares": "listed_equity",
    "listed equity": "listed_equity",
    "listed stock": "listed_equity",
    "listed shares": "listed_equity",

    # --------------------------------------------------------
    # EQUITY MUTUAL FUNDS
    # --------------------------------------------------------

    "equity mutual fund": (
        "equity_oriented_mf"
    ),

    "equity mutual funds": (
        "equity_oriented_mf"
    ),

    "equity mf": (
        "equity_oriented_mf"
    ),

    "equity-oriented mutual fund": (
        "equity_oriented_mf"
    ),

    "equity-oriented mutual funds": (
        "equity_oriented_mf"
    ),

    # --------------------------------------------------------
    # UNLISTED EQUITY
    # --------------------------------------------------------

    "unlisted equity": (
        "unlisted_equity"
    ),

    "unlisted stock": (
        "unlisted_equity"
    ),

    "unlisted shares": (
        "unlisted_equity"
    ),

    # --------------------------------------------------------
    # OTHER LISTED SECURITIES
    # --------------------------------------------------------

    "listed security": (
        "listed_other_security"
    ),

    "listed securities": (
        "listed_other_security"
    ),

    "bond": (
        "listed_other_security"
    ),

    "bonds": (
        "listed_other_security"
    ),

    # --------------------------------------------------------
    # OTHER UNLISTED SECURITIES
    # --------------------------------------------------------

    "unlisted security": (
        "unlisted_other_security"
    ),

    "unlisted securities": (
        "unlisted_other_security"
    ),
}


# ============================================================
# NORMALIZE INVESTMENT TYPE
# ============================================================

def normalize_investment_type(
    investment_type,
):
    """
    Normalize investment_type before mapping.
    """

    if investment_type is None:
        return ""

    return (
        str(investment_type)
        .strip()
        .lower()
    )


# ============================================================
# RESOLVE ASSET CLASS
# ============================================================

def resolve_asset_class(
    investment_type,
):
    """
    Resolve an existing investment_type into an
    internal tax asset class.

    Unknown values remain UNCLASSIFIED.
    """

    normalized_type = (
        normalize_investment_type(
            investment_type
        )
    )

    asset_class = ASSET_TYPE_MAP.get(
        normalized_type
    )

    if asset_class is None:

        return {
            "asset_class": "UNCLASSIFIED",
            "status": "unclassified",
            "reason": (
                "Investment type does not have "
                "a safe automatic asset-class mapping."
            ),
        }

    return {
        "asset_class": asset_class,
        "status": "classified",
        "reason": (
            "Investment type matched "
            "the configured asset-class mapping."
        ),
    }


# ============================================================
# LIST ASSET CLASSIFICATIONS
# ============================================================

@router.get("/")
def list_asset_classifications(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Return all investment records with their resolved
    asset class.

    This endpoint is READ-ONLY.
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
                broker
            FROM investments
            WHERE user_id = :user_id
            ORDER BY id ASC
            """
        ),
        {
            "user_id": user_id,
        },
    )

    investments = []

    classified_count = 0
    unclassified_count = 0

    for row in result:

        investment = dict(
            row._mapping
        )

        classification = (
            resolve_asset_class(
                investment[
                    "investment_type"
                ]
            )
        )

        if (
            classification[
                "status"
            ]
            == "classified"
        ):
            classified_count += 1
        else:
            unclassified_count += 1

        investments.append(
            {
                "investment_id": (
                    investment["id"]
                ),
                "name": (
                    investment["name"]
                ),
                "investment_type": (
                    investment[
                        "investment_type"
                    ]
                ),
                "symbol": (
                    investment["symbol"]
                ),
                "asset_class": (
                    classification[
                        "asset_class"
                    ]
                ),
                "classification_status": (
                    classification[
                        "status"
                    ]
                ),
                "classification_reason": (
                    classification[
                        "reason"
                    ]
                ),
            }
        )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "status": "success",

        "user_id": user_id,

        "asset_classification_engine": {
            "name": (
                "Asset Classification Resolver"
            ),
            "version": "1.0",
            "read_only": True,
        },

        "summary": {
            "investment_count": len(
                investments
            ),
            "classified_count": (
                classified_count
            ),
            "unclassified_count": (
                unclassified_count
            ),
        },

        "mapping_source": (
            "investment_type"
        ),

        "investments": investments,
    }

"""Income from house property (Sections 22-24 of the Income-tax Act).

Pure functions, no database or web imports, so they are easy to test.

Rules used (all amounts are for one financial year):
  Let-out property
    Net annual value = rent received - municipal taxes paid by the owner (not below 0)
    Standard deduction = 30% of net annual value
    Interest on housing loan = actual interest for the year (both regimes)
    Income = net annual value - standard deduction - interest
  Self-occupied property
    Annual value is nil. Interest is allowed only in the old regime, up to
    Rs 2,00,000 in total across self-occupied properties. Income = -interest allowed.
  None
    The person confirms there is no house property income. Counts as zero.
Loss from house property:
  Old regime: set off against other income up to Rs 2,00,000; any excess is
  not used here (carry-forward is not modelled).
  New regime: a loss is not set off against other income (counts as zero).
"""
from decimal import Decimal, ROUND_HALF_UP

PROPERTY_TYPES = ("let_out", "self_occupied", "none")
STANDARD_DEDUCTION_RATE = Decimal("0.30")
SELF_OCCUPIED_INTEREST_CAP = Decimal("200000")
LOSS_SETOFF_CAP = Decimal("200000")
_CENT = Decimal("0.01")


def _d(value):
    return Decimal(str(value if value is not None else 0))


def _q(value):
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


def compute_house_property(records, tax_regime):
    """records: objects with property_type, annual_rent_received,
    municipal_taxes_paid, interest_on_housing_loan (and optional id/property_label).
    Returns a dict with a per-property breakdown and the amount to count."""
    regime = str(tax_regime or "").strip().lower()
    old_regime = regime == "old"
    properties = []
    total = Decimal("0")
    self_interest_left = SELF_OCCUPIED_INTEREST_CAP if old_regime else Decimal("0")

    for rec in records:
        kind = str(getattr(rec, "property_type", "") or "").strip().lower()
        label = getattr(rec, "property_label", None)
        item = {
            "id": getattr(rec, "id", None), "label": label, "property_type": kind,
            "gross_annual_value": Decimal("0"), "municipal_taxes": Decimal("0"),
            "net_annual_value": Decimal("0"), "standard_deduction_30pct": Decimal("0"),
            "interest_claimed": Decimal("0"), "interest_allowed": Decimal("0"),
            "income": Decimal("0"),
        }
        if kind == "let_out":
            rent = max(_d(getattr(rec, "annual_rent_received", 0)), Decimal("0"))
            municipal = min(max(_d(getattr(rec, "municipal_taxes_paid", 0)), Decimal("0")), rent)
            interest = max(_d(getattr(rec, "interest_on_housing_loan", 0)), Decimal("0"))
            nav = rent - municipal
            std = _q(nav * STANDARD_DEDUCTION_RATE)
            item.update(
                gross_annual_value=rent, municipal_taxes=municipal, net_annual_value=nav,
                standard_deduction_30pct=std, interest_claimed=interest,
                interest_allowed=interest, income=_q(nav - std - interest),
            )
        elif kind == "self_occupied":
            interest = max(_d(getattr(rec, "interest_on_housing_loan", 0)), Decimal("0"))
            allowed = min(interest, self_interest_left)
            self_interest_left -= allowed
            item.update(interest_claimed=interest, interest_allowed=allowed, income=_q(-allowed))
        total += item["income"]
        properties.append(item)

    total = _q(total)
    if total >= 0:
        counted = total
    elif old_regime:
        counted = max(total, -LOSS_SETOFF_CAP)
    else:
        counted = Decimal("0")
    return {
        "properties": properties,
        "total_before_loss_limit": total,
        "counted_amount": _q(counted),
        "loss_not_set_off": _q(counted - total) if total < 0 else Decimal("0"),
        "tax_regime": "old" if old_regime else "new",
    }

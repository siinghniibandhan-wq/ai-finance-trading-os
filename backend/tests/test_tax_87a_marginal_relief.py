"""Regression tests for Section 87A rebate and New Regime marginal relief."""
from decimal import Decimal

from app.routes import final_tax_liability as tax_liability_module
from app.routes.final_tax_liability import (
    calculate_87a_rebate,
    calculate_new_regime_slab_tax,
)


def test_new_regime_full_rebate_at_12_lakh():
    slab_tax = calculate_new_regime_slab_tax(1_200_000)
    result = calculate_87a_rebate(1_200_000, slab_tax, "new", "resident")
    assert slab_tax == Decimal("60000.00")
    assert result["rebate"] == Decimal("60000.00")
    assert result["marginal_relief"] == Decimal("0.00")


def test_new_regime_marginal_relief_is_separate_from_rebate():
    income = Decimal("1200100")
    slab_tax = calculate_new_regime_slab_tax(income)
    result = calculate_87a_rebate(income, slab_tax, "new", "resident")
    assert slab_tax == Decimal("60015.00")
    assert result["rebate"] == Decimal("0.00")
    assert result["marginal_relief"] == Decimal("59915.00")
    assert slab_tax - result["marginal_relief"] == Decimal("100.00")


def test_no_marginal_relief_when_ordinary_tax_is_below_income_excess():
    result = calculate_87a_rebate(1_300_000, 50_000, "new", "resident")
    assert result["rebate"] == Decimal("0.00")
    assert result["marginal_relief"] == Decimal("0.00")


def test_old_regime_does_not_get_new_regime_marginal_relief():
    result = calculate_87a_rebate(510_000, 13_500, "old", "resident")
    assert result["rebate"] == Decimal("0.00")
    assert result["marginal_relief"] == Decimal("0.00")


def test_nonresident_not_eligible_for_87a():
    result = calculate_87a_rebate(500_000, 12_500, "old", "non_resident")
    assert result["eligible"] is False
    assert result["rebate"] == Decimal("0.00")



def test_final_liability_excludes_special_rate_gains_from_87a_rebate_basis(monkeypatch):
    captured = {}

    def capture_rebate_basis(taxable_income, normal_tax, tax_regime, residential_status):
        captured["taxable_income"] = taxable_income
        return calculate_87a_rebate(taxable_income, normal_tax, tax_regime, residential_status)

    monkeypatch.setattr(tax_liability_module, "calculate_87a_rebate", capture_rebate_basis)
    monkeypatch.setattr(
        tax_liability_module,
        "get_final_taxable_income",
        lambda **kwargs: {
            "status": "success",
            "income_heads": {
                "salary": {"available": True},
                "house_property": {"available": True},
                "business_or_profession": {"available": True},
                "other_sources": {"total": 0},
                "capital_gains": {
                    "stcg_after_setoff": 500000,
                    "ltcg_after_setoff": 0,
                },
            },
            "deductions": {"verified_amount": 0},
            "exempt_income": {"verified_amount": 0},
            "taxable_income": {"provisional_taxable_income": 1300000},
        },
    )

    class _Query:
        def filter(self, *args, **kwargs):
            return self

        def all(self):
            return []

    class _DB:
        def query(self, *args, **kwargs):
            return _Query()

    tax_liability_module.get_final_tax_liability(
        user_id=1,
        financial_year="2026-27",
        tax_regime="new",
        residential_status="resident",
        age_category=None,
        stt_confirmed=True,
        ltcg_112a_confirmed=False,
        tds_credit=None,
        advance_tax_credit=None,
        self_assessment_tax_credit=None,
        db=_DB(),
    )

    # Total income is ₹13 lakh, but ₹5 lakh is STCG taxed separately.
    # Section 87A applies only to the normal slab-rate component (₹8 lakh).
    assert captured["taxable_income"] == Decimal("800000")

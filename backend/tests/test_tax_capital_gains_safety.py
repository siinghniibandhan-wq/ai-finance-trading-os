"""Regression tests for safe STCG classification in tax liability."""
from decimal import Decimal
from app.routes.final_tax_liability import split_capital_gains_tax_bases


def test_unconfirmed_stt_keeps_stcg_in_ordinary_slabs():
    result = split_capital_gains_tax_bases(Decimal("50000"), Decimal("200000"), False)
    assert result["stcg_special_rate"] == Decimal("0")
    assert result["stcg_ordinary_slab"] == Decimal("50000")
    assert result["ltcg_special_rate"] == Decimal("200000")


def test_confirmed_stt_uses_special_rate_stcg_base():
    result = split_capital_gains_tax_bases(Decimal("50000"), Decimal("200000"), True)
    assert result["stcg_special_rate"] == Decimal("50000")
    assert result["stcg_ordinary_slab"] == Decimal("0")
    assert result["ltcg_special_rate"] == Decimal("200000")


def test_negative_gains_are_clamped_to_zero_for_tax_base_split():
    result = split_capital_gains_tax_bases(Decimal("-50"), Decimal("-100"), False)
    assert result["stcg_special_rate"] == Decimal("0")
    assert result["stcg_ordinary_slab"] == Decimal("0")
    assert result["ltcg_special_rate"] == Decimal("0")

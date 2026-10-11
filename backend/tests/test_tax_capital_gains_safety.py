"""Regression tests for safe STCG/LTCG classification in tax liability."""
from decimal import Decimal
from app.routes.final_tax_liability import split_capital_gains_tax_bases


def test_unconfirmed_stt_keeps_stcg_in_ordinary_slabs():
    result = split_capital_gains_tax_bases(
        Decimal("50000"), Decimal("200000"), False, False
    )
    assert result["stcg_special_rate"] == Decimal("0")
    assert result["stcg_ordinary_slab"] == Decimal("50000")
    assert result["ltcg_special_rate"] == Decimal("0")
    assert result["ltcg_ordinary_slab"] == Decimal("200000")


def test_confirmed_stt_does_not_assume_section_112a_eligibility():
    result = split_capital_gains_tax_bases(
        Decimal("50000"), Decimal("200000"), True, False
    )
    assert result["stcg_special_rate"] == Decimal("50000")
    assert result["stcg_ordinary_slab"] == Decimal("0")
    assert result["ltcg_special_rate"] == Decimal("0")
    assert result["ltcg_ordinary_slab"] == Decimal("200000")


def test_confirmed_section_112a_eligibility_uses_special_rate_base():
    result = split_capital_gains_tax_bases(
        Decimal("50000"), Decimal("200000"), True, True
    )
    assert result["ltcg_special_rate"] == Decimal("200000")
    assert result["ltcg_ordinary_slab"] == Decimal("0")


def test_negative_gains_are_clamped_to_zero():
    result = split_capital_gains_tax_bases(
        Decimal("-50"), Decimal("-100"), False, False
    )
    assert result["stcg_special_rate"] == Decimal("0")
    assert result["stcg_ordinary_slab"] == Decimal("0")
    assert result["ltcg_special_rate"] == Decimal("0")
    assert result["ltcg_ordinary_slab"] == Decimal("0")

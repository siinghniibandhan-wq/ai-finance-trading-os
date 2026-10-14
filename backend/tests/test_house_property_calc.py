import sys, os
from decimal import Decimal
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.house_property_calc import compute_house_property


def rec(kind, rent=0, municipal=0, interest=0, i=1):
    return SimpleNamespace(id=i, property_label=f"p{i}", property_type=kind, annual_rent_received=rent,
                           municipal_taxes_paid=municipal, interest_on_housing_loan=interest)


def test_let_out_basic():
    r = compute_house_property([rec("let_out", 240000, 10000, 0)], "old")
    p = r["properties"][0]
    assert p["net_annual_value"] == Decimal("230000")
    assert p["standard_deduction_30pct"] == Decimal("69000.00")
    assert r["counted_amount"] == Decimal("161000.00")


def test_let_out_with_interest_gives_loss_within_cap_old():
    r = compute_house_property([rec("let_out", 240000, 0, 400000)], "old")
    assert r["total_before_loss_limit"] == Decimal("-232000.00")
    assert r["counted_amount"] == Decimal("-200000.00")
    assert r["loss_not_set_off"] == Decimal("32000.00")


def test_loss_not_set_off_in_new_regime():
    r = compute_house_property([rec("let_out", 240000, 0, 400000)], "new")
    assert r["counted_amount"] == Decimal("0.00")


def test_self_occupied_interest_cap_old():
    r = compute_house_property([rec("self_occupied", interest=350000)], "old")
    assert r["properties"][0]["interest_allowed"] == Decimal("200000")
    assert r["counted_amount"] == Decimal("-200000.00")


def test_self_occupied_no_interest_in_new_regime():
    r = compute_house_property([rec("self_occupied", interest=350000)], "new")
    assert r["counted_amount"] == Decimal("0.00")


def test_two_self_occupied_share_one_cap():
    r = compute_house_property([rec("self_occupied", interest=150000, i=1), rec("self_occupied", interest=150000, i=2)], "old")
    assert r["counted_amount"] == Decimal("-200000.00")


def test_none_counts_zero():
    r = compute_house_property([rec("none")], "old")
    assert r["counted_amount"] == Decimal("0.00")


def test_municipal_tax_cannot_exceed_rent():
    r = compute_house_property([rec("let_out", 1000, 5000, 0)], "old")
    assert r["properties"][0]["net_annual_value"] == Decimal("0")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("passed", name)

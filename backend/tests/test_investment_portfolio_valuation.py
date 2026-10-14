from pathlib import Path


def test_bulk_refresh_uses_active_ledger_quantity_and_weighted_buy_cost():
    source = Path(__file__).parents[1].joinpath(
        "app", "routes", "investments.py"
    ).read_text()
    refresh = source.split('@router.post("/refresh")', 1)[1].split(
        '@router.post("/{investment_id}/refresh")', 1
    )[0]

    assert "COALESCE(tx.active_quantity, 0)" in refresh
    assert "tx.weighted_buy_price" in refresh
    assert "FROM investment_transactions" in refresh


def test_single_refresh_uses_active_ledger_quantity_and_weighted_buy_cost():
    source = Path(__file__).parents[1].joinpath(
        "app", "routes", "investments.py"
    ).read_text()
    refresh = source.split('@router.post("/{investment_id}/refresh")', 1)[1]

    assert "COALESCE(tx.active_quantity, 0)" in refresh
    assert "tx.weighted_buy_price" in refresh
    assert "FROM investment_transactions" in refresh

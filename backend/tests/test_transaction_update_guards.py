from pathlib import Path


def test_transaction_edit_rejects_conversion_to_transfer_before_balance_mutation():
    source = Path(__file__).parents[1].joinpath(
        "app", "routes", "transactions.py"
    ).read_text()
    route_start = source.index("def update_transaction(")
    route_end = source.index("# DELETE TRANSACTION", route_start)
    route = source[route_start:route_end]

    guard = route.index('if str(new_type or "").strip().lower() == "transfer":')
    account_balance_mutation = route.index("_reverse_balance_effect(old_account, old_type, old_amount)")
    assert guard < account_balance_mutation
    assert "Create a new transfer using the Transfer form." in route

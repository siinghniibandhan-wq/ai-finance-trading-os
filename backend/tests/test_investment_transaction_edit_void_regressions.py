"""Regression guards for investment transaction edit and void consistency."""

from pathlib import Path


ROUTE_SOURCE = Path(__file__).parents[1].joinpath(
    "app", "routes", "investment_transactions.py"
).read_text()


def route_source(name):
    start = ROUTE_SOURCE.index(f"def {name}(")
    end = ROUTE_SOURCE.find("\n@router.", start + 1)
    return ROUTE_SOURCE[start : end if end != -1 else None]


def test_edit_only_updates_active_transactions_and_recalculates_balance():
    source = route_source("update_transaction")

    assert 'if existing.status != "ACTIVE"' in source
    assert "Only active transactions can be edited." in source
    assert "status = 'ACTIVE'" in source
    assert "UPDATE investments SET quantity = :quantity" in source
    assert "db.commit()" in source


def test_void_is_audited_and_recalculates_balance_from_active_ledger():
    source = route_source("void_transaction")

    assert 'if existing.status != "ACTIVE"' in source
    assert "status = 'VOIDED'" in source
    assert "void_reason = :reason" in source
    assert "voided_at = CURRENT_TIMESTAMP" in source
    assert "status = 'ACTIVE'" in source
    assert "UPDATE investments SET quantity = :quantity" in source
    assert "db.commit()" in source


def test_void_rejects_changes_that_leave_later_sells_unfunded():
    source = route_source("void_transaction")

    assert "Voiding this transaction would make later SELL activity exceed available BUY quantity." in source
    assert "if running < 0:" in source


def test_hard_delete_is_disabled_to_preserve_transaction_audit_history():
    source = route_source("delete_transaction")

    assert "status_code=405" in source
    assert "Permanent deletion is disabled." in source
    assert "Use POST /{transaction_id}/void" in source

"""Append-only Finance Diary writer.

Entries deliberately store IDs as plain values (no foreign keys), so historical
records survive deletion of the account/transaction they describe.
"""
import json
from datetime import date, datetime
from decimal import Decimal

from app.models import FinanceDiaryEntry


def _json_default(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return str(value)


def record_finance_event(db, *, user_id, event_type, entity_type, entity_id=None, description, snapshot=None):
    entry = FinanceDiaryEntry(
        user_id=int(user_id),
        event_type=str(event_type),
        entity_type=str(entity_type),
        entity_id=None if entity_id is None else str(entity_id),
        description=str(description),
        snapshot_json=json.dumps(snapshot, default=_json_default, sort_keys=True) if snapshot is not None else None,
    )
    db.add(entry)
    return entry

"""Pure, provider-neutral transformations for live derivatives market data.

Provider adapters must validate and normalize their payloads before calling these
functions. No synthetic values are generated here.
"""
from collections import defaultdict
from datetime import datetime, timezone
from math import isfinite
from typing import Any, Iterable


def _number(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be numeric") from None
    if not isfinite(number) or number < 0:
        raise ValueError(f"{field} must be a finite non-negative number")
    return number


def _require_contract(row: Any) -> dict:
    if not isinstance(row, dict):
        raise ValueError("contract must be an object")
    return row


def aggregate_contract_months(rows: Iterable[dict]) -> list[dict]:
    """Group normalized futures contracts by underlying and expiry."""
    grouped = {}
    for raw_row in rows:
        row = _require_contract(raw_row)
        symbol = str(row.get("symbol") or "").strip().upper()
        expiry = str(row.get("expiry") or "").strip()
        if not symbol or not expiry:
            raise ValueError("Each contract requires symbol and expiry")
        # Missing provider values must not silently become fabricated zeroes.
        volume = _number(row.get("volume"), "volume")
        oi = _number(row.get("oi"), "oi")
        key = (symbol, expiry)
        bucket = grouped.setdefault(key, {"symbol": symbol, "expiry": expiry,
                                          "contracts": 0, "volume": 0, "oi": 0})
        bucket["contracts"] += 1
        bucket["volume"] += volume
        bucket["oi"] += oi
    return [grouped[key] for key in sorted(grouped, key=lambda item: (item[0], item[1]))]


def calculate_oi_change(current_oi: Any, previous_oi: Any) -> dict:
    current = _number(current_oi, "current_oi")
    previous = _number(previous_oi, "previous_oi")
    change = current - previous
    return {
        "change": change,
        "change_pct": round(change / previous * 100, 4) if previous else None,
    }


def aggregate_option_oi(rows: Iterable[dict]) -> list[dict]:
    """Aggregate open interest by strike, keeping calls and puts separate."""
    grouped = defaultdict(lambda: {"ce_oi": 0, "pe_oi": 0})
    for raw_row in rows:
        row = _require_contract(raw_row)
        strike = _number(row.get("strike"), "strike")
        side = str(row.get("option_type") or "").strip().upper()
        if side not in {"CE", "PE"}:
            raise ValueError("option_type must be CE or PE")
        oi = _number(row.get("oi"), "oi")
        grouped[strike]["ce_oi" if side == "CE" else "pe_oi"] += oi
    return [
        {"strike": strike, **grouped[strike]}
        for strike in sorted(grouped)
    ]


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("last_tick_at must be an ISO-8601 timestamp") from None
    else:
        raise ValueError("last_tick_at must be a datetime, ISO-8601 string, or null")
    if parsed.tzinfo is None:
        raise ValueError("last_tick_at must include a timezone")
    return parsed.astimezone(timezone.utc)


def feed_status(last_tick_at: Any, *, now: datetime | None = None,
                stale_after_seconds: int = 15) -> dict:
    """Return freshness metadata; a missing tick is never reported as live."""
    if stale_after_seconds < 1:
        raise ValueError("stale_after_seconds must be positive")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must include a timezone")
    current = current.astimezone(timezone.utc)
    tick = _parse_timestamp(last_tick_at)
    if tick is None:
        return {"status": "disconnected", "last_tick_at": None, "age_seconds": None}
    age = max(0.0, (current - tick).total_seconds())
    return {
        "status": "fresh" if age <= stale_after_seconds else "stale",
        "last_tick_at": tick.isoformat(),
        "age_seconds": round(age, 3),
    }

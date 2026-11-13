"""Pure, provider-agnostic calculations for Indian F&O market intelligence.

This module deliberately contains no broker execution, network access, or
provider-specific parsing. Live data adapters must normalize provider payloads
before calling these functions.
"""

from __future__ import annotations

import math
from collections import defaultdict
from numbers import Real
from typing import Any, Iterable


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def classify_futures_position(
    price_change_pct: float | None,
    oi_change_pct: float | None,
) -> str:
    """Classify futures positioning from price and open-interest direction."""
    price = _finite_number(price_change_pct)
    oi = _finite_number(oi_change_pct)
    if price is None or oi is None:
        return "insufficient_data"
    if price == 0 or oi == 0:
        return "neutral"
    if price > 0 and oi > 0:
        return "long_build_up"
    if price < 0 and oi > 0:
        return "short_build_up"
    if price > 0 and oi < 0:
        return "short_covering"
    return "long_unwinding"


def calculate_option_metrics(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Calculate aggregate PCR and highest-OI support/resistance strikes."""
    if not isinstance(rows, (list, tuple)) or not rows:
        raise ValueError("A non-empty option chain is required.")

    by_strike: dict[float, dict[str, float]] = defaultdict(
        lambda: {"call_oi": 0.0, "put_oi": 0.0}
    )
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Every option-chain row must be an object.")
        strike = _finite_number(row.get("strike"))
        call_oi = _finite_number(row.get("call_oi"))
        put_oi = _finite_number(row.get("put_oi"))
        if strike is None or strike <= 0:
            raise ValueError("Option strikes must be positive finite numbers.")
        if call_oi is None or put_oi is None or call_oi < 0 or put_oi < 0:
            raise ValueError("Call and put OI must be non-negative finite numbers.")
        by_strike[strike]["call_oi"] += call_oi
        by_strike[strike]["put_oi"] += put_oi

    total_call_oi = sum(item["call_oi"] for item in by_strike.values())
    total_put_oi = sum(item["put_oi"] for item in by_strike.values())
    resistance = max(
        by_strike,
        key=lambda strike: (by_strike[strike]["call_oi"], -strike),
    )
    support = max(
        by_strike,
        key=lambda strike: (by_strike[strike]["put_oi"], -strike),
    )

    return {
        "total_call_oi": int(total_call_oi) if total_call_oi.is_integer() else total_call_oi,
        "total_put_oi": int(total_put_oi) if total_put_oi.is_integer() else total_put_oi,
        "put_call_ratio": (total_put_oi / total_call_oi) if total_call_oi else None,
        "support_strike": support,
        "resistance_strike": resistance,
        "strike_count": len(by_strike),
    }


def score_conviction(
    *,
    positions_opened: bool,
    spot_agrees: bool,
    last_hour_agrees: bool,
    option_writers_agree: bool,
    sector_agrees: bool,
) -> dict[str, Any]:
    """Score five independently supplied confirmations; this is not a trade signal."""
    checks = {
        "positions_opened": bool(positions_opened),
        "spot_agrees": bool(spot_agrees),
        "last_hour_agrees": bool(last_hour_agrees),
        "option_writers_agree": bool(option_writers_agree),
        "sector_agrees": bool(sector_agrees),
    }
    score = sum(checks.values())
    label = "high" if score >= 4 else "medium" if score == 3 else "low"
    return {
        "score": score,
        "out_of": 5,
        "percentage": score * 20,
        "label": label,
        "checks": checks,
    }


def aggregate_sector_strength(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate sector breadth and mean constituent percentage move."""
    if not isinstance(rows, (list, tuple)):
        raise ValueError("Sector constituents must be a list or tuple.")

    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict):
            continue
        sector = str(row.get("sector") or "").strip()
        change = _finite_number(row.get("change_pct"))
        if not sector or change is None:
            continue
        groups[sector].append(change)

    results = []
    for sector, changes in groups.items():
        advancers = sum(change > 0 for change in changes)
        decliners = sum(change < 0 for change in changes)
        unchanged = len(changes) - advancers - decliners
        results.append({
            "sector": sector,
            "constituents": len(changes),
            "advancers": advancers,
            "decliners": decliners,
            "unchanged": unchanged,
            "average_change_pct": sum(changes) / len(changes),
            "breadth": advancers - decliners,
        })
    return sorted(
        results,
        key=lambda item: (item["average_change_pct"], item["breadth"], item["sector"]),
        reverse=True,
    )

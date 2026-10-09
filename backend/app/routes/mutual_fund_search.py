"""Read-only search for Indian mutual-fund schemes using AMFI's NAV master."""

import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/mutual-funds", tags=["Mutual Funds"])
AMFI_NAV_URL = "https://www.amfiindia.com/spages/NAVAll.txt"


def _classify_plan_option(scheme_name: str, plan_value: str = "", option_value: str = ""):
    """Use AMFI's explicit Plan/Option columns when present, otherwise infer from name."""
    name = (scheme_name or "").strip()
    plan_text = (plan_value or "").strip()
    option_text = (option_value or "").strip()

    combined = f"{plan_text} {name}".casefold()
    if re.search(r"\bdirect\b", combined):
        plan_type = "Direct Plan"
    elif re.search(r"\bregular\b", combined):
        plan_type = "Regular Plan"
    else:
        plan_type = None

    option_combined = f"{option_text} {name}".casefold()
    if "idcw" in option_combined or "dividend" in option_combined:
        option_type = "IDCW"
    elif "growth" in option_combined:
        option_type = "Growth"
    elif "bonus" in option_combined:
        option_type = "Bonus"
    else:
        option_type = None

    return plan_type, option_type


def _parse_amfi_row(line: str):
    """Parse both AMFI's classic 6-column and newer 8-column layouts."""
    columns = [part.strip() for part in line.strip().split(";")]
    if len(columns) < 6 or not columns[0].isdigit():
        return None

    scheme_code = columns[0]
    isin_growth = columns[1] if len(columns) > 1 else ""
    isin_idcw = columns[2] if len(columns) > 2 else ""
    scheme_name = columns[3] if len(columns) > 3 else ""

    # Newer layout: Code; ISIN Growth/Payout; ISIN Reinvestment; Name; Plan; Option; NAV; Date
    # Classic layout: Code; ISIN Growth/Payout; ISIN Reinvestment; Name; NAV; Date
    if len(columns) >= 8:
        plan_value, option_value, nav_text, nav_date = columns[4:8]
    else:
        plan_value, option_value = "", ""
        nav_text, nav_date = columns[4:6]

    if not scheme_name:
        return None

    plan_type, option_type = _classify_plan_option(scheme_name, plan_value, option_value)
    try:
        nav = float(nav_text.replace(",", "")) if nav_text else None
    except ValueError:
        nav = None

    return {
        "scheme_code": scheme_code,
        "symbol": scheme_code,
        "name": scheme_name,
        "scheme_name": scheme_name,
        "plan_type": plan_type,
        "option_type": option_type,
        "isin_growth": isin_growth if isin_growth and isin_growth != "-" else None,
        "isin_idcw": isin_idcw if isin_idcw and isin_idcw != "-" else None,
        "latest_nav": nav,
        "last_price": nav,
        "nav_date": nav_date or None,
        "exchange": "AMFI",
        "instrument_type": "Mutual Fund",
        "source": "AMFI",
    }


@router.get("/search/")
def search_mutual_funds(
    query: str = Query(..., min_length=1, description="Scheme name, scheme code, or ISIN"),
    limit: int = Query(20, ge=1, le=50),
):
    """Search AMFI's current scheme/NAV file; this endpoint does not write to the database."""
    cleaned = query.strip().casefold()
    if not cleaned:
        raise HTTPException(status_code=400, detail="Search query is required.")

    request = Request(
        AMFI_NAV_URL,
        headers={"User-Agent": "FinancialOS/1.0", "Accept": "text/plain,*/*"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=25) as response:
            content = response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Mutual-fund scheme data is temporarily unavailable from AMFI.",
        ) from exc

    results = []
    for line in content.splitlines():
        item = _parse_amfi_row(line)
        if not item:
            continue
        searchable = " ".join(
            str(item.get(key) or "")
            for key in ("scheme_name", "scheme_code", "isin_growth", "isin_idcw", "plan_type", "option_type")
        ).casefold()
        if cleaned not in searchable:
            continue
        results.append(item)
        if len(results) >= limit:
            break

    return {
        "status": "success",
        "engine": "Mutual Fund Scheme Search",
        "query": query.strip(),
        "count": len(results),
        "results": results,
        "source": {"provider": "AMFI", "endpoint": "/spages/NAVAll.txt"},
        "read_only": True,
        "database_write": False,
    }

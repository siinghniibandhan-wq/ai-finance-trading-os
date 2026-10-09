"""Read-only search for Indian mutual-fund schemes using AMFI's NAV master."""

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Query


router = APIRouter(prefix="/api/mutual-funds", tags=["Mutual Funds"])
AMFI_NAV_URL = "https://www.amfiindia.com/spages/NAVAll.txt"


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
        # AMFI rows are semicolon-separated: scheme code;scheme name;ISIN growth;ISIN IDCW;NAV;date
        columns = [part.strip() for part in line.split(";")]
        if len(columns) < 6 or not columns[0].isdigit():
            continue
        scheme_code, scheme_name, isin_growth, isin_idcw, nav_text, nav_date = columns[:6]
        if not scheme_name or cleaned not in " ".join(
            [scheme_name, scheme_code, isin_growth, isin_idcw]
        ).casefold():
            continue
        try:
            nav = float(nav_text.replace(",", ""))
        except (TypeError, ValueError):
            nav = None
        results.append({
            "scheme_code": scheme_code,
            "symbol": scheme_code,
            "name": scheme_name,
            "scheme_name": scheme_name,
            "isin_growth": isin_growth or None,
            "isin_idcw": isin_idcw or None,
            "latest_nav": nav,
            "last_price": nav,
            "nav_date": nav_date or None,
            "exchange": "AMFI",
            "instrument_type": "Mutual Fund",
            "source": "AMFI",
        })
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

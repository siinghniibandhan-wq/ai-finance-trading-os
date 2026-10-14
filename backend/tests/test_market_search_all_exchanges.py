from io import BytesIO

import pytest
from fastapi import HTTPException

from app.routes import market_search


class FakeResponse:
    status = 200

    def __init__(self, body):
        self.body = body.encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


CSV = """instrument_token,exchange_token,tradingsymbol,name,last_price,expiry,strike,tick_size,lot_size,instrument_type,segment,exchange\n101,1,RELIANCE-EQ,Reliance Industries,1400,,,0.05,1,EQ,NSECM,NSE\n202,2,RELIANCE-A,Reliance Industries,1401,,,0.05,1,A,BSECM,BSE\n303,3,RELIANCEPHARMA-EQ,Reliance Pharma,100,,,0.05,1,EQ,NSECM,NSE\n404,4,TCS-EQ,Tata Consultancy Services,3500,,,0.05,1,EQ,NSECM,NSE\n"""


def test_search_all_returns_both_exact_exchange_listings_before_other_matches(monkeypatch):
    monkeypatch.setattr(market_search, "urlopen", lambda *args, **kwargs: FakeResponse(CSV))

    result = market_search.search_market(query="RELIANCE", exchange="ALL", limit=12)

    assert [(item["exchange"], item["symbol"]) for item in result["results"][:2]] == [
        ("NSE", "RELIANCE-EQ"),
        ("BSE", "RELIANCE-A"),
    ]
    assert result["results"][0]["series"] == "EQ"
    assert result["results"][1]["series"] == "A"
    assert result["count"] == 3


def test_search_can_still_filter_to_one_exchange(monkeypatch):
    monkeypatch.setattr(market_search, "urlopen", lambda *args, **kwargs: FakeResponse(CSV))

    result = market_search.search_market(query="RELIANCE", exchange="BSE", limit=12)

    assert result["count"] == 1
    assert result["results"][0]["exchange"] == "BSE"


def test_search_rejects_unknown_exchange(monkeypatch):
    monkeypatch.setattr(market_search, "urlopen", lambda *args, **kwargs: FakeResponse(CSV))

    with pytest.raises(HTTPException) as error:
        market_search.search_market(query="RELIANCE", exchange="MCX", limit=12)

    assert error.value.status_code == 422

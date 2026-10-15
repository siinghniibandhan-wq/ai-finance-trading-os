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


def test_same_security_exchange_pair_stays_together_for_company_prefix(monkeypatch):
    csv = """instrument_token,exchange_token,tradingsymbol,name,last_price,instrument_type,segment,exchange
1,1,HDFCBANK-EQ,HDFC Bank,100,EQ,NSECM,NSE
2,2,HDFCLIFE-EQ,HDFC Life Insurance,200,EQ,NSECM,NSE
3,3,HDFCBANK-A,HDFC Bank,101,A,BSECM,BSE
4,4,HDFCLIFE-A,HDFC Life Insurance,201,A,BSECM,BSE
"""
    monkeypatch.setattr(market_search, "urlopen", lambda *args, **kwargs: FakeResponse(csv))

    result = market_search.search_market(query="HDFC", exchange="ALL", limit=12)

    assert [(item["name"], item["exchange"]) for item in result["results"][:2]] == [
        ("HDFC Bank", "NSE"),
        ("HDFC Bank", "BSE"),
    ]


def test_search_excludes_derivative_segments_and_contracts(monkeypatch):
    csv = """instrument_token,exchange_token,tradingsymbol,name,last_price,expiry,strike,instrument_type,segment,exchange
1,1,RELIANCE-EQ,Reliance Industries,100,,,EQ,NSECM,NSE
2,2,RELIANCE-FUT,Reliance Industries Futures,101,2026-10-29,,FUT,NSEFO,NSEFO
3,3,RELIANCE-2500-CE,Reliance Industries Call,10,2026-10-29,2500,CE,NSEFO,NSEFO
4,4,RELIANCE-BE,Reliance Industries,99,,,BE,BSECM,BSE
"""
    monkeypatch.setattr(market_search, "urlopen", lambda *args, **kwargs: FakeResponse(csv))

    result = market_search.search_market(query="RELIANCE", exchange="ALL", limit=12)

    assert [(item["exchange"], item["symbol"]) for item in result["results"]] == [
        ("NSE", "RELIANCE-EQ"),
        ("BSE", "RELIANCE-BE"),
    ]

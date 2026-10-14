import pytest

from app.routes.investments import build_market_quote_symbol
from app.services.market_price import MarketPriceError


def test_market_quote_symbol_qualifies_bse_listing():
    assert build_market_quote_symbol("RELIANCE", "BSE") == "BSE:RELIANCE"


def test_market_quote_symbol_qualifies_nse_listing():
    assert build_market_quote_symbol("RELIANCE-EQ", "NSE") == "NSE:RELIANCE-EQ"


def test_market_quote_symbol_preserves_matching_existing_exchange_prefix():
    assert build_market_quote_symbol("BSE:RELIANCE", "BSE") == "BSE:RELIANCE"


def test_market_quote_symbol_rejects_exchange_conflict():
    with pytest.raises(MarketPriceError, match="conflicts"):
        build_market_quote_symbol("NSE:RELIANCE", "BSE")


def test_market_quote_symbol_rejects_unsupported_exchange():
    with pytest.raises(MarketPriceError, match="Unsupported instrument exchange"):
        build_market_quote_symbol("RELIANCE", "UNKNOWN")


def test_market_quote_symbol_keeps_legacy_unqualified_symbol_when_exchange_missing():
    assert build_market_quote_symbol("RELIANCE") == "RELIANCE"

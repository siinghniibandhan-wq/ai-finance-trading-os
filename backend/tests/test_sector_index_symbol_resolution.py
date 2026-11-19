import json
from unittest.mock import patch

from app.routes import market_flow, market_indices


def test_two_missing_sector_indices_use_documented_mstock_script_symbols():
    sectors = {item["key"]: item for item in market_flow.SECTOR_UNIVERSES}

    assert sectors["consumer-durables"]["quote_symbol"] == "NIFTYCONSRDURBL"
    assert sectors["financial-services"]["quote_symbol"] == "NIFTYFINSERVICE"
    assert sectors["consumer-durables"]["index_symbol"] == "NIFTY CONSUMER DURABLES"
    assert sectors["financial-services"]["index_symbol"] == "NIFTY FINANCIAL SERVICES"


def test_fetch_index_uses_quote_symbol_but_preserves_display_symbol():
    index = {
        "name": "Consumer Durables",
        "exchange": "NSE",
        "symbol": "NIFTY CONSUMER DURABLES",
        "quote_symbol": "NIFTYCONSRDURBL",
    }
    payload = {
        "status": "success",
        "data": {
            "NSE:NIFTYCONSRDURBL": {
                "last_price": 12345.6,
                "ohlc": {"close": 12200.0},
            }
        },
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps(payload).encode()

    with patch.object(market_indices, "GATEWAY_URL", "http://gateway.test"), patch.object(
        market_indices, "urlopen", return_value=FakeResponse()
    ) as mocked_urlopen:
        result = market_indices.fetch_index(index)

    request = mocked_urlopen.call_args.args[0]
    assert request.full_url.endswith("symbol=NSE%3ANIFTYCONSRDURBL")
    assert result["symbol"] == "NIFTY CONSUMER DURABLES"
    assert result["last_price"] == 12345.6
    assert result["previous_close"] == 12200.0
    assert result["percent_change"] > 0


def test_other_sector_symbols_remain_unchanged():
    sectors = {item["key"]: item for item in market_flow.SECTOR_UNIVERSES}

    assert sectors["auto"]["index_symbol"] == "NIFTY AUTO"
    assert "quote_symbol" not in sectors["auto"]
    assert sectors["it"]["index_symbol"] == "NIFTY IT"
    assert "quote_symbol" not in sectors["it"]


def test_sector_snapshot_passes_canonical_symbols_only_for_the_two_affected_indices(monkeypatch):
    monkeypatch.setattr(market_flow, "_sector_index_cache", {
        "loaded_at": 0.0, "results": [], "errors": [],
    })
    seen = []

    def fake_fetch(index):
        seen.append(dict(index))
        return {
            "name": index["name"],
            "exchange": index["exchange"],
            "symbol": index["symbol"],
            "last_price": 1000,
            "previous_close": 990,
            "change": 10,
            "percent_change": 100 / 99,
            "status": "success",
        }

    monkeypatch.setattr(market_flow, "fetch_index", fake_fetch)
    results, errors = market_flow.fetch_sector_index_snapshots()

    assert errors == []
    assert len(results) == len(market_flow.SECTOR_UNIVERSES)
    by_symbol = {item["symbol"]: item for item in seen}
    assert by_symbol["NIFTY CONSUMER DURABLES"]["quote_symbol"] == "NIFTYCONSRDURBL"
    assert by_symbol["NIFTY FINANCIAL SERVICES"]["quote_symbol"] == "NIFTYFINSERVICE"
    assert "quote_symbol" not in by_symbol["NIFTY AUTO"]
    assert "quote_symbol" not in by_symbol["NIFTY IT"]

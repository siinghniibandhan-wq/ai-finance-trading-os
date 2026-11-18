from app.services import mstock_gateway
from app.routes import market_history, market_search, market_indices, market_movers
from app.services import market_price


def test_all_market_data_adapters_share_the_configured_gateway_url():
    expected = mstock_gateway.MSTOCK_GATEWAY_URL
    assert expected == "http://127.0.0.1:8000"
    assert market_history.MSTOCK_GATEWAY_URL == expected
    assert market_search.MSTOCK_GATEWAY_URL == expected
    assert market_indices.GATEWAY_URL == expected
    assert market_movers.MSTOCK_GATEWAY_URL == expected
    assert market_price.MSTOCK_GATEWAY_URL == expected


def test_gateway_url_has_no_stale_public_ip_fallback():
    assert "54.153.201.74" not in mstock_gateway.MSTOCK_GATEWAY_URL

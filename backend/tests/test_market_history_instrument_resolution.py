from app.routes.market_history import _resolve_instrument_from_csv


def test_resolves_instrument_when_gateway_csv_uses_provider_header_aliases():
    csv_text = (
        "\\ufeffExch,TradingSym,Token,CompanyName\\n"
        "NSECM,RELIANCE-EQ,2885,Reliance Industries Limited\\n"
    )

    assert _resolve_instrument_from_csv(csv_text, "RELIANCE-EQ", "NSE") == (
        "2885",
        "RELIANCE-EQ",
        "Reliance Industries Limited",
    )


def test_instrument_resolution_does_not_match_another_exchange():
    csv_text = (
        "exchange,tradingsymbol,instrument_token,name\\n"
        "BSE,RELIANCE,500325,Reliance Industries Limited\\n"
    )

    assert _resolve_instrument_from_csv(csv_text, "RELIANCE", "NSE") is None


def test_instrument_resolution_requires_a_valid_token():
    csv_text = (
        "exchange,tradingsymbol,instrument_token,name\\n"
        "NSE,RELIANCE,,Reliance Industries Limited\\n"
    )

    assert _resolve_instrument_from_csv(csv_text, "RELIANCE", "NSE") is None


def test_instrument_resolution_rejects_non_numeric_provider_tokens():
    csv_text = (
        "exchange,tradingsymbol,instrument_token,name\\n"
        "NSE,RELIANCE,not-a-token,Reliance Industries Limited\\n"
    )

    assert _resolve_instrument_from_csv(csv_text, "RELIANCE", "NSE") is None

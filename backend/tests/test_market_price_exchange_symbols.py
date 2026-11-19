from app.services.market_price import gateway_quote_symbol


def test_nse_cash_symbol_keeps_legacy_eq_qualification():
    assert gateway_quote_symbol("NSE:RELIANCE") == "NSE:RELIANCE-EQ"


def test_bse_bare_symbol_is_not_given_an_nse_eq_suffix():
    assert gateway_quote_symbol("BSE:ACC") == "BSE:ACC"


def test_bse_exact_script_master_series_is_preserved():
    assert gateway_quote_symbol("BSE:ACC-A") == "BSE:ACC-A"


def test_bse_legacy_synthetic_eq_suffix_is_left_for_gateway_resolution():
    assert gateway_quote_symbol("BSE:ACC-EQ") == "BSE:ACC-EQ"


def test_non_cash_instruments_are_not_modified():
    assert gateway_quote_symbol("NFO:NIFTY26NOVFUT") == "NFO:NIFTY26NOVFUT"


def test_unqualified_symbols_keep_legacy_gateway_default():
    assert gateway_quote_symbol("RELIANCE") == "RELIANCE"

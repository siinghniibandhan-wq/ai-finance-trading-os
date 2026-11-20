import unittest

from app.routes.market_intelligence import (
    parse_corporate_action_rows,
    parse_institutional_rows,
)


class MarketIntelligenceParserTests(unittest.TestCase):
    def test_institutional_rows_normalize_categories_and_keep_valid_net_values(self):
        rows = parse_institutional_rows([
            {"date": "20-Nov-2026", "category": "FII/FPI", "buyValue": "100.50", "sellValue": "80.25", "netValue": "20.25"},
            {"date": "20-Nov-2026", "category": "DII", "buyValue": "70", "sellValue": "90", "netValue": "-20"},
            {"date": "20-Nov-2026", "category": "Other", "buyValue": "10", "sellValue": "5", "netValue": "5"},
            {"date": "20-Nov-2026", "category": "DII", "buyValue": "100", "sellValue": "50", "netValue": "999"},
        ])
        self.assertEqual([row["investor_type"] for row in rows], ["DII", "FII/FPI"])
        self.assertEqual(rows[0]["net_value_crore"], -20.0)
        self.assertEqual(rows[1]["net_value_crore"], 20.25)

    def test_institutional_rows_reject_missing_dates_and_incomplete_values(self):
        rows = parse_institutional_rows([
            {"date": "", "category": "DII", "buyValue": "10", "sellValue": "5", "netValue": "5"},
            {"date": "20-Nov-2026", "category": "FII/FPI", "buyValue": "10", "sellValue": None, "netValue": "5"},
        ])
        self.assertEqual(rows, [])

    def test_corporate_actions_match_exact_symbol_and_parse_dividend_fields(self):
        rows = parse_corporate_action_rows([
            {"symbol": "RELIANCE", "company": "Reliance Industries", "series": "EQ",
             "subject": "Interim Dividend - Rs 7.00 Per Share", "exDate": "28-Nov-2026",
             "recDate": "30-Nov-2026", "faceVal": "10"},
            {"symbol": "RELIANCE1", "subject": "Dividend - Rs 2 Per Share"},
        ], "RELIANCE")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["event_type"], "dividend")
        self.assertEqual(rows[0]["dividend_per_share"], 7.0)
        self.assertEqual(rows[0]["ex_date"], "2026-11-28")
        self.assertEqual(rows[0]["record_date"], "2026-11-30")

    def test_corporate_actions_do_not_infer_dividend_amount(self):
        rows = parse_corporate_action_rows([
            {"symbol": "ABC", "subject": "Final Dividend", "exDate": "2026-12-01"},
        ], "ABC")
        self.assertIsNone(rows[0]["dividend_per_share"])


if __name__ == "__main__":
    unittest.main()

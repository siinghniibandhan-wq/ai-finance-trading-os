# Financial OS — Vibe Trading Phase 1 (based on latest supplied snapshot)

This additive backend update uses the newly supplied `ai-finance-trading-os-main.zip` as its base. It preserves the existing React UI, AWS m.Stock gateway configuration, market-price service, database schema, investment records, broker relationships, and P&L code.

## Included functionality

- `GET /api/vibe-trading/status` — reports Phase 1 capabilities.
- `GET /api/vibe-trading/quote?symbol=RELIANCE` — retrieves a quote via the existing market-price service.
- `POST /api/vibe-trading/quotes` — fetches up to 20 unique symbols concurrently; returns partial results when some symbols fail.
- `POST /api/vibe-trading/research` — retrieves requested quotes concurrently and passes only retrieved quote evidence to the existing Gemini provider.

## Performance controls

- `VIBE_QUOTE_CACHE_TTL_SECONDS` defaults to 2 seconds. Set to `0` to disable caching.
- `VIBE_QUOTE_WORKERS` defaults to 8 and is capped at 8 concurrent quote calls.
- Cache is in-memory per application worker, bounded to 1,000 symbols. It is not shared between multiple workers.
- Cache reduces repeated requests but can return a quote retrieved up to the configured TTL ago.
- The existing market-price service does not expose the provider's original quote timestamp. `retrieved_at` is therefore not represented as proof that a price is real-time.
- Concurrent REST quote calls can increase request load. The concurrency setting should be adjusted to the AWS gateway/provider's allowed rate limits.

## No live execution

This phase is read-only. It does not submit broker orders, write to the database, add migrations, or alter investment records.

## Focused tests

Run from `backend/`:

```bash
PYTHONPATH=. pytest -q tests/test_vibe_trading_fast_quotes.py
```

Tests mock market prices and verify cache and batch behavior. They do not verify live AWS gateway connectivity, provider freshness, or Gemini availability.

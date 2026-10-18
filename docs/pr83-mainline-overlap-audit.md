# PR #83 overlap audit against current main

Audit base: merge base `c6da048416e6501c4af3a5d1f002f0d9e4513729`.
PR #83 head audited: `73329f6dbfeab7d213d074ffff888f1164a3139a`.
Comparison: 20 PR-only commits; 45 commits on current main since the merge base.

## Files changed on current main since the merge base
- `.github/workflows/market-regression-tests.yml`
- `backend/app/models.py`
- `backend/app/routes/broker_orders.py`
- `backend/app/routes/investments.py`
- `backend/tests/test_broker_orders.py`
- `backend/tests/test_investment_portfolio_valuation.py`
- plus frontend/workflow/docs files listed in GitHub compare output.

## PR #83 commits that overlap those mainline-changed files

| PR #83 commit | Message | Overlapping file |
|---|---|---|
| `ba9b304ad623add55f379f3fad9b2b0d66ccb4f4` | Add exchange field for broker fill instrument matching | `backend/app/routes/investments.py` |
| `70b920cc8460d842d85c8bd854cc474db14bc9d3` | Run broker fill reconciliation tests in market CI | `.github/workflows/market-regression-tests.yml` |
| `76fe9a514e465319d8bd736767d5b8e4ed2d94eb` | Align broker order proxy with existing m.Stock gateway contract | `backend/app/routes/broker_orders.py` |
| `914c74095c6837a1f24bef9ee4a83e744b499f2b` | Test translated gateway order payload and client reference mapping | `backend/tests/test_broker_orders.py` |
| `fa27c76a16ff404a96ad4638f7befcdc67b46dd9` | Support configured shared-secret authentication to m.Stock gateway | `backend/app/routes/broker_orders.py` |
| `008a9e68043ffc5ae11ca7d1ce000a756c244df4` | Require HTTPS when sending gateway shared secret | `backend/app/routes/broker_orders.py` |
| `0954da55b7c37cb93047170da18f6231562a57d5` | Test gateway secret requires encrypted HTTPS transport | `backend/tests/test_broker_orders.py` |
| `527e0f2dc8c4d49dedfe8795166e46b8505c7745` | Filter broker order book by authenticated user | `backend/app/routes/broker_orders.py` |
| `1016063b2c2579b64da612c07c0e741b4978a8cf` | Test user-scoped broker order book filtering | `backend/tests/test_broker_orders.py` |

These nine commits require manual reconciliation rather than cherry-picking. In particular, PR #83's older `broker_orders.py` changes must not overwrite the current mainline loopback-only gateway URL, mandatory secret, and durable duplicate-submission reservation.

The other 11 PR #83 commits touch files not listed as changed on main since the merge base. This is a path-level overlap audit; it does not by itself prove semantic compatibility.

The new working branch was created from current `main` and ports a focused reconciliation implementation without cherry-picking PR #83.

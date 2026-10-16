# Financial OS — Tax Module Update Batch

## Files in this batch

1. `frontend/src/App.jsx`
2. `backend/app/routes/itr_ready_tax_report.py`
3. `backend/app/routes/deductions_exempt_income.py`
4. `backend/tests/test_itr_income_classification.py`

## Changes

- Requires the user to select Old or New regime before the Tax Centre loads calculations.
- Keeps existing Money and Invest transaction screens/modules untouched.
- Corrects the ITR report query parameter to `regime` and passes the STT confirmation flag.
- Displays both old-regime and new-regime report estimates side by side after the initial regime selection.
- Shows the existing regime-filtered deduction and exempt-income catalogue, including salary standard-deduction limits in the catalogue for the two supported FYs.
- Adds preliminary ITR-1 / ITR-2 / ITR-3 guidance, tax-credit placeholders, and missing-data disclosure.
- In the tax report aggregation, classifies generic income records using category/description keywords, flags conflicting explicit classifications, and excludes likely loan proceeds from taxable income.
- Does not infer deduction claims from ordinary expenses or silently apply unverified claims.

## Exact replacement paths

- `Tax_App.jsx` → `frontend/src/App.jsx`
- `itr_ready_tax_report.py` → `backend/app/routes/itr_ready_tax_report.py`
- `deductions_exempt_income.py` → `backend/app/routes/deductions_exempt_income.py`
- `test_itr_income_classification.py` → `backend/tests/test_itr_income_classification.py`

## Validation performed

- Python compile check passed for backend app and tests.
- Four regression tests passed for salary keyword classification, loan-disbursement exclusion, explicit-type conflict warning, and dividend classification.
- Deduction catalogue checks passed for Old/New standard deduction display and Section 24(b) catalogue presence.
- Frontend production build was not run because `node_modules` is not present in this environment.

## Important limitations

This is a tax-module improvement batch, not a completed electronic ITR filing integration. Verified deduction evidence, salary gross-up/Form 16 details, house-property schedules, business/profession schedules, TDS/advance-tax records, residential status, and final ITR form eligibility still need dedicated data capture and validation. The displayed report remains provisional until those sources are connected and reconciled. Review current Finance Act rules for the selected FY before filing.


## Tax review confirmations — integration into main

- Added the `tax_review_confirmations` table and registered the `/api/tax-review/` endpoints.
- A tax section is complete only when the user explicitly confirms it and no entries remain pending review.
- The ITR-ready report now uses these section statuses to update the missing-section list; residential status, personal/filing details, and ITR-form eligibility remain required.
- This is a preparatory review workflow, not automated document verification or electronic ITR filing.

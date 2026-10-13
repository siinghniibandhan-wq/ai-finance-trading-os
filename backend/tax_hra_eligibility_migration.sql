-- HRA eligibility confirmations. Legacy records default to false and must be
-- reconfirmed before the tax engine applies an HRA exemption.
ALTER TABLE tax_salary_income_records
    ADD COLUMN IF NOT EXISTS accommodation_owned_by_taxpayer BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE tax_salary_income_records
    ADD COLUMN IF NOT EXISTS rent_actually_paid BOOLEAN NOT NULL DEFAULT FALSE;

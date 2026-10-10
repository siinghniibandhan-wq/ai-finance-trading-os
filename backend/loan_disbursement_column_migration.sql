-- ============================================================
-- FINANCIAL OS
-- MIGRATION: Loan Disbursement Transaction Column
-- ============================================================
--
-- Purpose:
-- Add the missing disbursement_transaction_id column to loans.
--
-- Why:
-- SQLAlchemy's Base.metadata.create_all() does not add new
-- columns to database tables that already exist.
--
-- Safety:
-- 1. Does not delete or recreate tables.
-- 2. Does not delete existing financial records.
-- 3. Allows existing loans to have a NULL transaction link.
-- 4. Can be executed again safely.
--
-- IMPORTANT:
-- Back up the database before applying this migration to
-- another production environment.
-- ============================================================

BEGIN;

-- ============================================================
-- STEP 1: ADD THE MISSING COLUMN
-- ============================================================

ALTER TABLE public.loans
ADD COLUMN IF NOT EXISTS disbursement_transaction_id INTEGER;


-- ============================================================
-- STEP 2: ADD THE FOREIGN KEY
-- Link to the transaction that recorded the loan disbursement.
-- If the linked transaction is deleted, set the link to NULL.
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.loans'::regclass
          AND conname = 'fk_loans_disbursement_transaction'
    ) THEN

        ALTER TABLE public.loans
        ADD CONSTRAINT fk_loans_disbursement_transaction
        FOREIGN KEY (disbursement_transaction_id)
        REFERENCES public.transactions(id)
        ON DELETE SET NULL;

    END IF;
END
$$;


-- ============================================================
-- STEP 3: CREATE A UNIQUE INDEX
-- One transaction can be linked to at most one borrowed loan.
-- PostgreSQL permits multiple NULL values in this unique index.
-- ============================================================

CREATE UNIQUE INDEX IF NOT EXISTS
ix_loans_disbursement_transaction_id
ON public.loans (disbursement_transaction_id);


-- ============================================================
-- STEP 4: COMMIT THE MIGRATION
-- ============================================================

COMMIT;


-- ============================================================
-- STEP 5: VERIFY THE COLUMN
-- Run this query separately after the migration succeeds.
-- ============================================================

SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'loans'
  AND column_name = 'disbursement_transaction_id';

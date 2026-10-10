-- Financial OS: Loan Given / linked movement ledger, Stage 1
-- BACK UP your production database before applying this migration.
-- This migration adds tables only; it does not alter existing records.

CREATE TABLE IF NOT EXISTS loan_receivables (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    borrower_name VARCHAR(150) NOT NULL,
    description VARCHAR(200),
    principal_amount NUMERIC(18,2) NOT NULL CHECK (principal_amount > 0),
    outstanding_principal NUMERIC(18,2) NOT NULL CHECK (outstanding_principal >= 0),
    source_account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    disbursement_transaction_id INTEGER UNIQUE REFERENCES transactions(id) ON DELETE SET NULL,
    interest_rate NUMERIC(7,4),
    start_date DATE NOT NULL,
    due_date DATE,
    reference_number VARCHAR(150),
    notes TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_loan_receivables_id ON loan_receivables(id);
CREATE INDEX IF NOT EXISTS ix_loan_receivables_user_id ON loan_receivables(user_id);
CREATE INDEX IF NOT EXISTS ix_loan_receivables_source_account_id ON loan_receivables(source_account_id);
CREATE INDEX IF NOT EXISTS ix_loan_receivables_disbursement_transaction_id ON loan_receivables(disbursement_transaction_id);
CREATE INDEX IF NOT EXISTS ix_loan_receivables_status ON loan_receivables(status);

CREATE TABLE IF NOT EXISTS loan_movements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    loan_id INTEGER REFERENCES loans(id) ON DELETE CASCADE,
    receivable_id INTEGER REFERENCES loan_receivables(id) ON DELETE CASCADE,
    transaction_id INTEGER NOT NULL UNIQUE REFERENCES transactions(id) ON DELETE RESTRICT,
    movement_type VARCHAR(30) NOT NULL,
    principal_amount NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (principal_amount >= 0),
    interest_amount NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (interest_amount >= 0),
    fee_amount NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (fee_amount >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_loan_movements_one_target CHECK (
      (loan_id IS NOT NULL AND receivable_id IS NULL) OR
      (loan_id IS NULL AND receivable_id IS NOT NULL)
    )
);
CREATE INDEX IF NOT EXISTS ix_loan_movements_id ON loan_movements(id);
CREATE INDEX IF NOT EXISTS ix_loan_movements_user_id ON loan_movements(user_id);
CREATE INDEX IF NOT EXISTS ix_loan_movements_loan_id ON loan_movements(loan_id);
CREATE INDEX IF NOT EXISTS ix_loan_movements_receivable_id ON loan_movements(receivable_id);
CREATE INDEX IF NOT EXISTS ix_loan_movements_transaction_id ON loan_movements(transaction_id);

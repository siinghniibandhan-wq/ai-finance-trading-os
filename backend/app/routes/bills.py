# =====================================================
# DATABASE TABLE
# =====================================================

def ensure_bills_table(db: Session):
    """
    Create the bills table if it does not already exist.
    """

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS bills (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        category_id INTEGER NULL,
        account_id INTEGER NULL,
        amount NUMERIC(14,2) NOT NULL,
        frequency VARCHAR(50) NOT NULL,
        next_due_date DATE NOT NULL,
        status VARCHAR(30) NOT NULL DEFAULT 'active',
        notes TEXT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """

    db.execute(text(create_table_sql))
    db.commit()

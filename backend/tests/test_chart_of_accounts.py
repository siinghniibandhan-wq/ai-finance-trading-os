"""Chart of Accounts catalogue regression tests."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models import ChartOfAccount, User
from app.routes.chart_of_accounts import _seed_defaults, DEFAULT_ACCOUNTS


def _session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_default_chart_of_accounts_is_seeded_idempotently_and_parented():
    db = _session()
    user = User(name="CoA Test", currency="INR")
    db.add(user)
    db.commit()

    _seed_defaults(db, user.id)
    first_count = db.query(ChartOfAccount).filter_by(user_id=user.id).count()
    _seed_defaults(db, user.id)
    second_count = db.query(ChartOfAccount).filter_by(user_id=user.id).count()

    assert first_count == len(DEFAULT_ACCOUNTS)
    assert second_count == first_count
    rows = {row.code: row for row in db.query(ChartOfAccount).filter_by(user_id=user.id).all()}
    assert rows["1110"].parent_id == rows["1100"].id
    assert rows["1210"].parent_id == rows["1200"].id
    assert {row.account_type for row in rows.values()} == {"Asset", "Liability", "Equity", "Income", "Expense"}
    assert rows["2030"].tax_mapping_key is None  # loan proceeds are not mapped as income
    db.close()


def test_chart_of_accounts_are_scoped_per_user():
    db = _session()
    user_a = User(name="User A", currency="INR")
    user_b = User(name="User B", currency="INR")
    db.add_all([user_a, user_b])
    db.commit()
    _seed_defaults(db, user_a.id)
    _seed_defaults(db, user_b.id)

    codes_a = {r.code for r in db.query(ChartOfAccount).filter_by(user_id=user_a.id).all()}
    codes_b = {r.code for r in db.query(ChartOfAccount).filter_by(user_id=user_b.id).all()}
    assert codes_a == codes_b
    assert db.query(ChartOfAccount).filter_by(user_id=user_a.id, code="1000").one().id != db.query(
        ChartOfAccount
    ).filter_by(user_id=user_b.id, code="1000").one().id
    db.close()

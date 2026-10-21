"""User-scoped Chart of Accounts API; codes, not labels, are stable identifiers."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models import ChartOfAccount, User
from app.routes.auth import get_current_user
from app.finance_diary import record_finance_event

router = APIRouter(prefix="/api/chart-of-accounts", tags=["Chart of Accounts"])

# Compact default catalogue. Tax keys are routing hints, not tax conclusions.
DEFAULT_ACCOUNTS = [
    ("1000","Assets","Asset",None,None), ("1010","Cash","Asset","1000",None),
    ("1020","Bank Accounts","Asset","1000",None), ("1100","Receivables","Asset","1000",None),
    ("1110","Customer Receivables","Asset","1100",None), ("1120","Other Receivables","Asset","1100",None),
    ("1200","Investments","Asset","1000",None), ("1210","Mutual Fund Investments","Asset","1200","capital_gains"),
    ("1220","Stocks","Asset","1200","capital_gains"), ("1230","ETFs","Asset","1200","capital_gains"),
    ("1240","Bonds","Asset","1200","capital_gains"), ("2000","Liabilities","Liability",None,None),
    ("2010","Payables","Liability","2000",None), ("2020","Credit Card Payable","Liability","2000",None),
    ("2030","Loans Payable","Liability","2000",None), ("3000","Equity","Equity",None,None),
    ("4000","Income","Income",None,None), ("4010","Salary Income","Income","4000","salary"),
    ("4020","Business and Professional Income","Income","4000","business_profession"),
    ("4030","Rental Income","Income","4000","house_property"), ("4040","Interest Income","Income","4000","other_sources"),
    ("4050","Dividend Income","Income","4000","other_sources"), ("4060","Other Income — Review Required","Income","4000","review_required"),
    ("5000","Expenses","Expense",None,None), ("5010","Living Expenses","Expense","5000",None),
    ("5020","Business Expenses","Expense","5000","business_expense_review"),
    ("5030","Property Expenses","Expense","5000","house_property_expense_review"),
    ("5040","Loan Interest","Expense","5000","interest_purpose_review"), ("5050","Taxes Paid","Expense","5000","tax_payment"),
]

class ChartOfAccountCreate(BaseModel):
    code: str = Field(min_length=2, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=150)
    account_type: str
    parent_id: int | None = None
    tax_mapping_key: str | None = Field(default=None, max_length=100)
    is_enabled: bool = True

class ChartOfAccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    is_enabled: bool | None = None
    tax_mapping_key: str | None = Field(default=None, max_length=100)

def _seed_defaults(db: Session, user_id: int) -> None:
    rows = {r.code:r for r in db.query(ChartOfAccount).filter_by(user_id=user_id).all()}
    changed = False
    for code,name,kind,parent_code,tax_key in DEFAULT_ACCOUNTS:
        row = rows.get(code)
        if row is None:
            row = ChartOfAccount(user_id=user_id, code=code, name=name, account_type=kind,
                is_system=True, is_enabled=True, tax_mapping_key=tax_key)
            db.add(row); db.flush(); rows[code]=row; changed=True
        if parent_code and row.parent_id is None and parent_code in rows:
            row.parent_id=rows[parent_code].id; changed=True
    if changed: db.commit()

def _serialize(r):
    return {"id":r.id,"user_id":r.user_id,"code":r.code,"name":r.name,
        "account_type":r.account_type,"parent_id":r.parent_id,"is_system":r.is_system,
        "is_enabled":r.is_enabled,"tax_mapping_key":r.tax_mapping_key,"created_at":r.created_at}

@router.get("/")
def list_chart_of_accounts(include_disabled: bool = False, db: Session = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    _seed_defaults(db,current_user.id)
    q=db.query(ChartOfAccount).filter_by(user_id=current_user.id)
    if not include_disabled: q=q.filter(ChartOfAccount.is_enabled.is_(True))
    return [_serialize(r) for r in q.order_by(ChartOfAccount.code.asc()).all()]

@router.post("/", status_code=201)
def create_chart_of_account(payload: ChartOfAccountCreate, db: Session = Depends(get_db),
                            current_user: User = Depends(get_current_user)):
    _seed_defaults(db,current_user.id)
    if payload.account_type not in {"Asset","Liability","Equity","Income","Expense"}:
        raise HTTPException(status_code=422,detail="Invalid account_type.")
    if db.query(ChartOfAccount).filter_by(user_id=current_user.id,code=payload.code).first():
        raise HTTPException(status_code=409,detail="Account code already exists.")
    if payload.parent_id is not None and not db.query(ChartOfAccount).filter_by(
        id=payload.parent_id,user_id=current_user.id).first():
        raise HTTPException(status_code=404,detail="Parent account not found for this user.")
    row=ChartOfAccount(user_id=current_user.id,code=payload.code,name=payload.name.strip(),
        account_type=payload.account_type,parent_id=payload.parent_id,is_system=False,
        is_enabled=payload.is_enabled,tax_mapping_key=payload.tax_mapping_key)
    db.add(row)
    db.flush()
    record_finance_event(
        db, user_id=current_user.id, event_type="created",
        entity_type="chart_of_account", entity_id=row.id,
        description=f"Chart of Accounts entry created: {row.code} {row.name}",
        snapshot={"id": row.id, "code": row.code, "name": row.name,
                  "account_type": row.account_type, "parent_id": row.parent_id,
                  "is_enabled": row.is_enabled, "tax_mapping_key": row.tax_mapping_key},
    )
    db.commit()
    db.refresh(row)
    return _serialize(row)

@router.patch("/{account_id}")
def update_chart_of_account(account_id: int,payload: ChartOfAccountUpdate,db: Session=Depends(get_db),
                            current_user: User=Depends(get_current_user)):
    row=db.query(ChartOfAccount).filter_by(id=account_id,user_id=current_user.id).first()
    if not row: raise HTTPException(status_code=404,detail="Chart of Accounts entry not found.")
    before = {"code": row.code, "name": row.name, "account_type": row.account_type,
              "parent_id": row.parent_id, "is_enabled": row.is_enabled,
              "tax_mapping_key": row.tax_mapping_key}
    for key,value in payload.model_dump(exclude_unset=True).items():
        setattr(row,key,value.strip() if key=="name" and value is not None else value)
    after = {"code": row.code, "name": row.name, "account_type": row.account_type,
             "parent_id": row.parent_id, "is_enabled": row.is_enabled,
             "tax_mapping_key": row.tax_mapping_key}
    if before != after:
        record_finance_event(
            db, user_id=current_user.id, event_type="updated",
            entity_type="chart_of_account", entity_id=row.id,
            description=f"Chart of Accounts entry updated: {row.code} {row.name}",
            snapshot={"before": before, "after": after},
        )
    db.commit(); db.refresh(row)
    return _serialize(row)

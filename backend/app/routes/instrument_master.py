"""Canonical instrument master API used by investment records."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.routes.auth import get_current_admin
from app.models import InstrumentMaster

router = APIRouter(prefix="/api/instrument-master", tags=["Instrument Master"])

class InstrumentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    symbol: str | None = None
    exchange: str | None = None
    isin: str | None = None
    asset_class: str = "Other"
    product_type: str = "Other"

@router.get("/")
def search_instruments(q: str = Query("", max_length=120), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    query = db.query(InstrumentMaster)
    if q.strip():
        pattern = f"%{q.strip()}%"
        query = query.filter(InstrumentMaster.name.ilike(pattern) | InstrumentMaster.symbol.ilike(pattern) | InstrumentMaster.isin.ilike(pattern))
    return [dict(id=row.id, canonical_key=row.canonical_key, name=row.name, symbol=row.symbol, exchange=row.exchange, isin=row.isin, asset_class=row.asset_class, product_type=row.product_type) for row in query.order_by(InstrumentMaster.name).limit(limit).all()]

@router.post("/", status_code=201, dependencies=[Depends(get_current_admin)])
def create_instrument(data: InstrumentCreate, db: Session = Depends(get_db)):
    symbol = (data.symbol or "").strip().upper() or None
    exchange = (data.exchange or "").strip().upper() or None
    isin = (data.isin or "").strip().upper() or None
    canonical_key = f"{isin or symbol or data.name.strip().upper()}::{exchange or 'NA'}::{data.product_type.strip().lower()}"
    existing = db.query(InstrumentMaster).filter(InstrumentMaster.canonical_key == canonical_key).first()
    if existing:
        return dict(id=existing.id, canonical_key=existing.canonical_key, name=existing.name, symbol=existing.symbol, exchange=existing.exchange, isin=existing.isin, asset_class=existing.asset_class, product_type=existing.product_type)
    row = InstrumentMaster(canonical_key=canonical_key, name=data.name.strip(), symbol=symbol, exchange=exchange, isin=isin, asset_class=data.asset_class.strip() or "Other", product_type=data.product_type.strip() or "Other")
    db.add(row)
    try:
        db.commit()
    except Exception:
        db.rollback()
        row = db.query(InstrumentMaster).filter(InstrumentMaster.canonical_key == canonical_key).first()
        if not row:
            raise HTTPException(status_code=409, detail="Unable to create canonical instrument record.")
    else:
        db.refresh(row)
    return dict(id=row.id, canonical_key=row.canonical_key, name=row.name, symbol=row.symbol, exchange=row.exchange, isin=row.isin, asset_class=row.asset_class, product_type=row.product_type)

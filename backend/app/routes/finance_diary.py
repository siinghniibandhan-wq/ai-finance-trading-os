"""Read-only Finance Diary API. No edit/delete endpoints are exposed."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models import FinanceDiaryEntry
from app.schemas import FinanceDiaryEntryResponse

router = APIRouter(prefix="/api/finance-diary", tags=["Finance Diary"])

@router.get("/", response_model=list[FinanceDiaryEntryResponse])
def list_finance_diary(
    user_id: int = Query(..., gt=0),
    search: str | None = None,
    event_type: str | None = None,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(FinanceDiaryEntry).filter(FinanceDiaryEntry.user_id == user_id)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            FinanceDiaryEntry.description.ilike(pattern)
            | FinanceDiaryEntry.entity_type.ilike(pattern)
            | FinanceDiaryEntry.entity_id.ilike(pattern)
        )
    if event_type:
        query = query.filter(FinanceDiaryEntry.event_type == event_type)
    return query.order_by(FinanceDiaryEntry.created_at.desc(), FinanceDiaryEntry.id.desc()).offset(offset).limit(limit).all()

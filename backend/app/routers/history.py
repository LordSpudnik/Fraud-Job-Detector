import json

from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models_db import PredictionRecord

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history")
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    records = (
        db.query(PredictionRecord)
        .order_by(desc(PredictionRecord.created_at))
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "title": r.title,
            "model_used": r.model_used,
            "prediction": r.prediction,
            "confidence": r.confidence,
            "top_factors": json.loads(r.top_factors) if r.top_factors else [],
        }
        for r in records
    ]


@router.get("/history/{record_id}")
def get_history_item(record_id: int, db: Session = Depends(get_db)):
    r = db.query(PredictionRecord).filter(PredictionRecord.id == record_id).first()
    if not r:
        return {"error": "not found"}
    return {
        "id": r.id,
        "created_at": r.created_at.isoformat(),
        "title": r.title,
        "company_profile": r.company_profile,
        "description": r.description,
        "requirements": r.requirements,
        "benefits": r.benefits,
        "employment_type": r.employment_type,
        "required_experience": r.required_experience,
        "required_education": r.required_education,
        "industry": r.industry,
        "function": r.function,
        "telecommuting": r.telecommuting,
        "has_company_logo": r.has_company_logo,
        "has_questions": r.has_questions,
        "model_used": r.model_used,
        "prediction": r.prediction,
        "confidence": r.confidence,
        "top_factors": json.loads(r.top_factors) if r.top_factors else [],
    }


@router.delete("/history")
def clear_history(db: Session = Depends(get_db)):
    db.query(PredictionRecord).delete()
    db.commit()
    return {"status": "cleared"}

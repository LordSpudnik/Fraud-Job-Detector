import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml.inference import get_registry
from app.models_db import PredictionRecord
from app.schemas.schemas import JobPostingInput, PredictionResponse, ShapFactor

router = APIRouter(prefix="/api", tags=["prediction"])


@router.post("/predict", response_model=PredictionResponse)
def predict_job(payload: JobPostingInput, db: Session = Depends(get_db)):
    registry = get_registry()
    job = payload.model_dump()
    model_name = job.pop("model_name", None)

    try:
        label, confidence, top_factors = registry.predict(job, model_name=model_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    used_model = model_name or registry.get_best_model_name()

    record = PredictionRecord(
        title=payload.title,
        company_profile=payload.company_profile,
        description=payload.description,
        requirements=payload.requirements,
        benefits=payload.benefits,
        employment_type=payload.employment_type,
        required_experience=payload.required_experience,
        required_education=payload.required_education,
        industry=payload.industry,
        function=payload.function,
        telecommuting=payload.telecommuting,
        has_company_logo=payload.has_company_logo,
        has_questions=payload.has_questions,
        model_used=used_model,
        prediction=label,
        confidence=confidence,
        top_factors=json.dumps(top_factors),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return PredictionResponse(
        prediction=label,
        confidence=confidence,
        model_used=used_model,
        top_factors=[ShapFactor(**f) for f in top_factors],
        record_id=record.id,
    )


@router.get("/models")
def list_models():
    registry = get_registry()
    return {"models": registry.list_models(), "best_model": registry.get_best_model_name()}

from fastapi import APIRouter

from app.ml.inference import get_registry

router = APIRouter(prefix="/api", tags=["models"])


@router.get("/models/compare")
def compare_models():
    registry = get_registry()
    return {
        "best_model": registry.get_best_model_name(),
        "models": registry.get_metrics(),
    }


@router.get("/eda")
def eda_summary():
    registry = get_registry()
    return registry.get_eda_summary()

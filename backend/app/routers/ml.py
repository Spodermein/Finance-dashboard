from fastapi import APIRouter
from ..ml import service as ml_service  # <-- Add this line

router = APIRouter()

@router.get("/ml/health")
def ml_health():
    return {"status": "ml router ok"}

@router.get("/status")
def status():
    return ml_service.get_status()

@router.post("/threshold/{value}")
def set_threshold(value: float):
    ml_service.set_threshold(value)
    return ml_service.get_status()
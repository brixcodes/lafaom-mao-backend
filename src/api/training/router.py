from fastapi import APIRouter
from src.api.training.routers import router as training_router

router = APIRouter(tags=["Training"])

router.include_router(training_router)
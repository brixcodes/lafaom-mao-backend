from typing import Annotated
from fastapi import APIRouter, Depends, Query
from src.api.auth.utils import check_permissions
from src.api.user.models import PermissionEnum, User
from src.api.training.service import TrainingService
from src.api.training.schemas import (
    TrainingCreateInput,
    TrainingUpdateInput,
    TrainingOutSuccess,
    TrainingsPageOutSuccess,
    TrainingFilter,
    TrainingSessionCreateInput,
    TrainingSessionUpdateInput,
    TrainingSessionFilter,
    TrainingSessionOutSuccess,
    TrainingSessionsPageOutSuccess,
)
from src.api.training.dependencies import (
    get_training,
    get_training_session,
)

router = APIRouter()


# Trainings
@router.get("/trainings", response_model=TrainingsPageOutSuccess, tags=["Training"])
async def list_trainings(
    filters: Annotated[TrainingFilter, Query(...)],
    training_service: TrainingService = Depends(),
):
    trainings, total = await training_service.list_trainings(filters)
    return {"data": trainings, "page": filters.page, "number": len(trainings), "total_number": total}


@router.post("/trainings", response_model=TrainingOutSuccess, tags=["Training"])
async def create_training(
    input: TrainingCreateInput,
    current_user: Annotated[User, Depends(check_permissions([PermissionEnum.CAN_CREATE_TRAINING]))],
    training_service: TrainingService = Depends(),
):
    training = await training_service.create_training(input)
    return {"message": "Training created successfully", "data": training}


@router.get("/trainings/{training_id}", response_model=TrainingOutSuccess, tags=["Training"])
async def get_training_route(
    training_id: str,
    training=Depends(get_training),
):
    return {"message": "Training fetched successfully", "data": training}


@router.put("/trainings/{training_id}", response_model=TrainingOutSuccess, tags=["Training"])
async def update_training_route(
    training_id: str,
    input: TrainingUpdateInput,
    current_user: Annotated[User, Depends(check_permissions([PermissionEnum.CAN_UPDATE_TRAINING]))],
    training=Depends(get_training),
    training_service: TrainingService = Depends(),
):
    training = await training_service.update_training(training, input)
    return {"message": "Training updated successfully", "data": training}


@router.delete("/trainings/{training_id}", response_model=TrainingOutSuccess, tags=["Training"])
async def delete_training_route(
    training_id: str,
    current_user: Annotated[User, Depends(check_permissions([PermissionEnum.CAN_DELETE_TRAINING]))],
    training=Depends(get_training),
    training_service: TrainingService = Depends(),
):
    training = await training_service.delete_training(training)
    return {"message": "Training deleted successfully", "data": training}


# Training Sessions
@router.get("/trainings/training-sessions", response_model=TrainingSessionsPageOutSuccess, tags=["Training Session"])
async def list_training_sessions(
    filters: Annotated[TrainingSessionFilter, Query(...)],
    training_service: TrainingService = Depends(),
):
    sessions, total = await training_service.list_training_sessions(filters)
    return {"data": sessions, "page": filters.page, "number": len(sessions), "total_number": total}


@router.post("/trainings/training-sessions", response_model=TrainingSessionOutSuccess, tags=["Training Session"])
async def create_training_session(
    input: TrainingSessionCreateInput,
    current_user: Annotated[User, Depends(check_permissions([PermissionEnum.CAN_CREATE_TRAINING_SESSION]))],
    training_service: TrainingService = Depends(),
):
    session = await training_service.create_training_session(input)
    return {"message": "Training session created successfully", "data": session}


@router.get("/trainings/training-sessions/{session_id}", response_model=TrainingSessionOutSuccess, tags=["Training Session"])
async def get_training_session_route(
    session_id: str,
    training_session=Depends(get_training_session),
):
    return {"message": "Training session fetched successfully", "data": training_session}


@router.put("/trainings/training-sessions/{session_id}", response_model=TrainingSessionOutSuccess, tags=["Training Session"])
async def update_training_session_route(
    session_id: str,
    input: TrainingSessionUpdateInput,
    current_user: Annotated[User, Depends(check_permissions([PermissionEnum.CAN_UPDATE_TRAINING_SESSION]))],
    training_session=Depends(get_training_session),
    training_service: TrainingService = Depends(),
):
    training_session = await training_service.update_training_session(training_session, input)
    return {"message": "Training session updated successfully", "data": training_session}


@router.delete("/trainings/training-sessions/{session_id}", response_model=TrainingSessionOutSuccess, tags=["Training Session"])
async def delete_training_session_route(
    session_id: str,
    current_user: Annotated[User, Depends(check_permissions([PermissionEnum.CAN_DELETE_TRAINING_SESSION]))],
    training_session=Depends(get_training_session),
    training_service: TrainingService = Depends(),
):
    training_session = await training_service.delete_training_session(training_session)
    return {"message": "Training session deleted successfully", "data": training_session}
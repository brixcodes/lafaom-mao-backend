from typing import Annotated
from fastapi import APIRouter, Depends, Query
from src.api.auth.utils import check_permissions, get_current_active_user
from src.api.user.models import PermissionEnum, User
from src.api.training.service import TrainingService
from src.api.training.schemas import (
    ReclamationCreateInput,
    ReclamationAdminUpdateInput,
    ReclamationOutSuccess,
    ReclamationsPageOutSuccess,
    ReclamationFilter,
    ReclamationTypeCreateInput,
    ReclamationTypeOutSuccess,
    ReclamationTypeListOutSuccess,
)
from src.api.training.dependencies import (
    get_reclamation,
    get_user_reclamation,
)

router = APIRouter()

# User Reclamation Endpoints
@router.post("/my-reclamations", response_model=ReclamationOutSuccess, tags=["My Reclamations"])
async def create_my_reclamation(
    input: ReclamationCreateInput,
    current_user: Annotated[User, Depends(get_current_active_user)],
    training_service: TrainingService = Depends(),
):
    """Create a new reclamation by user"""
    # TODO: Validate that application_number belongs to current user
    reclamation = await training_service.create_reclamation(input, user_id=current_user.id)
    return {"message": "Reclamation created successfully", "data": reclamation}


@router.get("/my-reclamations", response_model=ReclamationsPageOutSuccess, tags=["My Reclamations"])
async def list_my_reclamations(
    filters: Annotated[ReclamationFilter, Query(...)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    training_service: TrainingService = Depends(),
):
    """Get paginated list of user's own reclamations"""
    reclamations, total = await training_service.list_user_reclamations(current_user.id, filters)
    return {
        "data": reclamations,
        "page": filters.page,
        "number": len(reclamations),
        "total_number": total,
        "message": "User reclamations fetched successfully"
    }


@router.get("/my-reclamations/{reclamation_id}", response_model=ReclamationOutSuccess, tags=["My Reclamations"])
async def get_my_reclamation(
    reclamation_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    reclamation=Depends(get_user_reclamation),
):
    """Get user's own reclamation by ID"""
    return {"message": "Reclamation fetched successfully", "data": reclamation}


# Admin Reclamation Endpoints
@router.get("/reclamations", response_model=ReclamationsPageOutSuccess, tags=["Admin Reclamations"])
async def list_all_reclamations_admin(
    filters: Annotated[ReclamationFilter, Query(...)],
    current_user: Annotated[User, Depends(check_permissions([PermissionEnum.CAN_VIEW_STUDENT_APPLICATION]))],
    training_service: TrainingService = Depends(),
):
    """Get paginated list of all reclamations (admin)"""
    reclamations, total = await training_service.list_all_reclamations(filters)
    return {
        "data": reclamations,
        "page": filters.page,
        "number": len(reclamations),
        "total_number": total,
        "message": "All reclamations fetched successfully"
    }


@router.get("/reclamations/{reclamation_id}", response_model=ReclamationOutSuccess, tags=["Admin Reclamations"])
async def get_reclamation_admin(
    reclamation_id: int,
    current_user: Annotated[User, Depends(check_permissions([PermissionEnum.CAN_VIEW_STUDENT_APPLICATION]))],
    reclamation=Depends(get_reclamation),
):
    """Get reclamation by ID (admin)"""
    return {"message": "Reclamation fetched successfully", "data": reclamation}


@router.put("/reclamations/{reclamation_id}/status", response_model=ReclamationOutSuccess, tags=["Admin Reclamations"])
async def update_reclamation_status(
    reclamation_id: int,
    input: ReclamationAdminUpdateInput,
    current_user: Annotated[User, Depends(check_permissions([PermissionEnum.CAN_CHANGE_STUDENT_APPLICATION_STATUS]))],
    reclamation=Depends(get_reclamation),
    training_service: TrainingService = Depends(),
):
    """Update reclamation status and assign admin (admin)"""
    reclamation = await training_service.update_reclamation_status(reclamation, input)
    return {"message": "Reclamation status updated successfully", "data": reclamation}


@router.delete("/reclamations/{reclamation_id}", response_model=ReclamationOutSuccess, tags=["Admin Reclamations"])
async def delete_reclamation_admin(
    reclamation_id: int,
    current_user: Annotated[User, Depends(check_permissions([PermissionEnum.CAN_DELETE_STUDENT_ATTACHMENT]))],
    reclamation=Depends(get_reclamation),
    training_service: TrainingService = Depends(),
):
    """Delete reclamation (admin)"""
    reclamation = await training_service.delete_reclamation(reclamation)
    return {"message": "Reclamation deleted successfully", "data": reclamation}


# Reclamation Types Endpoints
@router.get("/reclamation-types/active/all", response_model=ReclamationTypeListOutSuccess, tags=["Reclamation Types"])
async def get_active_reclamation_types(
    training_service: TrainingService = Depends(),
):
    """Get all active reclamation types for dropdown lists"""
    types = await training_service.get_all_reclamation_types()
    return {"data": types, "message": "Active reclamation types fetched successfully"}


@router.post("/reclamation-types", response_model=ReclamationTypeOutSuccess, tags=["Reclamation Types"])
async def create_reclamation_type(
    input: ReclamationTypeCreateInput,
    current_user: Annotated[User, Depends(check_permissions([PermissionEnum.CAN_CREATE_TRAINING]))],
    training_service: TrainingService = Depends(),
):
    """Create a new reclamation type (admin)"""
    reclamation_type = await training_service.create_reclamation_type(input)
    return {"message": "Reclamation type created successfully", "data": reclamation_type}
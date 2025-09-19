from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from src.api.auth.utils import check_permissions, get_current_active_user
from src.api.payments.schemas import InitPaymentOutSuccess
from src.api.user.models import PermissionEnum, User
from src.helper.schemas import BaseOutFail, ErrorMessage
from src.api.training.service import TrainingService
from src.api.training.schemas import (
    StudentApplicationFilter,
    StudentApplicationsPageOutSuccess,
    StudentAttachmentInput,
    StudentApplicationCreateInput,
    StudentApplicationSubmitInput,
    StudentApplicationOutSuccess,
    StudentAttachmentOutSuccess,
    StudentAttachmentListOutSuccess,
)

router = APIRouter()

@router.get("/trainings/student-applications", response_model=StudentApplicationsPageOutSuccess, tags=["Student Application"])
async def list_student_applications_admin(
    input: Annotated[StudentApplicationFilter, Query(...)],
    current_user: Annotated[User, Depends(check_permissions([PermissionEnum.CAN_VIEW_STUDENT_APPLICATION]))],
    training_service: TrainingService = Depends(),
):
    applications, total = await training_service.get_student_application(filters=input, user_id=None)
    
    return {"data": applications, "page": input.page, "number": len(applications), "total_number": total}


@router.get("/trainings/student-applications/{application_id}", response_model=StudentApplicationOutSuccess, tags=["Student Application"])
async def get_student_application_admin(
    application_id: int,
    current_user: Annotated[User, Depends(check_permissions([PermissionEnum.CAN_VIEW_STUDENT_APPLICATION]))],
    training_service: TrainingService = Depends(),
):
    full_application = await training_service.get_full_student_application_by_id(application_id, user_id=None)
    if full_application is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                message=ErrorMessage.STUDENT_APPLICATION_NOT_FOUND.description,
                error_code=ErrorMessage.STUDENT_APPLICATION_NOT_FOUND.value,
            ).model_dump(),
        )
    return {"message": "Student application fetched successfully", "data": full_application}



@router.get("/trainings/student-applications/{application_id}/attachments", response_model=StudentAttachmentListOutSuccess, tags=["Student Attachment"])
async def list_student_attachments(
    application_id: int,
    current_user: Annotated[User, Depends(check_permissions([PermissionEnum.CAN_VIEW_STUDENT_APPLICATION]))],
    training_service: TrainingService = Depends(),
):
    attachments = await training_service.list_attachments_by_application(application_id, user_id=None)
    return {"message": "Attachments fetched successfully", "data": attachments}




# Student Applications
@router.post("/trainings/student-applications", response_model=StudentApplicationOutSuccess, tags=["My Student Application"])
async def create_student_application(
    input: StudentApplicationCreateInput,
    training_service: TrainingService = Depends(),
):
    application = await training_service.start_student_application(input)
    return {"message": "Student application created successfully", "data": application}

@router.get("/trainings/my-student-applications", response_model=StudentApplicationsPageOutSuccess, tags=["My Student Application"])
async def list_my_student_applications(
    input:   Annotated[StudentApplicationFilter, Query(...)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    training_service: TrainingService = Depends(),
):
    applications, total = await training_service.get_student_application(filters=input, user_id=current_user.id)
    
    return {"data": applications, "page": input.page, "number": len(applications), "total_number": total}

@router.get("/trainings/my-student-applications/{application_id}", response_model=StudentApplicationOutSuccess, tags=["My Student Application"])
async def get_my_student_application(
    application_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    training_service: TrainingService = Depends(),
):
    full_application = await training_service.get_full_student_application_by_id(application_id=application_id,user_id = current_user.id)
    if full_application is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                message=ErrorMessage.STUDENT_APPLICATION_NOT_FOUND.description,
                error_code=ErrorMessage.STUDENT_APPLICATION_NOT_FOUND.value,
            ).model_dump(),
        )
    return {"message": "Student application fetched successfully", "data": full_application}

@router.delete("/trainings/my-student-applications/{application_id}", response_model=StudentApplicationOutSuccess, tags=["My Student Application"])
async def delete_my_student_application(
    application_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    training_service: TrainingService = Depends(),
):
    full_application = await training_service.get_full_student_application_by_id(application_id=application_id,user_id = current_user.id)
    if full_application is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                message=ErrorMessage.STUDENT_APPLICATION_NOT_FOUND.description,
                error_code=ErrorMessage.STUDENT_APPLICATION_NOT_FOUND.value,
            ).model_dump(),
        )
    
    await training_service.delete_student_application(full_application)
    
    return {"message": "Student application fetched successfully", "data": full_application}

# Student Attachments
@router.post("/trainings/my-student-applications/{application_id}/attachments", response_model=StudentAttachmentOutSuccess, tags=["My Student Attachment"])
async def create_student_attachment(
    application_id: int,
    input : StudentAttachmentInput,
    current_user: Annotated[User, Depends(get_current_active_user)],
    training_service: TrainingService = Depends(),
):
    application = await training_service.get_student_application_by_id(application_id)
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                message=ErrorMessage.STUDENT_APPLICATION_NOT_FOUND.description,
                error_code=ErrorMessage.STUDENT_APPLICATION_NOT_FOUND.value,
            ).model_dump(),
        )
    attachment = await training_service.create_student_attachment(user_id= current_user.id, application_id=application_id, input = input)
    return {"message": "Attachment created successfully", "data": attachment}

@router.delete("/trainings/my-student-attachments/{attachment_id}", response_model=StudentAttachmentOutSuccess, tags=["My Student Attachment"])
async def delete_student_attachment(
    attachment_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    training_service: TrainingService = Depends(),
):
    attachment = await training_service.get_student_attachment_by_id(attachment_id, user_id=current_user.id)
    if attachment is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                message=ErrorMessage.STUDENT_ATTACHMENT_NOT_FOUND.description,
                error_code=ErrorMessage.STUDENT_ATTACHMENT_NOT_FOUND.value,
            ).model_dump(),
        )
    attachment = await training_service.delete_student_attachment(attachment)
    return {"message": "Attachment deleted successfully", "data": attachment}


@router.post("/trainings/my-student-applications/submit", response_model=InitPaymentOutSuccess, tags=["Student Application"])
async def submit_student_application(
    input: StudentApplicationSubmitInput,
    current_user: Annotated[User, Depends(get_current_active_user)],
    training_service: TrainingService = Depends(),
):
    application = await training_service.get_student_application_by_id(input.application_id)
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                message=ErrorMessage.STUDENT_APPLICATION_NOT_FOUND.description,
                error_code=ErrorMessage.STUDENT_APPLICATION_NOT_FOUND.value,
            ).model_dump(),
        )
        
    application.target_session_id = input.target_session_id
    payment = await training_service.submit_student_application(application)
    if payment["message"] == "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                message=ErrorMessage.PAYMENT_INITIATION_FAILED.description,
                error_code=ErrorMessage.PAYMENT_INITIATION_FAILED.value,
            ).model_dump(),
        )
    return {"message": "Application submitted successfully", "data": {"payment": payment}}
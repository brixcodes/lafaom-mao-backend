from datetime import datetime
from typing import List, Optional, Literal
from fastapi import UploadFile
from pydantic import BaseModel, Field
from src.helper.schemas import BaseOutPage, BaseOutSuccess
from src.api.training.models import ApplicationStatusEnum
from .training import TrainingOut, TrainingSessionOut

class StudentApplicationFilter(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1)
    search: Optional[str] = None
    training_id: Optional[str] = None
    training_session_id: Optional[str] = None
    is_paid: Optional[bool] = True
    status: Optional[str] = None
    order_by: Literal["created_at"] = "created_at"
    asc: Literal["asc", "desc"] = "asc"

# Student Application and Attachments
class StudentAttachmentInput(BaseModel):
    name: str
    file: UploadFile

class StudentAttachmentOut(BaseModel):
    id: int
    application_id: int
    document_type: str
    file_path: str
    created_at: datetime
    updated_at: datetime

class StudentApplicationCreateInput(BaseModel):
    email: str
    target_session_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    country_code: Optional[str] = None
    attachments: Optional[List[str]] = None

class StudentApplicationUpdateInput(BaseModel):
    status: Optional[ApplicationStatusEnum] = None
    refusal_reason: Optional[str] = None

class StudentApplicationSubmitInput(BaseModel):
    application_id: int
    target_session_id: str

class StudentApplicationOut(BaseModel):
    id: int
    user_id: str
    training_id: str
    target_session_id: str
    application_number: str
    status: str
    refusal_reason: Optional[str]
    registration_fee: Optional[float]
    training_fee: Optional[float]
    currency: str
    training_title: str
    training_session_start_date: str
    training_session_end_date: str
    user_email: str
    user_first_name: str
    user_last_name: str

    created_at: datetime
    updated_at: datetime

class StudentApplicationFullOut(BaseModel):
    id: int
    user_id: str
    training_id: str
    target_session_id: str
    application_number: str
    status: str
    refusal_reason: Optional[str]
    registration_fee: Optional[float]
    training_fee: Optional[float]
    currency: str
    created_at: datetime
    updated_at: datetime
    
    training: Optional[TrainingOut] = None
    training_session: Optional[TrainingSessionOut] = None
    # user: Optional[UserOut] = None  # Import from system schemas if needed

# Success Response Schemas
class StudentApplicationOutSuccess(BaseOutSuccess):
    data: StudentApplicationFullOut

class StudentApplicationsPageOutSuccess(BaseOutPage):
    data: List[StudentApplicationOut]

class StudentAttachmentOutSuccess(BaseOutSuccess):
    data: StudentAttachmentOut

class StudentAttachmentListOutSuccess(BaseOutSuccess):
    data: List[StudentAttachmentOut]
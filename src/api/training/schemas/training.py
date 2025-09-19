from datetime import date, datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from src.helper.schemas import BaseOutPage, BaseOutSuccess

class StrengthInput(BaseModel):
    image: str
    content: str
    
class BenefitInput(BaseModel):
    image: str
    content: str
    url: str

# Training Schemas
class TrainingCreateInput(BaseModel):
    title: str
    status: Optional[str] = None
    duration: int = 0
    duration_unit: str
    specialty_id: int
    info_sheet: Optional[str] = None
    training_type: str
    presentation: Optional[str] = ""
    benefits: Optional[List[BenefitInput]] = None
    strengths: Optional[List[StrengthInput]] = None
    target_skills: Optional[str] = ""
    program: Optional[str] = ""
    target_audience: Optional[str] = ""
    prerequisites: Optional[str] = None
    enrollment: Optional[str] = ""

class TrainingUpdateInput(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    duration: Optional[int] = None
    duration_unit: Optional[str] = None
    specialty_id: Optional[int] = None
    info_sheet: Optional[str] = None
    training_type: Optional[str] = None
    presentation: Optional[str] = None
    benefits: Optional[List[dict]] = None
    strengths: Optional[List[dict]] = None
    target_skills: Optional[str] = None
    program: Optional[str] = None
    target_audience: Optional[str] = None
    prerequisites: Optional[str] = None
    enrollment: Optional[str] = None

class TrainingOut(BaseModel):
    id: str
    title: str
    status: str
    duration: int
    duration_unit: str
    specialty_id: int
    info_sheet: Optional[str]
    training_type: str
    presentation: str
    benefits: Optional[List[dict]]
    strengths: Optional[List[dict]]
    target_skills: str
    program: str
    target_audience: str
    prerequisites: Optional[str]
    enrollment: str
    created_at: datetime
    updated_at: datetime

class TrainingFilter(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1)
    search: Optional[str] = None
    status: Optional[str] = None
    specialty_id: Optional[int] = None
    order_by: Literal["created_at", "title"] = "created_at"
    asc: Literal["asc", "desc"] = "asc"

# Training Session Schemas
class TrainingSessionCreateInput(BaseModel):
    training_id: str
    center_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    registration_deadline: date
    available_slots: Optional[int] = None
    status: Optional[str] = None
    registration_fee: Optional[float] = None
    training_fee: Optional[float] = None
    currency: str = "EUR"

class TrainingSessionUpdateInput(BaseModel):
    center_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    registration_deadline: Optional[date] = None
    available_slots: Optional[int] = None
    status: Optional[str] = None
    registration_fee: Optional[float] = None
    training_fee: Optional[float] = None
    currency: Optional[str] = None

class TrainingSessionOut(BaseModel):
    id: str
    training_id: str
    center_id: Optional[int]
    start_date: Optional[date]
    end_date: Optional[date]
    registration_deadline: date
    available_slots: Optional[int]
    status: str
    registration_fee: Optional[float]
    training_fee: Optional[float]
    currency: str
    created_at: datetime
    updated_at: datetime

class TrainingSessionFilter(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1)
    training_id: Optional[str] = None
    center_id: Optional[int] = None
    status: Optional[str] = None
    order_by: Literal["created_at", "registration_deadline", "start_date"] = "created_at"
    asc: Literal["asc", "desc"] = "asc"

# Success Response Schemas
class TrainingOutSuccess(BaseOutSuccess):
    data: TrainingOut

class TrainingsPageOutSuccess(BaseOutPage):
    data: List[TrainingOut]

class TrainingSessionOutSuccess(BaseOutSuccess):
    data: TrainingSessionOut

class TrainingSessionsPageOutSuccess(BaseOutPage):
    data: List[TrainingSessionOut]
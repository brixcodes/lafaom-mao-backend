
from sqlmodel import  Field,Relationship
from datetime import date
from src.api.system.models import TrainingCenter
from src.helper.model import CustomBaseUUIDModel,CustomBaseModel
from typing import Dict, List, Optional
from enum import Enum
from  datetime import datetime
from sqlalchemy import JSON



class TrainingTypeEnum(str, Enum):
    ON_SITE = "On-Site"
    OFF_SITE = "Off-Site"


class TrainingStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class DurationEnum(str,Enum):
    MONTHS = "MONTHS"
    YEARS = "YEARS"
    DAYS = "DAYS"
    HOURS = "HOURS"

class Specialty(CustomBaseModel,table=True):
    name: str
    description: Optional[str] = Field(default="")

class Training(CustomBaseUUIDModel,table=True):
    __tablename__ = "trainings"
    
    
    title: str 
    status: str = Field(default=TrainingStatus.ACTIVE)
    
    duration: int = Field(default=0)
    duration_unit: str = Field(default=DurationEnum.HOURS)
    
    specialty_id: int = Field(foreign_key="specialty.id")
    info_sheet: Optional[str] = Field(default=None, max_length=255) #lien vers la fiche d'info
    training_type : str= Field(default=TrainingTypeEnum.ON_SITE)
    presentation: str = Field(default="", description="Context, challenges, and overall vision of the training")
    benefits: Optional[List[Dict[str,str]]] = Field(default=None, sa_column=Field(default=None, sa_column_kwargs={"type_": JSON}).sa_column)  # JSON
    strengths: Optional[List[Dict[str,str]]]  = Field(default=None, sa_column=Field(default=None, sa_column_kwargs={"type_": JSON}).sa_column)     # JSON array
    target_skills: str = Field(default="", description="Skills and know-how to be acquired")
    program: str = Field(default="", description="Detailed content and structure of the training")
    target_audience: str = Field(default="", description="Intended audience and prerequisites")
    prerequisites: Optional[str] = Field(default=None)
    enrollment: str = Field(default="", description="Enrollment methods, duration, pace")


class TrainingSessionStatusEnum(str, Enum):
    
    OPEN_FOR_REGISTRATION = "OPEN_FOR_REGISTRATION"
    CLOSE_FOR_REGISTRATION = "CLOSE_FOR_REGISTRATION"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"


class TrainingSession(CustomBaseUUIDModel, table=True):
    __tablename__ = "training_sessions"

    training_id: str = Field(foreign_key="trainings.id", nullable=False)
    center_id: Optional[int] = Field(foreign_key="training_centers.id", nullable=True)

    start_date: Optional[date] = Field(default=None)
    end_date: Optional[date] = Field(default=None)
    registration_deadline: date 
    available_slots: Optional[int] = Field(default=None, description="Number of available places")

    status: str = Field(default=TrainingSessionStatusEnum.OPEN_FOR_REGISTRATION, nullable=False)

    registration_fee: Optional[float] = Field(default=None, sa_column_kwargs={"precision": 12, "scale": 2})
    training_fee: Optional[float] = Field(default=None, sa_column_kwargs={"precision": 12, "scale": 2})
    currency : str = Field(default="EUR")
    
    
    # Relationships
    training: Optional[Training] = Relationship()
    center: Optional["TrainingCenter"] = Relationship()


class ApplicationStatusEnum(str, Enum):
    RECEIVED = "RECEIVED"
    REFUSED = "REFUSED"
    APPROVED = "APPROVED"

class StudentApplication(CustomBaseModel, table=True):
    __tablename__ = "student_applications"
    
    user_id: str = Field(foreign_key="users.id", nullable=False)
    training_id: str = Field(foreign_key="trainings.id")
    application_number: str = Field(default=None, max_length=50, index=True, unique=True)
    status: str = Field(default=ApplicationStatusEnum.RECEIVED)
    refusal_reason: Optional[str] = Field(default=None)
    registration_fee: float = Field(default=None, sa_column_kwargs={"precision": 12, "scale": 2})
    training_fee: float = Field(default=None, sa_column_kwargs={"precision": 12, "scale": 2})
    
    installment_percentage: List[float] = Field(default=None, sa_column=Field(default=None, sa_column_kwargs={"type_": JSON}).sa_column) 
    
    training: Training = Relationship()
    
    attachments: List["StudentAttachment"] = Relationship( sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class StudentAttachment(CustomBaseModel, table=True):
    __tablename__ = "student_attachments"

    application_id: int = Field(foreign_key="student_applications.id", nullable=False)
    document_type: str = Field( max_length=100)
    file_path: str = Field(max_length=255)
    upload_date: Optional[datetime] = Field(default=None)
    

class ReclamationStatusEnum(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"

class ReclamationType(CustomBaseModel,table=True):
    __tablename__ = "reclamation_types"
    name : str
    description : Optional[str]= Field(default=None)

class Reclamation(CustomBaseModel, table=True):
    __tablename__ = "reclamations"
    
    admin_id: Optional[str] = Field(foreign_key="users.id", nullable=True)
    reclamation_number: str = Field( max_length=50, index=True, unique=True)
    subject: str = Field( max_length=255)
    reclamation_type: int = Field(foreign_key="reclamation_types.id", nullable=False)
    status: ReclamationStatusEnum = Field(default=ReclamationStatusEnum.NEW)
    description: str = Field(default="")
    closure_date: Optional[datetime] = Field(default=None)
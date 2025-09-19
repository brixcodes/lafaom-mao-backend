from sqlmodel import Field, Relationship
from datetime import date
from src.helper.model import CustomBaseUUIDModel, CustomBaseModel
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime
from sqlalchemy import Column, JSON, Numeric

class TrainingTypeEnum(str, Enum):
    ON_SITE = "On-Site"
    OFF_SITE = "Off-Site"

class TrainingStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class DurationEnum(str, Enum):
    MONTHS = "MONTHS"
    YEARS = "YEARS"
    DAYS = "DAYS"
    HOURS = "HOURS"

class TrainingSessionStatusEnum(str, Enum):
    OPEN_FOR_REGISTRATION = "OPEN_FOR_REGISTRATION"
    CLOSE_FOR_REGISTRATION = "CLOSE_FOR_REGISTRATION"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"

class Training(CustomBaseUUIDModel, table=True):
    __tablename__ = "trainings"
    
    title: str 
    status: str = Field(default=TrainingStatus.ACTIVE)
    
    duration: int = Field(default=0)
    duration_unit: str = Field(default=DurationEnum.HOURS)
    
    specialty_id: int = Field(foreign_key="specialties.id")
    info_sheet: Optional[str] = Field(default=None, max_length=255)  # lien vers la fiche d'info
    training_type: str = Field(default=TrainingTypeEnum.ON_SITE)
    presentation: str = Field(default="", description="Context, challenges, and overall vision of the training")
    
    # JSON columns
    benefits: Optional[List[Dict[str, str]]] = Field(default=None, sa_column=Column(JSON))
    strengths: Optional[List[Dict[str, str]]] = Field(default=None, sa_column=Column(JSON))
    
    target_skills: str = Field(default="", description="Skills and know-how to be acquired")
    program: str = Field(default="", description="Detailed content and structure of the training")
    target_audience: str = Field(default="", description="Intended audience and prerequisites")
    prerequisites: Optional[str] = Field(default=None)
    enrollment: str = Field(default="", description="Enrollment methods, duration, pace")

class TrainingSession(CustomBaseUUIDModel, table=True):
    __tablename__ = "training_sessions"

    training_id: str = Field(foreign_key="trainings.id", nullable=False)
    center_id: Optional[int] = Field(foreign_key="organization_centers.id", nullable=True)

    start_date: Optional[date] = Field(default=None)
    end_date: Optional[date] = Field(default=None)
    registration_deadline: date 
    available_slots: Optional[int] = Field(default=None, description="Number of available places")

    status: str = Field(default=TrainingSessionStatusEnum.OPEN_FOR_REGISTRATION, nullable=False)

    registration_fee: Optional[float] = Field(default=None, sa_column=Column(Numeric(12, 2)))
    training_fee: Optional[float] = Field(default=None, sa_column=Column(Numeric(12, 2)))
    
    currency: str = Field(default="EUR")
    
    required_attachments: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    installment_percentage: Optional[List[float]] = Field(default=None, sa_column=Column(JSON))
    
    moodle_course_id: Optional[int] = Field(default=None, description="Linked Moodle course id")
    
    # Relationships
    training: Optional[Training] = Relationship()

class TrainingSessionParticipant(CustomBaseModel, table=True):
    __tablename__ = "training_session_participants"

    session_id: str = Field(foreign_key="training_sessions.id", nullable=False)
    user_id: str = Field(foreign_key="users.id", nullable=False)
    joined_at: Optional[datetime] = Field(default=None)
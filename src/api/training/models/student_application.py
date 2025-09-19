from sqlmodel import Field, Relationship
from src.helper.model import CustomBaseModel
from typing import List, Optional
from enum import Enum
from datetime import datetime
from sqlalchemy import Column, JSON, Numeric

class ApplicationStatusEnum(str, Enum):
    RECEIVED = "RECEIVED"
    REFUSED = "REFUSED"
    APPROVED = "APPROVED"

class StudentApplication(CustomBaseModel, table=True):
    __tablename__ = "student_applications"
    
    user_id: str = Field(foreign_key="users.id", nullable=False)
    training_id: str = Field(foreign_key="trainings.id")
    target_session_id: str = Field(foreign_key="training_sessions.id")
    application_number: str = Field(default=None, max_length=50, index=True, unique=True)
    status: str = Field(default=ApplicationStatusEnum.RECEIVED)
    refusal_reason: Optional[str] = Field(default=None)
    registration_fee: Optional[float] = Field(default=None, sa_column=Column(Numeric(12, 2)))
    training_fee: Optional[float] = Field(default=None, sa_column=Column(Numeric(12, 2)))
    currency: str = Field(default="EUR")
    installment_percentage: Optional[List[float]] = Field(default=None, sa_column=Column(JSON))
    
    # Import these at runtime to avoid circular imports
    # training: Training = Relationship()
    # training_session: TrainingSession = Relationship()
    # user: User = Relationship()
    
    attachments: List["StudentAttachment"] = Relationship(sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class StudentAttachment(CustomBaseModel, table=True):
    __tablename__ = "student_attachments"

    application_id: int = Field(foreign_key="student_applications.id", nullable=False)
    document_type: str = Field(max_length=100)
    file_path: str = Field(max_length=255)
    upload_date: Optional[datetime] = Field(default=None)
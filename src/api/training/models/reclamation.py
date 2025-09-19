from sqlmodel import Field
from src.helper.model import CustomBaseModel
from typing import Optional
from enum import Enum
from datetime import datetime

class ReclamationStatusEnum(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"

class ReclamationPriorityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class ReclamationType(CustomBaseModel, table=True):
    __tablename__ = "reclamation_types"
    name: str
    description: Optional[str] = Field(default=None)

class Reclamation(CustomBaseModel, table=True):
    __tablename__ = "reclamations"
    
    admin_id: Optional[str] = Field(foreign_key="users.id", nullable=True)
    reclamation_number: str = Field(max_length=50, index=True, unique=True)
    application_number: str = Field(max_length=50, index=True)
    subject: str = Field(max_length=255)
    reclamation_type: int = Field(foreign_key="reclamation_types.id", nullable=False)
    priority: str = Field(default=ReclamationPriorityEnum.LOW, max_length=10)
    status: str = Field(max_length=10, default=ReclamationStatusEnum.NEW)
    description: str = Field(default="")
    closure_date: Optional[datetime] = Field(default=None)
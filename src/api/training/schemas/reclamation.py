from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from src.helper.schemas import BaseOutPage, BaseOutSuccess
from src.api.training.models import ReclamationStatusEnum, ReclamationPriorityEnum

# Reclamation Schemas
class ReclamationCreateInput(BaseModel):
    application_number: str
    subject: str
    reclamation_type: int
    priority: ReclamationPriorityEnum = ReclamationPriorityEnum.LOW
    description: str

class ReclamationUpdateStatusInput(BaseModel):
    status: ReclamationStatusEnum
    admin_id: Optional[str] = None

class ReclamationAdminUpdateInput(BaseModel):
    status: Optional[ReclamationStatusEnum] = None
    admin_id: Optional[str] = None
    priority: Optional[ReclamationPriorityEnum] = None
    description: Optional[str] = None

class ReclamationOut(BaseModel):
    id: int
    admin_id: Optional[str]
    reclamation_number: str
    application_number: str
    subject: str
    reclamation_type: int
    priority: str
    status: str
    description: str
    closure_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class ReclamationFullOut(BaseModel):
    id: int
    admin_id: Optional[str]
    reclamation_number: str
    application_number: str
    subject: str
    reclamation_type: int
    priority: str
    status: str
    description: str
    closure_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Relationships (optional for full details)
    admin_name: Optional[str] = None
    reclamation_type_name: Optional[str] = None

class ReclamationFilter(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1)
    search: Optional[str] = None
    status: Optional[ReclamationStatusEnum] = None
    priority: Optional[ReclamationPriorityEnum] = None
    reclamation_type: Optional[int] = None
    admin_id: Optional[str] = None
    application_number: Optional[str] = None
    order_by: Literal["created_at", "subject", "priority"] = "created_at"
    asc: Literal["asc", "desc"] = "desc"

# Reclamation Type Schemas
class ReclamationTypeCreateInput(BaseModel):
    name: str
    description: Optional[str] = None

class ReclamationTypeOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

# Reclamation Success Response Schemas
class ReclamationOutSuccess(BaseOutSuccess):
    data: ReclamationFullOut

class ReclamationListOutSuccess(BaseOutSuccess):
    data: List[ReclamationOut]

class ReclamationsPageOutSuccess(BaseOutPage):
    data: List[ReclamationOut]

class ReclamationTypeOutSuccess(BaseOutSuccess):
    data: ReclamationTypeOut

class ReclamationTypeListOutSuccess(BaseOutSuccess):
    data: List[ReclamationTypeOut]
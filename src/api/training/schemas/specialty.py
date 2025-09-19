from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from src.helper.schemas import BaseOutPage, BaseOutSuccess

# Specialty Schemas
class SpecialtyCreateInput(BaseModel):
    name: str
    description: str = ""

class SpecialtyUpdateInput(BaseModel):
    name: str
    description: str = ""

class SpecialtyOut(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

class SpecialtyFilter(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1)
    search: Optional[str] = None
    order_by: Literal["created_at", "name"] = "created_at"
    asc: Literal["asc", "desc"] = "asc"

# Specialty Success Response Schemas
class SpecialtyOutSuccess(BaseOutSuccess):
    data: SpecialtyOut

class SpecialtyListOutSuccess(BaseOutSuccess):
    data: List[SpecialtyOut]

class SpecialtiesPageOutSuccess(BaseOutPage):
    data: List[SpecialtyOut]
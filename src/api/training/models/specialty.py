from sqlmodel import Field
from src.helper.model import CustomBaseModel
from typing import Optional

class Specialty(CustomBaseModel, table=True):
    __tablename__ = "specialties"
    
    name: str
    description: Optional[str] = Field(default="")
from sqlmodel import  Field
from src.helper.model import CustomBaseModel
from typing import  Optional




class TrainingCenter(CustomBaseModel, table=True):
    __tablename__ = "training_centers"

    name: str = Field( max_length=255, index=True, unique=True)
    address: str = Field(default="", max_length=255)
    city: str = Field(default='', max_length=120)
    postal_code: Optional[str] = Field(default=None, max_length=50)
    country_code: str = Field(default='', max_length=4)
    telephone_number: str = Field(default="", max_length=20)
    mobile_number: str = Field(default="", max_length=20)
    email: str = Field(default="", max_length=255)
    website: Optional[str] = Field(default=None, max_length=255)
    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)
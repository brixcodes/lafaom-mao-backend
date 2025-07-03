from sqlmodel import   TIMESTAMP, Field,Relationship,SQLModel
from typing import Optional
from datetime import datetime
from src.helper.model import CustomBaseModel,CustomBaseUUIDModel
from typing import  Optional
from uuid import uuid4
from src.api.user.models import User



class RefreshToken(CustomBaseUUIDModel,table=True):
    __tablename__ = "refresh_token"
    token : str = Field(nullable=False)
    user_id : str = Field(nullable=False)
    expires_at: datetime = Field(sa_type=TIMESTAMP(timezone=True), nullable=False) 


class TempUser(CustomBaseModel,table=True):
    __tablename__ = "temp_user"

    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    country_code: str = Field(nullable=True)
    phone_number: str | None  = Field(nullable=True)
    email:  str | None  = Field(nullable=True)
    password: str = Field(nullable=False)
    lang : str = Field(default="en")
    active : bool = Field(default=True)
    code : str = Field(default="")
    end_time: datetime = Field(sa_type=TIMESTAMP(timezone=True), nullable=False)
    
    def get_user_input(self)-> dict :
        return {
            
            "first_name": self.first_name,
            "last_name" : self.last_name,
            "country_code": self.country_code,
            "phone_number": self.phone_number,
            "email": self.email,
            "password": self.password,
            "lang"  : self.lang,
        }
    
    
class ForgottenPAsswordCode(CustomBaseModel,table=True):
    __tablename__ = "forgotten_password_code"
    
    user_id: str  | None =  Field(default=None, foreign_key="user.id")
    account : str = Field(nullable=False)
    code : str = Field(nullable=False)
    end_time : datetime = Field(sa_type=TIMESTAMP(timezone=True), nullable=False)
    active : bool = Field(default=True)



class ChangeEmailCode(CustomBaseModel,table=True):
    __tablename__ = "change_email_code"
    
    user_id: str  | None =  Field(default=None, foreign_key="user.id")
    account : str = Field(nullable=False)
    code : str = Field(nullable=False)
    end_time : datetime = Field(sa_type=TIMESTAMP(timezone=True), nullable=False)
    active : bool = Field(default=True)
    
    
class AuthUserProvider(CustomBaseModel,table=True):
    __tablename__ = "auth_user_provider"
    user_provider_id : str = Field(nullable=False)
    provider : str = Field(nullable=False)
    user_id: str | None =  Field(default=None, foreign_key="user.id")
    user : User = Relationship()
    
    
class AuthTempCode(SQLModel,table=True):
    __tablename__ = "auth_temp_code"
    user_id : str | None =  Field(default=None, foreign_key="user.id")
    code  : str = Field( nullable=False, primary_key=True)
    end_time : datetime = Field(sa_type=TIMESTAMP(timezone=True), nullable=False)
    user : User = Relationship()
    
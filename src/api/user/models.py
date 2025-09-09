from sqlmodel import  Field,Relationship,SQLModel
from datetime import date
from src.helper.model import CustomBaseUUIDModel,CustomBaseModel
from typing import List
from enum import Enum
from  datetime import datetime,timezone
from sqlalchemy import  TIMESTAMP, event



class Status(str, Enum):
    draft = "Draft"
    published = "Published"

class UserTypeEnum(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"
    Teacher = "teacher"
    STUDENT = "student"

class RoleEnum(str, Enum):
    SUPER_ADMIN = "super_admin"
    MANAGER = "manager"
    VISITOR = "visitor"
    
class UserStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    DELETED = "deleted"    

class CivilityEnum(str, Enum):
    MR = "Mr"
    MMME = "Mme"
    MLLE = "Mlle"
    

class PermissionEnum(str, Enum):

    CAN_VIEW_USER = "can_view_user"
    CAN_CREATE_USER = "can_create_user"
    CAN_UPDATE_USER = "can_update_user"
    CAN_DELETE_USER = "can_delete_user"
    

    CAN_VIEW_ROLE = "can_view_role"
    CAN_CREATE_ROLE = "can_create_role"
    CAN_UPDATE_ROLE = "can_update_role"
    CAN_DELETE_ROLE = "can_delete_role"
    
    CAN_GIVE_ROLE = "can_give_role"
    CAN_GIVE_PERMISSION = "can_give_permission"
    
"""
    CAN_VIEW_PERMISSION = "can_view_permission"
    CAN_CREATE_PERMISSION = "can_create_permission"
    CAN_UPDATE_PERMISSION = "can_update_permission"
    CAN_DELETE_PERMISSION = "can_delete_permission"
    
"""

class NotificationChannel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"      

class AddressTypeEnum(str, Enum):
    PRIMARY = "primary"
    BILLING = "billing"
class PermissionUserTypeEnum(str, Enum):
    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"



class Role(CustomBaseModel,table=True):
    __tablename__ = "role"
    
    name : str = Field(default=RoleEnum.MANAGER)
    description : str = Field(default="")

class UserRole(SQLModel,table=True):
    __tablename__ = "user_role"

    user_id : str | None = Field(default=None, foreign_key="users.id",primary_key=True)
    role_id : int | None = Field(default=None, foreign_key="role.id" ,primary_key=True)


class UserPermission(CustomBaseModel,table=True):
    __tablename__ = "user_permission"

    user_id : str | None = Field(default=None,foreign_key="users.id")
    role_id : int | None = Field(nullable=False,foreign_key="role.id" )
    permission : str = Field(nullable=False)

class SchoolCurriculum(CustomBaseModel,table=True):
    __tablename__ = "school_curriculum"
    
    user_id : str  = Field(foreign_key="users.id")
    qualification : str | None = Field(nullable=True)
    last_degree_obtained : str | None = Field(nullable=True)
    date_of_last_degree : date | None = Field(nullable=True)

class ProfessionStatus(CustomBaseModel,table=True):
    __tablename__ = "profession_status"
    
    user_id : str  = Field(foreign_key="users.id")
    professional_status : str = Field(nullable=False)
    professional_experience_in_months : int = Field(nullable=False,default=0)
    socio_professional_category : str | None = Field(nullable=True)

    job_position : str | None = Field(nullable=True)
    employer : str | None = Field(nullable=True)
    
class Address(CustomBaseModel, table=True):
    __tablename__ = "addresses"


    user_id: str = Field(foreign_key="users.id", nullable=False)
    address_type: str = Field(max_length=15, nullable=False,default=AddressTypeEnum.PRIMARY)  # e.g., 'primary', 'billing'

    country_code: str | None = Field(max_length=4, nullable=True)
    city: str | None = Field(max_length=120, nullable=True)
    street: str | None = Field(max_length=255, nullable=True)
    postal_code: str | None = Field(max_length=50, nullable=True)
    state: str | None = Field(max_length=120, nullable=True)


    user: "User" = Relationship(back_populates="addresses")

class User(CustomBaseUUIDModel,table=True):
    __tablename__ = "users"
    
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    birth_date: date | None = Field(nullable=True)
    civility : str | None = Field(nullable=True)
    country_code : str | None = Field(nullable=True,max_length=4)
    mobile_number : str | None = Field(nullable=True,index=True,unique=True)
    fix_number: str | None = Field(nullable=True,index=True,unique=True)
    email: str | None = Field(nullable=True,index=True,unique=True)
    password: str = Field(nullable=False)
    picture : str | None = Field(nullable=True)
    status : str = Field(default=UserStatusEnum.ACTIVE)
    lang : str = Field(default="en")
    web_token : str | None = Field(nullable=True)
    last_login : datetime | None = Field(default=None, nullable=True, sa_type=TIMESTAMP(timezone=True)) #datetime = Field(sa_type=TIMESTAMP(timezone=True), nullable=True)
    user_type :str = Field(default=UserTypeEnum.STUDENT)
    two_factor_enabled : bool = Field(default=False)
    
    
    professions_status : ProfessionStatus | None  = Relationship()
    addresses : List[Address] = Relationship()
    school_curriculum : SchoolCurriculum | None  = Relationship()
    
    roles : List["Role"] = Relationship(link_model=UserRole) 
    
    def full_name(self) -> str: 
        return f"{self.first_name.capitalize()} {self.last_name.capitalize()}"




def update_updated_at(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)


#Add the event listener for before update
event.listen(User, 'before_update', update_updated_at)
event.listen(Role, 'before_update', update_updated_at)
event.listen(UserRole, 'before_update', update_updated_at)
event.listen(UserPermission, 'before_update', update_updated_at)

#event.listen(mapper, 'before_delete', delete_delete_at)

#2131 , 22109 , 946    $2y$10$lY3advjnx.iUKjjhu4ir0uYOoTbspxZVr/TIDYPnhxXSOWdsBBPLC

#2136 $2y$10$1tOu7JhO61.LZvBRBDT.nObRhB3At25TJee4O8BXVzG/FamMcaPQi
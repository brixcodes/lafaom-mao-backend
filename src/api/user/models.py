from sqlmodel import  Field,Relationship,SQLModel, Column
from datetime import date
from src.helper.model import CustomBaseUUIDModel,CustomBaseModel
from typing import List
from enum import Enum
from  datetime import datetime,timezone

from sqlalchemy import JSON, TIMESTAMP, Integer, event

class DeviceType(str, Enum):
    IOS = "ios"
    WEB = "web"
    ANDROID = "android"


class Status(str, Enum):
    draft = "Draft"
    published = "Published"

class RoleEnum(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    
class UserStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    DELETED = "deleted"    

class PermissionEnum(str, Enum):

    CAN_VIEW_USER = "can_view_user"
    CAN_CREATE_USER = "can_create_user"
    CAN_UPDATE_USER = "can_update_user"
    CAN_DELETE_USER = "can_delete_user"

    CAN_VIEW_FAQ = "can_view_faq"
    CAN_CREATE_FAQ = "can_create_faq"
    CAN_UPDATE_FAQ = "can_update_faq"
    CAN_DELETE_FAQ = "can_delete_faq"

    CAN_VIEW_FAQ_CATEGORY = "can_view_faq_category"
    CAN_CREATE_FAQ_CATEGORY = "can_create_faq_category"
    CAN_UPDATE_FAQ_CATEGORY = "can_update_faq_category"
    CAN_DELETE_FAQ_CATEGORY = "can_delete_faq_category"
    
    CAN_VIEW_CATEGORY = "can_view_category"
    CAN_CREATE_CATEGORY = "can_create_category"
    CAN_UPDATE_CATEGORY = "can_update_category"
    CAN_DELETE_CATEGORY = "can_delete_category"
    
    CAN_VIEW_INQUIRY = "can_view_inquiry"
    CAN_UPDATE_INQUIRY = "can_update_inquiry"

    CAN_VIEW_LANGUAGE = "can_view_language"
    CAN_CREATE_LANGUAGE = "can_create_language"
    CAN_UPDATE_LANGUAGE = "can_update_language"
    CAN_DELETE_LANGUAGE = "can_delete_language"

    CAN_VIEW_COUNTRY = "can_view_country"
    CAN_CREATE_COUNTRY = "can_create_country"
    CAN_UPDATE_COUNTRY = "can_update_country"
    CAN_DELETE_COUNTRY = "can_delete_country"

    CAN_VIEW_ROLE = "can_view_role"
    CAN_CREATE_ROLE = "can_create_role"
    CAN_UPDATE_ROLE = "can_update_role"
    CAN_DELETE_ROLE = "can_delete_role"
    CAN_GIVE_ROLE = "can_give_role"

    CAN_VIEW_PERMISSION = "can_view_permission"
    CAN_CREATE_PERMISSION = "can_create_permission"
    CAN_UPDATE_PERMISSION = "can_update_permission"
    CAN_DELETE_PERMISSION = "can_delete_permission"
    CAN_GIVE_PERMISSION = "can_give_permission"

    CAN_VIEW_VIDEO = "can_view_video"
    CAN_CREATE_VIDEO = "can_create_video"
    CAN_UPDATE_VIDEO = "can_update_video"
    CAN_DELETE_VIDEO = "can_delete_video"

    CAN_VIEW_PODCAST = "can_view_podcast"
    CAN_CREATE_PODCAST = "can_create_podcast"
    CAN_UPDATE_PODCAST = "can_update_podcast"
    CAN_DELETE_PODCAST = "can_delete_podcast"

    CAN_VIEW_EBOOK = "can_view_ebook"
    CAN_CREATE_EBOOK = "can_create_ebook"
    CAN_UPDATE_EBOOK = "can_update_ebook"
    CAN_DELETE_EBOOK = "can_delete_ebook"

    CAN_VIEW_LIVESTREAM = "can_view_livestream"
    CAN_CREATE_LIVESTREAM = "can_create_livestream"
    CAN_UPDATE_LIVESTREAM = "can_update_livestream"
    CAN_DELETE_LIVESTREAM = "can_delete_livestream"

    CAN_VIEW_RADIO = "can_view_radio"
    CAN_CREATE_RADIO = "can_create_radio"
    CAN_UPDATE_RADIO = "can_update_radio"
    CAN_DELETE_RADIO = "can_delete_radio"

    CAN_VIEW_RADIO_PROGRAM = "can_view_radio_program"
    CAN_CREATE_RADIO_PROGRAM = "can_create_radio_program"
    CAN_UPDATE_RADIO_PROGRAM = "can_update_radio_program"
    CAN_DELETE_RADIO_PROGRAM = "can_delete_radio_program"
    
    CAN_VIEW_NEWSPAPER = "can_view_newspaper"
    CAN_CREATE_NEWSPAPER = "can_create_newspaper"
    CAN_UPDATE_NEWSPAPER = "can_update_newspaper"
    CAN_DELETE_NEWSPAPER = "can_delete_newspaper"

    CAN_VIEW_NEWSPAPER_ARTICLE = "can_view_newspaper_article"
    CAN_CREATE_NEWSPAPER_ARTICLE = "can_create_newspaper_article"
    CAN_UPDATE_NEWSPAPER_ARTICLE = "can_update_newspaper_article"
    CAN_DELETE_NEWSPAPER_ARTICLE = "can_delete_newspaper_article"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"      


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

    user_id : str | None = Field(default=None, foreign_key="user.id",primary_key=True)
    role_id : int | None = Field(default=None, foreign_key="role.id" ,primary_key=True)


class UserPermission(CustomBaseModel,table=True):
    __tablename__ = "user_permission"

    user_id : str | None = Field(default=None,foreign_key="user.id")
    role_id : int | None = Field(nullable=False,foreign_key="role.id" )
    permission : str = Field(nullable=False)

class User(CustomBaseUUIDModel,table=True):
    __tablename__ = "user"

    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    country_code: str = Field(nullable=False)
    phone_number: str | None = Field(nullable=True,index=True,unique=True)
    email: str | None = Field(nullable=True,index=True,unique=True)
    password: str = Field(nullable=False)
    picture : str = Field(default="")
    status : str = Field(default=UserStatusEnum.ACTIVE)
    lang : str = Field(default="en")
    prefer_notification : str = Field(nullable=True,default=NotificationChannel.EMAIL)
    android_token : str | None = Field(nullable=True)
    ios_token : str | None = Field(nullable=True)
    web_token : str | None = Field(nullable=True)
    prefer_lang_id : int | None = Field(default=None)
    
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
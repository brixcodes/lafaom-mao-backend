from pydantic import BaseModel,Field
from typing import List,Optional,Literal
from datetime import date, datetime
from src.api.user.models import UserTypeEnum
from src.helper.schemas import BaseOutSuccess



class CreateUserInput(BaseModel):
    id : str
    first_name: str 
    last_name: str 
    password: str
    birth_date: date | None 
    civility : str | None 
    country_code : str | None 
    mobile_number : str | None 
    fix_number: str | None 
    email: str | None 
    status : str
    lang : str 
    web_token : str | None 
    user_type : str 
    two_factor_enabled : bool 
    

class UpdateUserInput(BaseModel):
    id : str
    first_name: str 
    last_name: str 
    password: str
    birth_date: date | None 
    civility : str | None 
    country_code : str | None 
    mobile_number : str | None 
    fix_number: str | None 
    email: str | None 
    status : str
    lang : str 
    web_token : str | None 
    two_factor_enabled : bool



class ListDataInput(BaseModel):

    data : List[int]
    



    
class UserOut(BaseModel):
    id : str
    first_name: str 
    last_name: str 
    country_code: str 
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address : Optional[str] = None
    picture :  Optional[str] = None 
    status : str 
    lang : str 
    created_at : datetime
    updated_at : datetime
    prefer_notification : str 
    

class UserListInput(BaseModel):
    user_ids : List[str]


class ProfessionStatusOut(BaseModel):
    id : str
    professional_status : Optional[str] =""
    professional_experience_in_months : int  = 0
    socio_professional_category : Optional[str] ="" 
    job_position : Optional[str] ="" 
    employer : Optional[str] ="" 
    created_at : datetime

class AddressOut(BaseModel):
    id : str
    country_code: Optional[str]  =""
    city: Optional[str]  =""
    street: Optional[str]  =""
    postal_code: Optional[str] = "0000"
    state: Optional[str]  =""
    created_at : datetime

class UserSimpleOut(BaseModel):
    id : str
    first_name: str 
    last_name: str 
    birth_date: date | None 
    civility : str | None 
    country_code : str | None 
    mobile_number : str | None 
    fix_number: str | None 
    email: str | None 
    picture : str | None 
    status : str
    lang : str 
    web_token : str | None 
    last_login : datetime | None
    user_type : str 
    two_factor_enabled : bool 
    created_at : datetime
    
class SchoolCurriculumOut(BaseModel):
    id : str
    qualification : Optional[str] =""
    last_degree_obtained : Optional[str] =""
    date_of_last_degree :Optional[date] =""  
    created_at : datetime

class UserFullOut(UserSimpleOut):
    professions_status : Optional[ProfessionStatusOut]  
    addresses : List[AddressOut]
    school_curriculum : Optional[SchoolCurriculumOut] 
    

class UserOutSuccess(BaseOutSuccess):
    
    data: UserOut 

class UserFullOutSuccess(BaseOutSuccess):
    
    data: UserFullOut 

    
class UserListOutSuccess(BaseOutSuccess):
    
    data: List [UserOut]  
    
class UsersPageOutSuccess(BaseOutSuccess):
    
    data: List [UserOut]

class UserFilter(BaseModel):
    page: int | None = Field(1, ge=1)
    page_size: int | None = Field(20, ge=20)
    search : str | None
    user_type : UserTypeEnum | None
    country_code : str | None
    
    order_by:  Literal["created_at", "last_login","first_name","last_name"] = "created_at"
    asc :  Literal["asc", "desc"] = "asc"
    
class AssignPermissionsInput(BaseModel):
    user_id : str
    permissions : List[str]
    
class AssignRoleInput(BaseModel):
    user_id : str
    role_id : int
    
class RoleOut(BaseModel):
    id : int
    name : str
    description : Optional[str] = ''
    
class RoleOutSuccess(BaseOutSuccess):
    data : RoleOut
    
class RoleListOutSuccess(BaseOutSuccess):
    data : List[RoleOut]    
    
class PermissionOut(BaseModel):
    id : int
    name : str

class PermissionOutSuccess(BaseOutSuccess):
    data : PermissionOut
    
class PermissionListOutSuccess(BaseOutSuccess):
    data : List[PermissionOut]
from pydantic import BaseModel,Field
from typing import List,Optional,Literal
from datetime import datetime
from src.helper.schemas import BaseOutSuccess



class UserCreateInput(BaseModel):
    name: str
    email: str
    password: str
    

class  AccountInput(BaseModel):
    account : str   




class ListDataInput(BaseModel):

    data : List[int]
    

class UserUpdateInput(UserCreateInput):
    pass


    
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

class UserSimpleOut(BaseModel):
    id : str
    first_name: str 
    last_name: str 
    phone_number: Optional[str] = None
    email: Optional[str] = None
    status : str 
    lang : str 
    created_at : datetime
    

class UserOutSuccess(BaseOutSuccess):
    
    data: UserOut 


class UsersOutSuccess(BaseOutSuccess):
    
    data: List [UserOut]    
    
class UserListOutSuccess(BaseOutSuccess):
    
    data: List [UserOut]  
    
class FreelancerFilterParams(BaseModel):
    page: int | None = Field(1, ge=1)
    category : str = "all"
    location : str  = "all"
    skills: list[int]  =  []
    diplomas: list[str]  =  []
    certificates: list[int]  =  []
    languages: list[int]  =  []
    order_by:  Literal["created_at", "pricing"] = "created_at"
    asc :  Literal["asc", "desc"] = "asc"

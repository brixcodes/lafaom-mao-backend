from typing import List, Literal
from pydantic import BaseModel,field_validator,EmailStr
import phonenumbers
from  datetime import datetime
from src.api.user.models import NotificationChannel
from src.api.user.schemas import UserOut
import re
from enum import Enum


class Token(BaseModel):
    token: str
    token_type: str
    refresh_token: str =""
    device_id: str = ""
    expires_in: int | None = None

class UserTokenOut(BaseModel):
    access_token : Token
    user : UserOut 

class TokenData(BaseModel):
    token : str | None = None
    user_id : str | None = None
    expire_at: datetime | None = None
    
class LoginInput(BaseModel):
    account : str
    password : str = ""
    
    @field_validator('account')
    def valid_phone_number_or_email(cls, v):
        
        
        if not PhoneUtil(v).isValid() :
            email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'  # Simple regex for email validation
            if not re.match(email_regex, v):
                raise ValueError('Invalid email or phone number ')
            
            
    
        return v      
    
class UpdatePasswordInput(BaseModel):
    password: str 
    new_password : str 
    
    
class UpdateAccountSettingInput(BaseModel):
    prefer_notification :  NotificationChannel  | None = None   

class AuthCodeInput(BaseModel):
    code : str 

class RegisterProviderInput(BaseModel):
    first_name : str =""
    last_name : str =""
    country_code : str  | None = None
    phone_number : str  | None = None
    email: EmailStr | None = None
    lang : str = "en" 
    picture : str =""
    password : str = ""
    


class RegisterInput(BaseModel):
    first_name : str
    last_name : str
    country_code : str
    phone_number : str | None = None
    email: EmailStr | None = None
    password: str
    lang : str = "en" 
    @field_validator('phone_number')
    def valid_phone_number(cls, v):
        
        if v == "" :
            v = None
        
        if v != None  and not PhoneUtil(v).isValid() :
            raise ValueError('the number must be valid international phone number')
        
        
        return v         

class UpdateUserInput(BaseModel):
    first_name : str
    last_name : str
    country_code : str
    lang : str = "en" 
    
class UpdateDeviceInput(BaseModel):
    device_id : str

    
class CustomEmailInput(BaseModel):
    email: EmailStr
    
    @field_validator('email')
    def manual_email_validation(cls, v):
        # Simulate a validation error
        raise ValueError('the email already used')

class CustomPasswordInput(BaseModel):
    password : str
    
    @field_validator('password')
    def manual_password_validation(cls, v):
        # Simulate a validation error
        raise ValueError('the password does not match')        
        
class PhoneUtil():
    def __init__(self,number:str,country:str = None) -> None:
        try :
            self._value = phonenumbers.parse(number,country)
            print(self._value)
        except :   
            self._value = None 
            
    
    def isValid(self)-> bool:
        if self._value == None:
            return False
        else :    
            return phonenumbers.is_valid_number(self._value) 
        
class ValidateAccountInput(BaseModel) : 
    code : str    
    phone_number : str | None = None
    email: EmailStr | None = None
    @field_validator('phone_number')
    def valid_phone_number(cls, v):
        
        if v == "" :
            v = None
        
        if v != None  and not PhoneUtil(v).isValid() :
            raise ValueError('the number must be valid international phone number')
        
        
        return v   

class ChangeAttributeInput(BaseModel) : 
    
    account : str
    password : str = ""
    
    @field_validator('account')
    def valid_phone_number_or_email(cls, v):
        
        
        if not PhoneUtil(v).isValid() :
            email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'  # Simple regex for email validation
            if not re.match(email_regex, v):
                raise ValueError('Invalid email or phone number ')
            
    
        return v           
    
class ValidateForgottenPasswordCode(ChangeAttributeInput) : 
   
    password : str 
    code : str
    
class ValidateChangeEmailCode(ChangeAttributeInput) : 
    code : str
    
class RefreshTokenInput(BaseModel) : 
    refresh_token : str
    device_id: str = ""

class CheckPermission(BaseModel):
    data : List[str]

class ProviderURL(str, Enum):

    GITHUB_AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_INFO_URL = "https://api.github.com/user"


    LINKEDIN_AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
    LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    LINKEDIN_USER_INFO_URL = "https://api.linkedin.com/v2/me"
    LINKEDIN_USER_EMAIL_URL = "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))"


    GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"


class Provider(str, Enum):
    GOOGLE = "google"
    GITHUB = "github"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"

class SocialTokenInput(BaseModel) : 
    token : str
    platform : Literal["ios", "android", "web"] = "web"



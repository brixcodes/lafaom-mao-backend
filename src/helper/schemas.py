from typing import Any
from pydantic import BaseModel

from enum import Enum


class BaseOutPage(BaseModel):
    
    """
    Base schema for output which have pagination
    -    data : Any (the data to return)
    -    page : int (the page you have fetch)
    -    number :int (the number of record in the data)
    -    total_number : int (the total number of record found for the query)  
    -    number_page : int (the total number of page for the query)
        
    """
    
    data : Any
    page : int
    number :int
    total_number : int   
    
    
class BaseOut(BaseModel):
    
    """
    Base schema for output 
    -    message :  (message)
    -    success : bool (successful request or not)    
    """

    success : bool   
    message : str     
    
class BaseOutSuccess(BaseOut):
    
    """
    Base schema for success output 
    -    data : Any (the data to return)
    -    message :  (message)
    -    success : bool (successful request or not)    
    """

    success : bool   = True 
    message : str  
    data : Any  

class BaseOutFail(BaseOut):
    
    """
    Base schema for fail output 
    -    error_code : str (error code)
    -    message :  (message)
    -    success : bool (successful request or not)    
    """

    success : bool = False  
    message : str  
    error_code : str          

class WhatsappParameter(BaseModel):
    type : str = "text" 
    value : str = ""         
class WhatsappTemplate(BaseModel):
    templateName : str = "" 
    language : str = "en"   
    
class WhatsappMessage(BaseModel):
    
    template : WhatsappTemplate  
    phone_id : str = "" 
    parameters : list[WhatsappParameter] = []        
    
class AccessTokenType(str, Enum):
    WHATSAPP = "whatsapp"
    PESU_PAY = "pesu_pay"
    TOUPESU = "toupesu"

class LanguageType(str, Enum):
    FRENCH = "fr"
    ENGLISH = "en"    

class MESSAGE_CHANNEL(str, Enum):

    PUSHER = "pusher"
    CUSTOM_SERVICE = "custom_service"

class EMAIL_CHANNEL(str, Enum):

    SMTP = "smtp"
    MAILGUN = "mailgun"

class ErrorMessage(Enum):
    def __init__(self, value, description):
        self._value_ = value
        self.description = description

    @property
    def describe(self):
        return self.description
    
    NOT_AUTHENTICATED = ("not_authenticated", "Not Authenticated")
    INVALID_TOKEN = ("invalid_token", "Invalid Token")
    INVALID_CREDENTIALS = ("invalid_credentials", "Invalid Credentials")
    INVALID_TOKEN_TYPE = ("invalid_token_type", "Invalid Token Type")

    UNKNOWN_ERROR = ('unknown_error',"Error has occur, try latter")
    FAILED_TO_OBTAIN_USER_INFO = ('failed_to_obtain_user_info',"Failed to obtain user info")
    FAILED_TO_OBTAIN_TOKEN = ('failed_to_obtain_token',"Failed to obtain token")
    EMAIL_OR_PHONE_NUMBER_REQUIRED = ('email_or_phone_number_required',"Email or phone number required")
    
    PROVIDER_NOT_FOUND = ("provider_not_found", "Provider not found")
    
    CHANNEL_NOT_FOUND = ("channel_not_found", "Channel not found")
    USER_NOT_FOUND = ("user_not_found", "User not found")


    CODE_NOT_EXIST = ("code_not_exist","Code does not exist")
    CODE_ALREADY_USED= ("code_already_used","Code already used")
    CODE_HAS_EXPIRED = ("code_has_expired","Code has expired")

    USER_NOT_ACTIVE = ('user_not_active',"User is not active")
    COULD_NOT_VALIDATE_CREDENTIALS = ('could_not_validate_credentials',"Could not validate credentials")
    INCORRECT_EMAIL_OR_PASSWORD = ('in_correct_email_or_password',"Incorrect email or password")
    EMAIL_ALREADY_TAKEN = ('email_already_token',"Email already taken")
    EMAIL_NOT_FOUND = ('email_not_found',"User email not found")
    PHONE_NUMBER_NOT_SUPPORTED = ('phone_number_not_supported',"Phone number not yet supported")
    PASSWORD_NOT_CORRECT = ('password_not_correct',"The password is not correct")

    PHONE_NUMBER_ALREADY_TAKEN = ('phone_number_already_token',"Phone number already taken")
    
    REFRESH_TOKEN_NOT_FOUND = ('refresh_token_not_found',"Refresh token not found")
    REFRESH_TOKEN_HAS_EXPIRED = ('refresh_token_has_expired',"Refresh token has expired")

    SOME_THING_WENT_WRONG = ('something_went_wrong',"Something went wrong try later")
    TOUPESU_USER_NOT_FOUND = ('toupesu_user_not_found',"Toupesu user not found")

    ACCESS_DENIED = ('access_denied',"Access denied")
    SERVER_ERROR = ('server_error',"Server error")
    PROVIDER_NOT_SUPPORTED = ('provider_not_supported',"Provider not supported")     

    
    def __str__(self):
        return self.value   
from typing import Optional
from pydantic import BaseModel,EmailStr
from src.config import settings
from src.api.user.models import NotificationChannel
from src.helper.schemas import EMAIL_CHANNEL, WhatsappMessage, WhatsappParameter, WhatsappTemplate

from src.helper.utils import NotificationHelper


class NotificationBase(BaseModel):
    email : Optional[str] = None 
    phone_number : Optional[str] = None
    email_template : str = "email_base"
    whatsapp_template : str = "whatsapp_base"
    lang : str = "en"
    prefer_notification : NotificationChannel = NotificationChannel.EMAIL
    
    def email_data(self):
        return {}
    
    def whatsapp_data(self):
        return {}
    
    
    def send_notification(self) :
        if (self.prefer_notification == NotificationChannel.EMAIL and self.email != None) or self.email != None : 
            data = self.email_data()
            if settings.EMAIL_CHANNEL == EMAIL_CHANNEL.SMTP :
                NotificationHelper.send_smtp_email.delay( data)
            else : 
                NotificationHelper.send_mailgun_email.delay( data)
            return True
            
        elif (self.prefer_notification == NotificationChannel.WHATSAPP and self.phone_number != None) or  self.phone_number != None  :
            data = self.whatsapp_data()
            NotificationHelper.send_whatsapp_message.delay(data)
            return True
        return False


class LoginAlertNotification(NotificationBase) :

    subject : str = "Login Alert"
    email_template : str = "login_alert_email.html"
    whatsapp_template : str = "toupesu_registration_code_en"
    device : str = ""  
    date : str = ""
    
    def email_data(self)->dict :
        return{
            "to_email" :self.email,
            "subject":self.subject,
            "template_name":self.email_template ,
            "lang":self.lang,
            "context":{
                    "device":self.device,
                    "date": self.date
                } 
        } 
        
    def whatsapp_data(self)->dict :
        return WhatsappMessage(
                    phone_id = self.phone_number, 
                    template= WhatsappTemplate(
                        templateName=self.whatsapp_template,language=self.lang
                        ),
                    parameters = [ 
                                    WhatsappParameter(type="text",value=self.device),
                                    WhatsappParameter(type="text",value=self.date) 
                                ]
                ).model_dump()

class AccountVerifyNotification(NotificationBase) :

    subject : str = "Email Validation"
    email_template : str = "verify_email.html"
    whatsapp_template : str = "toupesu_registration_code_en"
    code : str = ""  
    time : int = 30
    
    def email_data(self)->dict :
        return{
            "to_email" :self.email,
            "subject":self.subject,
            "template_name":self.email_template ,
            "lang":self.lang,
            "context":{
                    "code":self.code,
                    "time": self.time
                } 
        } 
        
    def whatsapp_data(self)->dict :
        return WhatsappMessage(
                    phone_id = self.phone_number, 
                    template= WhatsappTemplate(
                        templateName=self.whatsapp_template,language=self.lang
                        ),
                    parameters = [ 
                                    WhatsappParameter(type="text",value=self.code),
                                    WhatsappParameter(type="text",value=self.time) 
                                ]
                ).model_dump()
        
class ForgottenPasswordNotification(NotificationBase) :

    subject : str = "Forgotten Password"
    email_template : str = "forgotten_password.html" 
    whatsapp_template : str = "toupesu_registration_code_en"
    code : str = ""  
    time : int = 30 
    
    def email_data(self)->dict :
        return{
            "to_email" :self.email,
            "subject":self.subject,
            "template_name":self.email_template ,
            "lang":self.lang,
            "context":{
                    "code":self.code,
                    "time": self.time
                } 
        } 
        
    def whatsapp_data(self)->dict :
        return WhatsappMessage(
                    phone_id = self.phone_number, 
                    template= WhatsappTemplate(
                        templateName=self.whatsapp_template,language=self.lang
                        ),
                    parameters = [ 
                                    WhatsappParameter(type="text",value=self.code),
                                    WhatsappParameter(type="text",value=self.time) 
                                ]
                ).model_dump()
        
        
class ChangeAccountNotification(NotificationBase) :

    subject : str = "Change Email"
    email_template : str = "change_email.html" 
    whatsapp_template : str = "toupesu_registration_code_en"
    code : str = ""  
    time : int = 30  
        
        
    def email_data(self)->dict :
        return{
            "to_email" :self.email,
            "subject":self.subject,
            "template_name":self.email_template ,
            "lang":self.lang,
            "context":{
                    "code":self.code,
                    "time": self.time
                } 
        } 
        
    def whatsapp_data(self)->dict :
        return WhatsappMessage(
                    phone_id = self.phone_number, 
                    template= WhatsappTemplate(
                        templateName=self.whatsapp_template,language=self.lang
                        ),
                    parameters = [ 
                                    WhatsappParameter(type="text",value=self.code),
                                    WhatsappParameter(type="text",value=str(self.time)) 
                                ]
                ).model_dump()
        
        
class TwoFactorAuthNotification(NotificationBase) :

    subject : str = "Two Factor Authentication"
    email_template : str = "2fa_auth_email.html"   
    whatsapp_template : str = "toupesu_registration_code_en"
    code : str = ""  
    time : int = 30  
        
        
    def email_data(self)->dict :
        return{
            "to_email" :self.email,
            "subject":self.subject,
            "template_name":self.email_template ,
            "lang":self.lang,
            "context":{
                    "code":self.code,
                    "time": self.time
                } 
        } 
        
    def whatsapp_data(self)->dict :
        return WhatsappMessage(
                    phone_id = self.phone_number, 
                    template= WhatsappTemplate(
                        templateName=self.whatsapp_template,language=self.lang
                        ),
                    parameters = [ 
                                    WhatsappParameter(type="text",value=self.code),
                                    #WhatsappParameter(type="text",value=self.time) 
                                ]
                ).model_dump()
        
        
class WelcomeNotification(NotificationBase) :

    subject : str = "Welcome to La'akam"
    email_template : str = "welcome_email.html"   
    whatsapp_template : str = "laakam_welcome_en"
        
        
    def email_data(self)->dict :
        return{
            "to_email" :self.email,
            "subject":self.subject,
            "template_name":self.email_template ,
            "lang":self.lang,
            "context":{
                } 
        } 
        
    def whatsapp_data(self)->dict :
        return WhatsappMessage(
                    phone_id = self.phone_number, 
                    template= WhatsappTemplate(
                        templateName=self.whatsapp_template,language=self.lang
                        ),
                    parameters = [ ]
                ).model_dump()
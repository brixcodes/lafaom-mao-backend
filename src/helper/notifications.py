
from pydantic import BaseModel
from src.config import settings

from src.helper.schemas import EMAIL_CHANNEL

from src.helper.utils import NotificationHelper


class NotificationBase(BaseModel):
    email : str
    email_template : str = "email_base"
    lang : str = "en"
    
    def email_data(self):
        return {}
    
    
    
    def send_notification(self) :
        data = self.email_data()
        if settings.EMAIL_CHANNEL == EMAIL_CHANNEL.SMTP :
            NotificationHelper.send_smtp_email.delay( data)
        else : 
            NotificationHelper.send_mailgun_email.delay( data)
        return True
            



class LoginAlertNotification(NotificationBase) :

    subject : str = "Login Alert"
    email_template : str = "login_alert_email.html"
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
        

class AccountVerifyNotification(NotificationBase) :

    subject : str = "Email Validation"
    email_template : str = "verify_email.html"
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
        

        
class ForgottenPasswordNotification(NotificationBase) :

    subject : str = "Forgotten Password"
    email_template : str = "forgotten_password.html"
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
        

        
        
class ChangeAccountNotification(NotificationBase) :

    subject : str = "Change Email"
    email_template : str = "change_email.html" 
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

        
        
class TwoFactorAuthNotification(NotificationBase) :

    subject : str = "Two Factor Authentication"
    email_template : str = "2fa_auth_email.html"  
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
        
        
        
class WelcomeNotification(NotificationBase) :

    subject : str = "Welcome to La'akam"
    email_template : str = "welcome_email.html"  
        
        
    def email_data(self)->dict :
        return{
            "to_email" :self.email,
            "subject":self.subject,
            "template_name":self.email_template ,
            "lang":self.lang,
            "context":{
                } 
        } 
        
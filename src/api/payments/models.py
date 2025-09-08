from sqlmodel import  Field
from src.helper.model import CustomBaseUUIDModel,CustomBaseModel
from typing import  Optional
from enum import Enum




class Payment(CustomBaseUUIDModel,table=True):
    
    __tablename__ = "payments"
    
    transaction_id : str
    amount : float # this is the amount from the article
    currency : str # this is the currency from the article
    payment_currency : str # this is the payment currency
    daily_rate : float
    usd_currency_rate : float
    usd_payment_currency_rate : float
    
    payable_id : str
    payable_type : str
    payment_type_id : str
    payment_type : str
    

class PaymentStatusEnum(Enum):
    PENDING = "pending"  
    ACCEPTED = "accepted"  
    REFUSED = "refused"  
    CANCELLED = "cancelled"  
    ERROR = "error"  
    REPAY = "rembourse"
    

class ChannelEnum(Enum):
    
    MOBILE_MONEY = "MOBILE_MONEY"
    WALLET = "WALLET"
    CREDIT_CARD = "CREDIT_CARD"

class CinetPayPayment(CustomBaseModel, table=True):
    """Model for CinetPay payments"""
    __tablename__ = "cinetpay_payments"

    
    transaction_id: str = Field(max_length=255, unique=True, index=True)
    amount: int = Field( description="Amount")
    currency: str = Field(default="XAF", max_length=3)
    channel : str = Field(default=ChannelEnum.MOBILE_MONEY, max_length=50)
    status: str = Field(default=PaymentStatusEnum.PENDING, max_length=10)
    
    api_response_id : Optional[str] = Field(default=None, max_length=100)
    payment_url: Optional[str]   = Field(default=None, max_length=255)
    payment_token: Optional[str] = Field(default=None, max_length=255)
    error_code : Optional[str] = Field(default=None, max_length=255)
    

class UserPaymentInfo(CustomBaseModel,table=True):
    __tablename__ = "user_payment_infos"
    
    customer_id : Optional[str] = Field(default=None, foreign_key="users.id")
    customer_name : str
    customer_surname : str
    customer_phone_number : str
    customer_email : str
    customer_address : str
    customer_city : str
    customer_country : str
    customer_state : str
    customer_zip_code : str
    




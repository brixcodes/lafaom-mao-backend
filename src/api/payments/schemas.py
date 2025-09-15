from pydantic import BaseModel, Field
from typing import Any, Optional

from src.api.job_offers.models import JobApplication

class CinetPayInit(BaseModel):
    transaction_id: str
    amount: int
    currency: str = "XOF"
    description: str
    invoice_data : dict
    meta :str
    customer_name : Optional[str] = None
    customer_surname :  Optional[str] = None
    customer_email : Optional[str] = None
    customer_phone_number : Optional[str] = None
    customer_address : Optional[str] = None
    customer_city : Optional[str] = None
    customer_country : Optional[str] = None
    customer_state : Optional[str] = None
    customer_zip_code : Optional[str] = None

class PaymentInitInput(BaseModel):
    payable: JobApplication 
    amount: int
    product_currency: str 
    description: str
    payment_provider: str = "CINETPAY"
    customer_name : Optional[str] = None
    customer_surname :  Optional[str] = None
    customer_email : Optional[str] = None
    customer_phone_number : Optional[str] = None
    customer_address : Optional[str] = None
    customer_city : Optional[str] = None
    customer_country : Optional[str] = None
    customer_state : Optional[str] = None
    customer_zip_code : Optional[str] = None

class WebhookPayload(BaseModel):
    cpm_site_id: str
    cpm_trans_id: str
    cpm_trans_date: str
    cpm_amount: str
    cpm_currency: str
    signature: str
    payment_method: str
    cel_phone_num: str
    cpm_phone_prefixe: str
    cpm_language: str
    cpm_version: str
    cpm_payment_config: str
    cpm_page_action: str
    cpm_custom: str
    cpm_designation: str
    cpm_error_message: str


class CinetPayCheckPaymentStatus(BaseModel):
    site_id: str
    transaction_id: str

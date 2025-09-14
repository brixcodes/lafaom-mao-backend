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

class PaymentInitInput(BaseModel):
    payable: JobApplication 
    amount: int
    product_currency: str 
    description: str
    payment_provider: str = "CINETPAY"

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

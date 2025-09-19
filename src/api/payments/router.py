import hashlib
import hmac
from typing import Annotated
from fastapi import APIRouter, Depends, Form, HTTPException, Header,Query
from src.api.payments.dependencies import get_payment_by_transaction
from src.api.payments.models import PaymentStatusEnum
from src.api.payments.service import PaymentService 
from src.api.payments.schemas import  PaymentFilter, PaymentOutSuccess, PaymentPageOutSuccess, WebhookPayload
from src.api.auth.models import User
from src.config import settings
# This is a placeholder for your actual dependency to get the current user
# You should replace it with your actual implementation.
async def get_current_active_user() -> User:
    # In a real application, you would get the user from the request's
    # authentication credentials (e.g., a JWT token).
    # For this example, we'll return a dummy user.
    return User(id="user123", email="user@example.com", is_active=True)


router = APIRouter()


@router.get("/payments",response_model=PaymentPageOutSuccess)
async def get_payment_status(
    filters: Annotated[PaymentFilter, Query(...)],
    payment_service: PaymentService = Depends()
):
 
    payments, total =await payment_service.list_payments(filters)
    return {"data": payments, "page": filters.page, "number": len(payments), "total_number": total}

@router.post("/cinetpay/notify")
async def cinetpay_webhook_handler(
    
    payload: Annotated[WebhookPayload, Form(...)],
    x_token: str = Header(..., alias="x-token")
    
):
    # Step 1: Concatenate fields in correct order
    data_string = (
        payload.cpm_site_id
        + payload.cpm_trans_id
        + payload.cpm_trans_date
        + payload.cpm_amount
        + payload.cpm_currency
        + payload.signature
        + payload.payment_method
        + payload.cel_phone_num
        + payload.cpm_phone_prefixe
        + payload.cpm_language
        + payload.cpm_version
        + payload.cpm_payment_config
        + payload.cpm_page_action
        + payload.cpm_custom
        + payload.cpm_designation
        + payload.cpm_error_message
    )

    
    generated_token = hmac.new(
        settings.CINETPAY_SECRET_KEY.encode("utf-8"),
        data_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    
    if not hmac.compare_digest(x_token, generated_token):
        raise HTTPException(status_code=403, detail="Invalid token")
    
    PaymentService.check_cash_in_status.apply_async(
                kwargs={"transaction_id": payload.cpm_trans_id},
                countdown=0  # Delay execution by 60 seconds
            )
    
    return {
        "status": "success",
        "message": "Webhook verified",
        "transaction_id": payload.cpm_trans_id,
    }

@router.get("/check-status/{transaction_id}",response_model=PaymentOutSuccess)
async def get_payment_status(
    transaction_id: str,
    payment : Annotated[User, Depends(get_payment_by_transaction)],
    payment_service: PaymentService = Depends()
):
    if payment.status == PaymentStatusEnum.PENDING.value:
        
        payment = await payment_service.check_payment_status(payment)
        
    return {
        "message" : "success",
        "data": payment
    }


from celery import shared_task
from sqlalchemy import select

from src.api.payments.models import Payment, PaymentStatusEnum
from src.api.payments.service import PaymentService
from src.database import get_session


@shared_task
def check_cash_in_status(transaction_id: str) -> dict:
    """
    Celery task to check cash-in status for a payment.
    """

    for session in get_session():
            payment_statement = select(Payment).where(Payment.transaction_id == transaction_id)
            payment = session.scalars(payment_statement).first()
            
            if not payment:
                return {"message": "failed", "data": None}

            if payment.status == PaymentStatusEnum.PENDING:
                payment = PaymentService.check_payment_status_sync(session, payment)

            return {"message": "success", "data": payment}
    # ✅ Correctly wrap the async function


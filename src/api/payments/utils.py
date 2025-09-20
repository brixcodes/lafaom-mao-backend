from asgiref.sync import async_to_sync

from celery import shared_task

from src.api.job_offers.service import JobOfferService
from src.api.payments.models import PaymentStatusEnum
from src.api.payments.service import PaymentService
from src.api.training.services.student_application import StudentApplicationService
from src.database import get_session


@shared_task
def check_cash_in_status(transaction_id: str) -> dict:
    """
    Celery task to check cash-in status for a payment.
    """

    async def _check():
        async with get_session() as session:
            payment_service = PaymentService(session=session)

            payment = await payment_service.get_payment_by_transaction_id(transaction_id)
            if not payment:
                return {"message": "failed", "data": None}

            if payment.status == PaymentStatusEnum.PENDING:
                payment = await payment_service.check_payment_status(transaction_id)

            if payment.status == PaymentStatusEnum.ACCEPTED:
                if payment.payable_type == "JobApplication":
                    job_service = JobOfferService(session=session)
                    await job_service.update_job_application_payment(
                        payment_id=int(payment.id),
                        application_id=payment.payable_id,
                    )
                elif payment.payable_type == "StudentApplication":
                    student_service = StudentApplicationService(session=session)
                    await student_service.update_student_application_payment(
                        payment_id=int(payment.id),
                        application_id=payment.payable_id,
                    )

            return {"message": "success", "data": payment}

    # Run the async function in the synchronous Celery task
    return async_to_sync(_check())
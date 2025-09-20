import asyncio

from celery import shared_task

from src.api.job_offers.service import JobOfferService
from src.api.payments.models import PaymentStatusEnum
from src.api.payments.service import PaymentService
from src.api.training.services.student_application import StudentApplicationService
from src.database import get_session



@shared_task
async def check_cash_in_status(transaction_id : str ) -> dict :
        
        async def _check():
            async for session in get_session():
                payment_service = PaymentService(session=session)

                payment = await payment_service.get_payment_by_transaction_id(transaction_id)
                if payment is None:
                    return {
                        "message": "failed",
                        "data": None,
                    }

                if payment.status == PaymentStatusEnum.PENDING:
                    # Assuming this is async too
                    payment = await payment_service.check_payment_status(transaction_id)
                    
                if payment.status == PaymentStatusEnum.ACCEPTED:
                    # Assuming this is async too
                    if payment.payable_type == "JobApplication":
                        job_application_service = JobOfferService(session=session)
                        job_offer = await job_application_service.update_job_application_payment(payment_id=int(payment.id),application_id=payment.payable_id)
                    
                    elif payment.payable_type == "StudentApplication":
                        job_offer_service = StudentApplicationService(session=session)
                        job_offer = await job_offer_service.update_student_application_payment(payment_id=int(payment.id),application_id=payment.payable_id)
                    
        

                return {
                    "message": "success",
                    "data": payment,
                }

        return asyncio.run(_check())


import asyncio
import math
from celery import shared_task
from fastapi import Depends
import httpx
from sqlmodel import select
from src.config import settings
from src.api.payments.models import CinetPayPayment, Payment, PaymentStatusEnum
from src.api.payments.schemas import CinetPayInit, PaymentInitInput
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session, get_session_async


class PaymentService:
    
    def __init__(self, session: AsyncSession = Depends(get_session_async)) -> None:
        self.session = session
        
    @staticmethod
    def round_up_to_nearest_5(x: float) -> int:
        return int(math.ceil(x / 5.0)) * 5
    async def get_currency_rates(self, from_currency: str, to_currencies: list[str] = None):
        async with httpx.AsyncClient() as client:
            headers = {
                "apikey": settings.CURRENCY_API_KEY
            }
            symbols = ",".join(to_currencies) if to_currencies else None
            params = {"source": from_currency}
            if symbols:
                params["currencies"] = symbols

            response = await client.get(f"{settings.CURRENCY_API_URL}", headers=headers, params=params)
            data = response.json()
            
            print(data,params)
            return data['quotes']


    async def initiate_payment(self, payment_data: PaymentInitInput):
        
        if payment_data.payment_provider == "CINETPAY":
            payment_currency = "XOF"
        else :
            payment_currency = payment_data.product_currency

        quota =  await self.get_currency_rates(payment_data.product_currency, [payment_currency])
        product_currency_to_payment_currency_rate = quota[f"{payment_data.product_currency}{payment_currency}"]  
        
        quota =  await self.get_currency_rates("USD",[payment_currency,payment_data.product_currency])
        usd_to_payment_currency_rate = quota[f"USD{payment_currency}"]
        usd_to_product_currency_rate = quota[f"USD{payment_data.product_currency}"]
        

        payment = Payment(
            transaction_id=str(uuid.uuid4()),
            product_amount=payment_data.amount,
            product_currency=payment_data.product_currency,
            payment_currency=payment_currency,
            daily_rate=product_currency_to_payment_currency_rate,
            usd_product_currency_rate=usd_to_product_currency_rate,
            usd_payment_currency_rate=usd_to_payment_currency_rate,
            status=PaymentStatusEnum.PENDING,
            payable_id=payment_data.payable.id,
            payable_type=payment_data.payable.__class__.__name__
        )
        
        cinetpay_data = CinetPayInit(
            transaction_id=payment.transaction_id,
            amount= PaymentService.round_up_to_nearest_5(payment_data.amount * product_currency_to_payment_currency_rate),
            currency=payment_currency,
            description=payment_data.description,
            meta=f"{payment_data.payable.__class__.__name__}-{payment_data.payable.id}",
            invoice_data={
                    "payable": payment.payable_type,
                    "payable_id": payment.payable_id
                }
        )
        
        cinetpay_client = CinetPayService(self.session)
        
        try:
            cinetpay_payment = await cinetpay_client.initiate_cinetpay_payment( cinetpay_data)
        except Exception as e:
            return {
                "message": "failed",
                "amount": payment_data.amount,
                "payment_link": None
            }
        
        payment.payment_type_id = cinetpay_payment.transaction_id
        payment.payment_type = cinetpay_payment.__class__.__name__
        
        self.session.add(payment)
        await self.session.commit()
        await self.session.refresh(payment)
        
        return {
            "message": "success",
            "amount" : payment_data.amount,
            "payment_link": cinetpay_payment.payment_url
        }
        
    async def get_payment_by_id(self, payment_id: str):
        statement = select(Payment).where(Payment.id == payment_id)
        result = await self.session.execute(statement)
        payment = result.scalars().one()
        return payment
    
    async def get_payment_by_transaction_id(self, transaction_id: str):
        statement = select(Payment).where(Payment.payment_type_id == transaction_id)
        result = await self.session.execute(statement)
        payment = result.scalars().one()
        return payment

    async def check_payment_status(self, payment : Payment):
        if payment.payment_type == "CinetPayPayment":
            
            cinetpay_client = CinetPayService(self.session)
            cinetpay_payment = await cinetpay_client.get_cinetpay_payment(payment.transaction_id)
            
            if cinetpay_payment is None:
                payment.status = PaymentStatusEnum.ERROR
                await self.session.commit()
                await self.session.refresh(payment)
            else :
                result = await  CinetPayService.check_cinetpay_payment_status(payment.transaction_id)
                if result["data"]["status"] == "ACCEPTED":
                    payment.status = PaymentStatusEnum.ACCEPTED
                    cinetpay_payment.status = PaymentStatusEnum.ACCEPTED
                    cinetpay_payment.amount_received = ["data"]["amount"]
                elif result["data"]["status"] == "REFUSED":
                    payment.status = PaymentStatusEnum.REFUSED
                    cinetpay_payment.status = PaymentStatusEnum.REFUSED
                
                await self.session.commit()
                await self.session.refresh(payment)
                await self.session.refresh(cinetpay_payment)

        return payment
    
    @staticmethod
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

                return {
                    "message": "success",
                    "data": payment,
                }

        return asyncio.run(_check())
        
        
                

class CinetPayService:
    def __init__(self, session: AsyncSession = Depends(get_session_async)) -> None:
        self.session = session


    async def initiate_cinetpay_payment(self, payment_data: CinetPayInit):

        payload = {
            "amount": payment_data.amount,
            "currency": payment_data.currency,
            "description": payment_data.description,
            "apikey": settings.CINETPAY_API_KEY,
            "site_id": settings.CINETPAY_SITE_ID,
            "transaction_id": payment_data.transaction_id,
            "channels": "MOBILE_MONEY",
            "return_url": settings.CINETPAY_RETURN_URL,
            "notify_url": settings.CINETPAY_NOTIFY_URL,
            "meta":payment_data.meta,
            "invoice_data": payment_data.invoice_data
        }

        async with httpx.AsyncClient() as client:
            response = await client.post("https://api-checkout.cinetpay.com/v2/payment", json=payload)
            
            print(response.json(),payload)
            response.raise_for_status()
            data = response.json()

            if data["code"] == "201":
                payment_link = data["data"]["payment_url"]
                
                db_payment = CinetPayPayment(
                    
                    transaction_id=payment_data.transaction_id,
                    amount=payment_data.amount,
                    currency=payment_data.currency,
                    status="PENDING",
                    payment_link=payment_link,
                    payment_url=data["data"]["payment_url"],
                    payment_token=data["data"]["payment_token"],
                    api_response_id=data["api_response_id"]
                )

                self.session.add(db_payment)
                await self.session.commit()
                await self.session.refresh(db_payment)
                return db_payment
            else:
                print(data["message"])
                raise Exception(data["message"])

    @staticmethod
    async def check_cinetpay_payment_status(transaction_id: str):
        payload = {
            "apikey": settings.CINETPAY_API_KEY,
            "site_id": settings.CINETPAY_SITE_ID,
            "transaction_id": transaction_id
        }
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api-checkout.cinetpay.com/v2/payment/check", json=payload)
            response.raise_for_status()
            return response.json()

    async def get_cinetpay_payment(self, transaction_id: str):
        statement = select(CinetPayPayment).where(CinetPayPayment.transaction_id == transaction_id)
        cinetpay_payment = await self.session.execute(statement)
        
        return cinetpay_payment.scalars().first()
    



import asyncio
import json
import math
from celery import shared_task
from fastapi import Depends
import httpx
from sqlalchemy import func, or_
from sqlmodel import select
from src.api.job_offers.service import JobOfferService
from src.api.training.models import StudentApplication
from src.config import settings
from src.api.payments.models import CinetPayPayment, Payment, PaymentStatusEnum
from src.api.payments.schemas import CinetPayInit, PaymentFilter, PaymentInitInput
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session, get_session_async
from src.redis_client import get_from_redis, set_to_redis


class PaymentService:
    
    def __init__(self, session: AsyncSession = Depends(get_session_async)) -> None:
        self.session = session
        
    @staticmethod
    def round_up_to_nearest_5(x: float) -> int:
        return int(math.ceil(x / 5.0)) * 5
    
    async def list_payments(self, filters: PaymentFilter):
        
        statement = (
            select(Payment)
            .where(Payment.delete_at.is_(None))
        )
        count_query = select(func.count(Payment.id)).where(Payment.delete_at.is_(None))
        
        print(filters)

        if filters.search is not None:
            like_clause = or_(
                Payment.transaction_id.contains(filters.search),
                Payment.payable_type.contains(filters.search),
                Payment.payment_type.contains(filters.search),
                Payment.product_currency.contains(filters.search),
            )
            statement = statement.where(like_clause)
            count_query = count_query.where(like_clause)
            
        if filters.currency is not None:
            statement = statement.where(Payment.product_currency == filters.currency)
            count_query = count_query.where(Payment.product_currency == filters.currency)

        if filters.status is not None:
            statement = statement.where(Payment.status == filters.status)
            count_query = count_query.where(Payment.status == filters.status)

        if filters.min_amount is not None:
            statement = statement.where(Payment.product_amount >= filters.min_amount)
            count_query = count_query.where(Payment.product_amount >= filters.min_amount)
            
        if filters.max_amount is not None:
            statement = statement.where(Payment.product_amount <= filters.max_amount)
            count_query = count_query.where(Payment.product_amount <= filters.max_amount)
            
        if filters.date_from is not None:
            statement = statement.where(Payment.created_at >= filters.date_from)
            count_query = count_query.where(Payment.created_at >= filters.date_from)
            
        if filters.date_to is not None:
            statement = statement.where(Payment.created_at <= filters.date_to)
            count_query = count_query.where(Payment.created_at <= filters.date_to)

        if filters.order_by == "created_at":
            statement = statement.order_by(Payment.created_at if filters.asc == "asc" else Payment.created_at.desc())
        elif filters.order_by == "amount":
            statement = statement.order_by(Payment.product_amount if filters.asc == "asc" else Payment.product_amount.desc())
        elif filters.order_by == "status":
            statement = statement.order_by(Payment.status if filters.asc == "asc" else Payment.status.desc())

        total_count = (await self.session.execute(count_query)).scalar_one()

        statement = statement.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)
        result = await self.session.execute(statement)
        return result.scalars().all(), total_count
    
    async def get_payment_by_payable(self, payable_id: str, payable_type: str):
        statement = select(Payment).where(Payment.payable_id == payable_id).where(Payment.payable_type == payable_type)
        result = await self.session.execute(statement)
        payment = result.scalars().first()
        return payment
    
    async def get_payment_by_transaction_id(self, transaction_id: str):
        statement = select(Payment).where(Payment.transaction_id == transaction_id)
        result = await self.session.execute(statement)
        payment = result.scalars().first()
        return payment
        
    async def get_payment_by_payment_type(self, payment_type: str, payment_type_id: str):
        statement = select(Payment).where(Payment.payment_type == payment_type).where(Payment.payment_type_id == payment_type_id)
        result = await self.session.execute(statement)
        payment = result.scalars().first()
        return payment
    
    async def get_currency_rates(self, from_currency: str, to_currencies: list[str] = None):
        
        cache_key = f"currency:{from_currency}:{','.join(to_currencies) if to_currencies else 'ALL'}"

        # Check cache
        cached = await get_from_redis(cache_key)
        if cached:
            return json.loads(cached)
        
        async with httpx.AsyncClient() as client:
            headers = {
                "apikey": settings.CURRENCY_API_KEY
            }
            symbols = ",".join(to_currencies) if to_currencies else None
            params = {"source": from_currency}
            if symbols:
                params["currencies"] = symbols
            #print(params,headers,settings.CURRENCY_API_URL)
            response = await client.get(f"{settings.CURRENCY_API_URL}", headers=headers, params=params)
            data = response.json()
            rates = data['quotes']
            #print(data,params)
        await set_to_redis(cache_key, json.dumps(rates), ex=14400)
        return rates

    async def initiate_payment(self, payment_data: PaymentInitInput,is_swallow: bool = False):
        
        if payment_data.payment_provider == "CINETPAY":
            payment_currency = "XAF"
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
            status=PaymentStatusEnum.PENDING.value,
            payable_id= str(payment_data.payable.id),
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
                },
            customer_name=payment_data.customer_name,
            customer_surname=payment_data.customer_surname,
            customer_email=payment_data.customer_email,
            customer_phone_number=payment_data.customer_phone_number,
            customer_address=payment_data.customer_address,
            customer_city=payment_data.customer_city,
            customer_country=payment_data.customer_country
        )
        
        cinetpay_client = CinetPayService(self.session)
        
        try:
            if is_swallow:
                result = await cinetpay_client.initiate_cinetpay_swallow_payment(cinetpay_data)
            else :
                result = await cinetpay_client.initiate_cinetpay_payment( cinetpay_data)
        except Exception as e:
            return {
                "success": False,
                "message":"unable to initiate payment",
                "amount": payment_data.amount,
                "payment_link": None,
                "transaction_id": None,
                "payment_provider": payment_data.payment_provider,
                "notify_url": settings.CINETPAY_NOTIFY_URL
            }
        
        if result["status"] == "success":
            cinetpay_payment = result["data"]
        else:
            return {
                "success": False,
                "message": result["message"],
                "amount": payment_data.amount,
                "payment_link": None,
                "transaction_id": None,
                "payment_provider": payment_data.payment_provider,
                "notify_url": settings.CINETPAY_NOTIFY_URL
            }
        
        payment.payment_type_id = str(cinetpay_payment.id)
        payment.payment_type = cinetpay_payment.__class__.__name__
        
        self.session.add(payment)
        await self.session.commit()
        await self.session.refresh(payment)
        
        return {
            "success": True,
            "payment_provider": payment_data.payment_provider,
            "amount" : payment_data.amount,
            "payment_link": cinetpay_payment.payment_url,
            "transaction_id": cinetpay_payment.transaction_id,
            "notify_url": settings.CINETPAY_NOTIFY_URL,
            "message": ''
        }
        
    async def get_payment_by_id(self, payment_id: str):
        statement = select(Payment).where(Payment.id == payment_id)
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
                
                if result["data"]["status"] : #== "ACCEPTED":
                    payment.status = PaymentStatusEnum.ACCEPTED.value
                    cinetpay_payment.status = PaymentStatusEnum.ACCEPTED.value
                    cinetpay_payment.amount_received = result["data"]["amount"]
                    
                    if payment.payable_type == "JobApplication":
                        job_application_service = JobOfferService(session=self.session)
                        job_offer = await job_application_service.update_job_application_payment(payment_id=int(payment.id),application_id=payment.payable_id)
                    
                    elif payment.payable_type == "StudentApplication":
                        statement = select(StudentApplication).where(StudentApplication.id == payment.payable_id)
                        result = await self.session.execute(statement)
                        student_application = result.scalars().one()
                        student_application.payment_id = payment.id
                        await self.session.commit()
                        await self.session.refresh(student_application)
                    
                elif result["data"]["status"] == "REFUSED":
                    payment.status = PaymentStatusEnum.REFUSED.value
                    cinetpay_payment.status = PaymentStatusEnum.REFUSED.value
                
                await self.session.commit()
                await self.session.refresh(payment)
                await self.session.refresh(cinetpay_payment)

        return payment
    
   

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
            "channels": "ALL",
            "return_url": settings.CINETPAY_RETURN_URL,
            "notify_url": settings.CINETPAY_NOTIFY_URL,
            "meta":payment_data.meta,
            "invoice_data": payment_data.invoice_data,
        }
        
        if payment_data.customer_name:
            payload["customer_name"] = payment_data.customer_name
        if payment_data.customer_surname:
            payload["customer_surname"] = payment_data.customer_surname
        if payment_data.customer_email:
            payload["customer_email"] = payment_data.customer_email
        if payment_data.customer_phone_number:
            payload["customer_phone_number"] = payment_data.customer_phone_number
        if payment_data.customer_address:
            payload["customer_address"] = payment_data.customer_address
        if payment_data.customer_city:
            payload["customer_city"] = payment_data.customer_city
        if payment_data.customer_country:
            payload["customer_country"] = payment_data.customer_country
        if payment_data.customer_state:
            payload["customer_state"] = payment_data.customer_state
        if payment_data.customer_zip_code:
            payload["customer_zip_code"] = payment_data.customer_zip_code
            
        payload["customer_zip_code"] = "065100"
        
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api-checkout.cinetpay.com/v2/payment", json=payload)
            
            print(response.status_code,response.json(),payload)
            if response.status_code == 400:
                data = response.json()
                return {
                    "status": "error",
                    "code":data["code"] ,
                    "message": data["message"] + " : " + data["description"]
                }
                
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
                return {
                    "status": "success",
                    "data": db_payment
                }
            else:
                print(data["message"])
                raise Exception(data["message"])

    async def initiate_cinetpay_swallow_payment(self, payment_data: CinetPayInit):
        db_payment = CinetPayPayment(
                    
                transaction_id=payment_data.transaction_id,
                amount=payment_data.amount,
                currency=payment_data.currency,
                status="PENDING",
            )

        self.session.add(db_payment)
        await self.session.commit()
        await self.session.refresh(db_payment)
        return db_payment

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
    


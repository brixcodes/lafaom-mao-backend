from fastapi import Depends
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session_async
from src.api.auth.models import RefreshToken,TempUser,ForgottenPAsswordCode,ChangeEmailCode,AuthUserProvider,AuthTempCode
from src.api.auth.schemas import Provider, RegisterProviderInput
from src.api.user.service import UserService
from sqlmodel import select, delete
from datetime import timedelta,datetime,timezone
from passlib.context import CryptContext
from src.api.auth.utils import get_password_hash
from src.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, session: AsyncSession = Depends(get_session_async)) -> None:
        self.session = session

    async def generate_refresh_token(self, user_id:str,expires_delta: timedelta | None = None  ):
        
        expires_at = datetime.now(timezone.utc) + (expires_delta if expires_delta else timedelta(minutes=3600))
        token = secrets.token_urlsafe(112)  # Generate a random token
            
        # Check if the token already exists in the database
        
        existing_token = await self.get_by_token(token)
        if existing_token is None:
            # If not, store it and return
            new_access_token = RefreshToken(token=  get_password_hash(token) , user_id=user_id,expires_at = expires_at)
            await self.session.merge(new_access_token)
            await self.session.commit()
            return new_access_token ,token

    

    async def get_by_token(self, id: str):
        statement = select(RefreshToken).where(RefreshToken.id == id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_token_valid(self, token: str):
        statement = select(RefreshToken).where(RefreshToken.token == token).where(RefreshToken.expires_at >= datetime.now(timezone.utc))
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def delete(self, token: str):
        statement = delete(RefreshToken).where(RefreshToken.token == token)
        await self.session.execute(statement)
        await self.session.commit()

    async def get_temp_user(self, email:str,code:str  ):
        
        statement = select(TempUser).where(TempUser.email == email).where(TempUser.code == code)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_forgotten_password_code(self, account:str,code:str  ):
        
        statement = select(ForgottenPAsswordCode).where(ForgottenPAsswordCode.account == account).where(ForgottenPAsswordCode.code == code)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
    
    async def make_temp_user_used(self, temp_id  ):
        
        statement = select(TempUser).where(TempUser.id == temp_id)
        result = await self.session.execute(statement)
        temp_user = result.scalar_one_or_none()
        temp_user.active = False
        await self.session.commit()
        
        return temp_user
        
        return temp_user.first()
    
    async def get_change_email_code(self, account:str,code:str , user_id : str ) -> ChangeEmailCode  | None:
        
        statement = select(ChangeEmailCode).where(ChangeEmailCode.account == account).where(ChangeEmailCode.code == code).where(ChangeEmailCode.user_id == user_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
    
    async def save_change_email_code(self,user_id :str ,  account : str, code : str   ):
        
        code = ChangeEmailCode(account=account,code=code,user_id=user_id,end_time=datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_CODE_EXPIRE_MINUTES))
        await self.session.merge(code)
        await self.session.commit()
        return code
    
    async def save_forgotten_password_code(self,user_id :str , account : str, code : str  ):
        
        code = ForgottenPAsswordCode(user_id=user_id,account=account,code=code,end_time=datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_CODE_EXPIRE_MINUTES))
        await self.session.merge(code)
        await self.session.commit()
        return code
    
    async def save_temp_user(self, input : dict  ):
        input["password"] = pwd_context.hash(input["password"])
        temp_user = TempUser(**input)
        await self.session.merge(temp_user)
        await self.session.commit()
        return temp_user
    
    async def make_forgotten_password_used(self, id : int  ):
        
        statement = select(ForgottenPAsswordCode).where(ForgottenPAsswordCode.id == id)
        result = await self.session.execute(statement)
        code = result.scalar_one_or_none()
        code.active = False
        await self.session.commit()
        
        
        return code
        
    async def make_change_account_used(self, id : int  ):
        
        statement = select(ChangeEmailCode).where(ChangeEmailCode.id == id)
        result = await self.session.execute(statement)
        code = result.scalar_one_or_none()
        code.active = False
        await self.session.commit()
        
        return code
    
    async def add_user_provider(self,user_id: str, provider : Provider , user_provider_id : str) : 
        
        user_provider = AuthUserProvider(user_provider_id=user_provider_id,user_id=user_id,provider=provider)
        await self.session.merge(user_provider)
        await self.session.commit()
        return user_provider
    
    async def get_user_provider(self,provider : Provider , user_provider_id : str) : 
        
        statement = (select(AuthUserProvider)
                        .where(AuthUserProvider.user_provider_id == user_provider_id)
                        .where(AuthUserProvider.provider == provider)
                    )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
    
    
    async def make_provider_auth(self,provider : Provider , user_provider_id : str,user_input : RegisterProviderInput) : 
        user_service = UserService(session =self.session)
        
        user_provider = await self.get_user_provider(provider=provider, user_provider_id=user_provider_id)
    
        if user_provider == None :
            
            user = await user_service.get_by_email(user_email= user_input.email)
            
            if user == None :
                user_input.password = secrets.token_urlsafe(8)

                user = await user_service.create(user_input)
            
            user_provider = await self.add_user_provider(user_id=user.id,user_provider_id=user_provider_id,provider=provider)
        
        code = await self.create_temp_auth_code(user_id=user_provider.user_id)
        
        return code.code 

    async def make_provider_register(self,provider : Provider , user_provider_id : str,user_input : RegisterProviderInput) : 
        user_service = UserService(session =self.session)
        
        user_provider = await self.get_user_provider(provider=provider, user_provider_id=user_provider_id)
    
        if user_provider == None :
            
            user = await user_service.get_by_email(user_email= user_input.email)
            
            if user == None :
                user_input.password = secrets.token_urlsafe(8)

                user = await user_service.create(user_input)
            
            user_provider = await self.add_user_provider(user_id=user.id,user_provider_id=user_provider_id,provider=provider)
        
        user = await user_service.get_by_id(user_id=user_provider.user_id)
        
        return user 


    
    async def create_temp_auth_code(self,user_id: str,expires_delta = None) : 
        
        expires_at = datetime.now(timezone.utc) + (expires_delta if expires_delta else timedelta(minutes=3600))
        token = secrets.token_urlsafe(144)
        auth_code = AuthTempCode(code=token,user_id=user_id,end_time=expires_at)
        await self.session.merge(auth_code)
        await self.session.commit()
        return auth_code
    
    async def delete_temp_auth_code(self,code: str) : 
        
        statement = select(AuthTempCode).where(AuthTempCode.code == code)
        result = await self.session.execute(statement)
        auth_code = result.scalar_one_or_none()
        if auth_code == None :
            return None
        
        await self.session.delete(auth_code)
        await self.session.commit()
        
        return auth_code


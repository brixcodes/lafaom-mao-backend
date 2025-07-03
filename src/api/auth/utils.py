from typing import Annotated, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from src.api.user.service import UserService
from src.helper.schemas import BaseOutFail,ErrorMessage
from src.api.user.models import  User
import random
import string
import jwt
from datetime import datetime, timedelta, timezone
from src.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = HTTPBearer()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes= settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt




async def get_current_user_id(token: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)] ):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=BaseOutFail(
                message=ErrorMessage.INVALID_TOKEN.description,
                error_code= ErrorMessage.INVALID_TOKEN.value
                
            ).model_dump(),
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    
    except InvalidTokenError:
        raise credentials_exception

async def get_current_user(user_id: Annotated[str, Depends(get_current_user_id)],user_service:Annotated[UserService, Depends()] ):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=BaseOutFail(
                message=ErrorMessage.COULD_NOT_VALIDATE_CREDENTIALS.description,
                error_code= ErrorMessage.COULD_NOT_VALIDATE_CREDENTIALS.value
                
            ).model_dump(),
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user =  await user_service.get_by_id(user_id= user_id)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.status:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,  detail=BaseOutFail(
                message=ErrorMessage.USER_NOT_ACTIVE.description,
                error_code= ErrorMessage.USER_NOT_ACTIVE.value
                
            ).model_dump() )
    
    
    return current_user



def check_permissions(required_permissions: List[str]):
    """ Dependency to check if the user has required permissions. """
    async def permission_checker(current: Annotated[User, Depends(get_current_user)]  , user_service:Annotated[UserService, Depends()]):
        val = await user_service.has_all_permissions(user_id=current.id, permissions=required_permissions)
        if not val :
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=BaseOutFail(
                message=ErrorMessage.ACCESS_DENIED.description,
                error_code= ErrorMessage.ACCESS_DENIED.value
                
            ).model_dump())
        return current
    return permission_checker


def check_roles(required_roles: List[str]):
    """ Dependency to check if the user has required roles. """
    def permission_checker(current: User = Depends(get_current_user)):
        if not current.has_all_role(required_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=BaseOutFail(
                message=ErrorMessage.ACCESS_DENIED.description,
                error_code= ErrorMessage.ACCESS_DENIED.value
                
            ).model_dump())
        return current
    return permission_checker

def generate_random_code(length=5):
    characters = string.ascii_letters + string.digits  # a-z, A-Z, 0-9

    return ''.join(random.choice(characters) for _ in range(length)).upper()
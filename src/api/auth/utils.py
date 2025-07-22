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
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import httpx
from firebase_admin import auth as firebase_auth


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



async def verify_google_token(token: str, platform: str = "web"):
    
    
    try:
        idinfo = id_token.verify_oauth2_token(id_token=token, request=google_requests.Request())
        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise HTTPException(status_code=403, detail="Invalid token issuer")

        # Ensure it was issued to one of your apps
        #if idinfo["aud"] == settings.GOOGLE_CLIENT_ID and platform == "web":
        #    raise HTTPException(status_code=403, detail="Invalid audience")
    
        return {
                "provider_user_id": idinfo["sub"],
                "email": idinfo["email"],
                "first_name": idinfo.get("given_name", ""),
                "last_name": idinfo.get("family_name", ""),
                "picture": idinfo.get("picture")
            }
    except Exception as e:
        print(e)
        return None



async def verify_facebook_token(token: str):
    async with httpx.AsyncClient() as client:
        # Get user info
        user_info_url = f"https://graph.facebook.com/me?fields=id,first_name,last_name,email,picture&access_token={token}"
        resp = await client.get(user_info_url)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return {
            "provider_user_id": data["id"],
            "email": data.get("email"),
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "picture": data.get("picture", {}).get("data", {}).get("url")
        }



async def verify_firebase_token(token: str):
    
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return {
                "provider_user_id": decoded_token["uid"],
                "email": decoded_token.get("email", ""),
                "first_name": decoded_token.get("name", "").split(" ")[0] if decoded_token.get("name") else "",
                "last_name": decoded_token.get("name", "").split(" ")[1] if decoded_token.get("name") and len(decoded_token["name"].split(" ")) > 1 else "",
                "picture": decoded_token.get("picture")
        }
    
    except Exception as e:
        print(e)
        
        return None
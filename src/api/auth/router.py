from datetime import timedelta
from typing import Annotated
from fastapi import Depends , HTTPException, status, APIRouter,BackgroundTasks,UploadFile,File,Request,Response
from src.api.user.models import DeviceType, User
from src.api.auth.schemas import (CheckPermission, Token,LoginInput,RegisterInput, UpdateDeviceInput,ValidateAccountInput,
                                ValidateForgottenPasswordCode,ValidateChangeEmailCode,UpdateAccountSettingInput,
                                ChangeAttributeInput,RefreshTokenInput,UpdateUserInput,UserTokenOut,
                                UpdatePasswordInput,Provider,ProviderURL,RegisterProviderInput,AuthCodeInput)
from src.api.auth.utils import (get_current_active_user,verify_password,
                                generate_random_code,create_access_token)
from src.helper.notifications import (ChangeAccountNotification,ForgottenPasswordNotification,AccountVerifyNotification,NotificationChannel)
from src.config import settings
from src.api.user.service import UserService
from src.api.auth.service import AuthService
from fastapi.responses import RedirectResponse, JSONResponse
from src.api.user.schemas import  UserOutSuccess
from src.helper.schemas import ErrorMessage,BaseOutFail,BaseOutSuccess
from datetime import datetime, timezone
import re
import httpx

from src.helper.utils import delete_file, upload_file


router = APIRouter()


@router.post("/token", response_model=UserTokenOut | BaseOutSuccess)
async def login_for_access_token( request: Request,
    form_data: LoginInput, user_service: UserService = Depends(), token_service: AuthService = Depends()
) -> UserTokenOut | BaseOutSuccess:
    user = await user_service.get_by_account(form_data.account)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=BaseOutFail(
                message=ErrorMessage.INCORRECT_EMAIL_OR_PASSWORD.description,
                error_code=ErrorMessage.INCORRECT_EMAIL_OR_PASSWORD.value
            ).model_dump(),
            headers={"WWW-Authenticate": "Bearer"}
        )

    refresh_token, token = await token_service.generate_refresh_token(user_id=user.id)
    access_token = create_access_token(data={"sub": user.id})


    return {
        "access_token": Token(
            token=access_token, token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=token, device_id=refresh_token.id
        ),
        "user": user
    }


@router.post("/refresh-token", response_model=UserTokenOut)
async def get_token_from_refresh_token(request: Request,
    form_data: RefreshTokenInput, user_service: UserService = Depends(), token_service: AuthService = Depends()
) -> UserTokenOut:
    
    token = await token_service.get_by_token(id=form_data.device_id)   

    if token is None or not verify_password(form_data.refresh_token,token.token  ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=BaseOutFail(
                message=ErrorMessage.REFRESH_TOKEN_NOT_FOUND.description,
                error_code=ErrorMessage.REFRESH_TOKEN_NOT_FOUND.value,
            ).model_dump(),
            headers={"WWW-Authenticate": "Bearer"},
        )    
    
    if token.expires_at.tzinfo is None:
        token.expires_at = token.expires_at.replace(tzinfo=timezone.utc)    
    
    if token.expires_at <= datetime.now(timezone.utc)  : 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                    message=ErrorMessage.REFRESH_TOKEN_HAS_EXPIRED.description,
                    error_code= ErrorMessage.REFRESH_TOKEN_HAS_EXPIRED.value
                ).model_dump()
        )

    user = await user_service.get_by_id( user_id=token.user_id )
    
    access_token = create_access_token(
        data={"sub": user.id})

    return {
            "access_token" : Token(
                token=access_token, token_type="bearer", expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,refresh_token= form_data.refresh_token,device_id = form_data.device_id  
            ),
            "user" : user
        }


@router.post("/register")
async def register(
    register_input: RegisterInput, user_service : Annotated[UserService , Depends()], token_service : Annotated[AuthService, Depends()],background_tasks: BackgroundTasks
):
    if register_input.email != None:
        register_input.phone_number = None
        user_email = await user_service.get_by_email(register_input.email)
        if user_email is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=BaseOutFail(
                        message=ErrorMessage.EMAIL_ALREADY_TAKEN.description,
                        error_code= ErrorMessage.EMAIL_ALREADY_TAKEN.value
                    ).model_dump()
            )
    
    elif register_input.phone_number != None:
        register_input.email = None    
        user_phone = await user_service.get_by_phone(register_input.phone_number)
        if user_phone is not None:  
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=BaseOutFail(
                    message=ErrorMessage.PHONE_NUMBER_ALREADY_TAKEN.description,
                    error_code= ErrorMessage.PHONE_NUMBER_ALREADY_TAKEN.value
                ).model_dump()
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                    message=ErrorMessage.EMAIL_OR_PHONE_NUMBER_REQUIRED.description,
                    error_code= ErrorMessage.EMAIL_OR_PHONE_NUMBER_REQUIRED.value
                ).model_dump()
        )
        
    code = generate_random_code()  
    input = register_input.model_dump()
    input["code"]=   code 
    input['end_time'] =  datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_CODE_EXPIRE_MINUTES)

    temp  = await  token_service.save_temp_user(input)
    
    AccountVerifyNotification(
            email=temp.email,
            phone_number=temp.phone_number,
            code=code,
            time = settings.OTP_CODE_EXPIRE_MINUTES
            
        ).send_notification()
    
    return {
        "message": "Save successfully",
        "data" : {
                "email" :temp.email
            },
        "code" : code,
        "success": True
    }


@router.post("/validate-account",response_model=UserTokenOut)
async def validate_account(response: Response,
    validate_input: ValidateAccountInput, user_service : Annotated[UserService , Depends()], token_service : Annotated[AuthService, Depends()]
):
    if validate_input.email != None:
        user_email = await  user_service.get_by_email(validate_input.email)
        if user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=BaseOutFail(
                        message=ErrorMessage.EMAIL_ALREADY_TAKEN.description,
                        error_code= ErrorMessage.EMAIL_ALREADY_TAKEN.value
                    ).model_dump()
            )
            
    elif validate_input.phone_number != None:    
        user_phone = await  user_service.get_by_phone(validate_input.phone_number)
        if user_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=BaseOutFail(
                        message=ErrorMessage.PHONE_NUMBER_ALREADY_TAKEN.description,
                        error_code= ErrorMessage.PHONE_NUMBER_ALREADY_TAKEN.value
                    ).model_dump()
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                    message=ErrorMessage.EMAIL_OR_PHONE_NUMBER_REQUIRED.description,
                    error_code= ErrorMessage.EMAIL_OR_PHONE_NUMBER_REQUIRED.value
                ).model_dump()
        )        
    
    temp_user = await  token_service.get_temp_user(email=validate_input.email,code=validate_input.code)        
    if  temp_user == None :
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                    message=ErrorMessage.EMAIL_NOT_FOUND.description,
                    error_code= ErrorMessage.EMAIL_NOT_FOUND.value
                ).model_dump()
        )

    if temp_user.end_time.tzinfo is None:
        temp_user.end_time = temp_user.end_time.replace(tzinfo=timezone.utc)   
    
    if not temp_user.active  : 
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                    message=ErrorMessage.CODE_ALREADY_USED.description,
                    error_code= ErrorMessage.CODE_ALREADY_USED.value
                ).model_dump()
        )

    
    if temp_user.end_time <= datetime.now(timezone.utc) : 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                    message=ErrorMessage.CODE_HAS_EXPIRED.description,
                    error_code= ErrorMessage.CODE_HAS_EXPIRED.value
                ).model_dump()
        )
        
    input = RegisterInput(**temp_user.get_user_input())
    
    user = await  user_service.create( input,password_hash=True)
    await token_service.make_temp_user_used(temp_id=temp_user.id)
    
    refresh_token, token = await  token_service.generate_refresh_token(user_id=user.id)
    
    response.set_cookie(
        key="device_id", 
        value=refresh_token.id,
        max_age=60*60*24*30,  # 1 year expiration
        secure=True,            # Send only over HTTPS
        httponly=True,          # Make the cookie inaccessible to JavaScript
        samesite="None"          # Prevent sending in cross-site requests
    )
    
    access_token = create_access_token(
        data={"sub": user.id})

    return {
            "access_token" : Token(
                token=access_token, token_type="bearer", expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,refresh_token= token,device_id=refresh_token.id
            ),
            "user" :user
        }

@router.post("/password-forgotten")
async def password_forgotten(
    input: ChangeAttributeInput,  token_service : Annotated[AuthService, Depends()], user_service : Annotated[UserService , Depends()],
):
    
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'  # Simple regex for email validation
    if not re.match(email_regex, input.account):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                    message=ErrorMessage.PHONE_NUMBER_NOT_SUPPORTED.description,
                    error_code= ErrorMessage.PHONE_NUMBER_NOT_SUPPORTED.value
                ).model_dump()
        )
        
    user =await user_service.get_by_email(user_email=input.account)   
    
    
    if user == None:
        return {
            "message": "Save successfully",
            "data" : {
                "account" :input.account
            },
            "success": True
        }
    
    code = generate_random_code()  

    save_code  = await token_service.save_forgotten_password_code(user_id=user.id,account=input.account,code=code)
    
    ForgottenPasswordNotification(
            email=user.email,
            phone_number=user.phone_number,
            code=code,
            time = 30,
            prefer_notification=user.prefer_notification
            
        ).send_notification()
    
    
    
    return {
            "message": "Save successfully",
            "data" : {
                "account" :input.account
            },
            "code":code,
            "success": True
        }


@router.post("/validate-password-forgotten-code",response_model=UserTokenOut)
async def validate_forgotten_password_code(response: Response,
    validate_input: ValidateForgottenPasswordCode, user_service : Annotated[UserService , Depends()], token_service : Annotated[AuthService, Depends()]
):

    code = await token_service.get_forgotten_password_code(account=validate_input.account,code=validate_input.code)   
    
    if  code == None :
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                    message=ErrorMessage.EMAIL_NOT_FOUND.description,
                    error_code= ErrorMessage.EMAIL_NOT_FOUND.value
                ).model_dump()
        )
        
    if not code.active  : 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                    message=ErrorMessage.CODE_ALREADY_USED.description,
                    error_code= ErrorMessage.CODE_ALREADY_USED.value
                ).model_dump()
        )
        
    if code.end_time.tzinfo is None:
        code.end_time = code.end_time.replace(tzinfo=timezone.utc)           
    if code.end_time <= datetime.now(timezone.utc)  : 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                    message=ErrorMessage.CODE_HAS_EXPIRED.description,
                    error_code= ErrorMessage.CODE_HAS_EXPIRED.value
                ).model_dump()
        )
        
    
    
    user = await user_service.update_password( user_id= code.user_id,password= validate_input.password )
    await token_service.make_forgotten_password_used(id=code.id)
    
    refresh_token, token = await token_service.generate_refresh_token(user_id=user.id)
    
    response.set_cookie(
        key="device_id", 
        value=refresh_token.id,
        max_age=60*60*24*365,   # 1 year expiration
        secure=True,            # Send only over HTTPS
        httponly=True,          # Make the cookie inaccessible to JavaScript
        samesite="None"          # Prevent sending in cross-site requests
    )
    
    access_token = create_access_token(
        data={"sub": user.id})

    return {
            "access_token" : Token(
                token=access_token, token_type="bearer", expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,refresh_token= token,device_id=refresh_token.id
            ),
            "user" : user
        }


@router.post("/change-account")
async def change_account(
    current_user: Annotated[User, Depends(get_current_active_user)],input: ChangeAttributeInput, user_service : Annotated[UserService , Depends()], token_service : Annotated[AuthService, Depends()]
):

    if not verify_password(input.password  , current_user.password) :
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                    message=ErrorMessage.PASSWORD_NOT_CORRECT.description,
                    error_code= ErrorMessage.PASSWORD_NOT_CORRECT.value
                ).model_dump()
        )
    
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'  # Simple regex for email validation
    
    if not re.match(email_regex, input.account):
        user_by_phone = await user_service.get_by_phone(input.account)
        if user_by_phone  :
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=BaseOutFail(
                        message=ErrorMessage.PHONE_NUMBER_ALREADY_TAKEN.description,
                        error_code= ErrorMessage.PHONE_NUMBER_ALREADY_TAKEN.value
                    ).model_dump()
            )
        
    else :
        
        user_by_email = await user_service.get_by_email(input.account)

        if user_by_email :
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=BaseOutFail(
                        message=ErrorMessage.EMAIL_ALREADY_TAKEN.description,
                        error_code= ErrorMessage.EMAIL_ALREADY_TAKEN.value
                    ).model_dump()
            )
    
    
    code = generate_random_code()  

    save_code  = await token_service.save_change_email_code(user_id=current_user.id,account=input.account,code=code)
    
    
    
    if  re.match(email_regex, input.account):
        
        ChangeAccountNotification(
            email=input.account,
            code=code,
            time = settings.OTP_CODE_EXPIRE_MINUTES,
            prefer_notification= NotificationChannel.EMAIL
        ).send_notification()
        
    else :
        ChangeAccountNotification(
            
            phone_number=input.account,
            code=code,
            time = 30,
            prefer_notification= NotificationChannel.WHATSAPP
            
        ).send_notification()    
    

    return {
            "message": "Save successfully",
            "data" : {
                "account" :input.account
            },
            "code":code,
            "success": True
        }


@router.post("/validate-change-account-code", response_model=UserOutSuccess)
async def validate_change_account_code(
    current_user: Annotated[User, Depends(get_current_active_user)],validate_input: ValidateChangeEmailCode, user_service : Annotated[UserService , Depends()], token_service : Annotated[AuthService, Depends()]
):

    code = await token_service.get_change_email_code(account=validate_input.account,code=validate_input.code,user_id =current_user.id)   
    
    if  code == None :
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                    message=ErrorMessage.EMAIL_NOT_FOUND.description,
                    error_code= ErrorMessage.EMAIL_NOT_FOUND.value
                ).model_dump()
        )
    if not code.active  : 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                    message=ErrorMessage.CODE_ALREADY_USED.description,
                    error_code= ErrorMessage.CODE_ALREADY_USED.value
                ).model_dump()
        )
    if code.end_time.tzinfo is None:
        code.end_time = code.end_time.replace(tzinfo=timezone.utc)           
    if code.end_time <= datetime.now(timezone.utc)  : 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                    message=ErrorMessage.CODE_HAS_EXPIRED.description,
                    error_code= ErrorMessage.CODE_HAS_EXPIRED.value
                ).model_dump()
        )

    user = await user_service.update_phone_or_email( user_id= code.user_id,account=code.account  )
    await token_service.make_forgotten_password_used(id=code.id)
    
    return {
        "data" : user,
        "message" : "account change successfully"
    }

@router.get("/me", response_model=UserOutSuccess)
async def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    
    return {
        "data":current_user,
        "message" : "profile fetch successfully"
    }

@router.post("/check-permission", response_model=UserOutSuccess)
async def get_permission(
    current_user: Annotated[User, Depends(get_current_active_user)],input: CheckPermission,user_service : Annotated[UserService , Depends()]
):
    val = await user_service.has_all_permissions(user_id=current_user.id, permissions=input.data)
    if not val :
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=BaseOutFail(
            message=ErrorMessage.ACCESS_DENIED.description,
            error_code= ErrorMessage.ACCESS_DENIED.value
                
        ).model_dump())
    
    
    return {
        "data":current_user,
        "message" : "profile fetch successfully"
    }


@router.post("/update-profile",response_model=UserOutSuccess)
async def update_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],update_input: UpdateUserInput, user_service : Annotated[UserService , Depends()]
):
    user = await user_service.update_profile( user_id= current_user.id,input=update_input  )
    
    return {
        "data":user,
        "message" : "profile updated successfully"
    }


@router.post("/update-android-id",response_model=UserOutSuccess)
async def update_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],input: UpdateDeviceInput, user_service : Annotated[UserService , Depends()]
):
    user = await user_service.update_device_id( user_id= current_user.id, device_type=DeviceType.ANDROID, input=input )
    
    return {
        "data":user,
        "message" : "Android device ID updated successfully"
    }

@router.post("/update-web-id",response_model=UserOutSuccess)
async def update_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],input: UpdateDeviceInput, user_service : Annotated[UserService , Depends()]
):
    user = await user_service.update_device_id( user_id= current_user.id, device_type=DeviceType.WEB, input=input )
    
    return {
        "data":user,
        "message" : "Web device ID updated successfully"
    }
    
@router.post("/update-ios-id",response_model=UserOutSuccess)
async def update_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],input: UpdateDeviceInput, user_service : Annotated[UserService , Depends()]
):
    user = await user_service.update_device_id( user_id= current_user.id, device_type=DeviceType.IOS, input=input )
    
    return {
        "data" : user ,
        "message" : "IOS device ID  updated successfully"
    }    

@router.post("/update-password",response_model=UserOutSuccess)
async def update_password(
    current_user: Annotated[User, Depends(get_current_active_user)],update_input: UpdatePasswordInput, user_service : Annotated[UserService , Depends()]
):
    if not verify_password(update_input.password  , current_user.password) :
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                    message=ErrorMessage.PASSWORD_NOT_CORRECT.description,
                    error_code= ErrorMessage.PASSWORD_NOT_CORRECT.value
                ).model_dump()
        )
    
    user = await user_service.update_password( user_id= current_user.id,password=update_input.new_password  )
    
    return {
        "data":user,
        "message" : "password change successfully"
    }

@router.post("/update-account-setting",response_model=UserOutSuccess)
async def update_account_setting(
    current_user: Annotated[User, Depends(get_current_active_user)],update_input: UpdateAccountSettingInput, user_service : Annotated[UserService , Depends()]
):

    user = await user_service.update_account_setting( user_id= current_user.id, input=update_input  )
    
    return {
        "data":user,
        "message" : "Account setting updated successfully"
    }


@router.post("/upload-profile-image",response_model=UserOutSuccess)
async def update_profile_image(
    current_user: Annotated[User, Depends(get_current_active_user)],image: Annotated[UploadFile, File()], user_service : Annotated[UserService , Depends()]
):
    name = f"{current_user.first_name}_{current_user.last_name}_profile"
    try :
        document , _ , _ = await upload_file(file=image,location="/profile", name = name)
        delete_file(current_user.picture)
    
    except Exception as e :
        print("Error when uploading profile image :" ,e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BaseOutFail(
                    message=ErrorMessage.UNKNOWN_ERROR.description,
                    error_code= ErrorMessage.UNKNOWN_ERROR.value
                ).model_dump()
        )


    user = await user_service.update_profile_image( user_id= current_user.id,picture= document   )
    
    return {
        "data":user,
        "message" : "picture image updated successfully"
    }



@router.get("/{provider}/login")
async def provider_login(request: Request,provider : Provider = Provider.GOOGLE,redirect_url : str = "" ):
    
    request.session['redirect_url'] = redirect_url
    
    if provider == Provider.GITHUB :
        
        auth_url = (
            f"{ProviderURL.GITHUB_AUTHORIZATION_URL}?client_id={settings.GITHUB_CLIENT_ID}"
            f"&redirect_uri={settings.GITHUB_REDIRECT_URL}"
            f"&scope=read:user user:email"
        )
        
    elif provider == Provider.LINKEDIN : 

        auth_url = (
            f"{ProviderURL.LINKEDIN_AUTHORIZATION_URL}?response_type=code"
            f"&client_id={settings.LINKEDIN_CLIENT_ID}"
            f"&redirect_uri={settings.LINKEDIN_REDIRECT_URL}"
            f"&scope=r_liteprofile%20r_emailaddress"
        )
    elif provider == Provider.GOOGLE :
        
        auth_url = (
            f"{ProviderURL.GOOGLE_AUTHORIZATION_URL}?response_type=code"
            f"&client_id={settings.GOOGLE_CLIENT_ID}"
            f"&redirect_uri={settings.GOOGLE_REDIRECT_URL}"
            f"&scope=email%20profile"
            f"&access_type=offline"
            f"&prompt=consent"
        )  
    
    elif provider == Provider.FACEBOOK :
        auth_url = (
            "https://www.facebook.com/v16.0/dialog/oauth?"
            f"client_id={settings.FACEBOOK_CLIENT_ID}"
            f"&redirect_uri={settings.FACEBOOK_REDIRECT_URL}"
            f"&scope=email,public_profile"
        )
        
    else :
        raise HTTPException(
            status_code=400, 
            detail=BaseOutFail(
                message=ErrorMessage.PROVIDER_NOT_FOUND.description,
                error_code= ErrorMessage.PROVIDER_NOT_FOUND.value
            ).model_dump()
        )     

    return RedirectResponse(auth_url)

@router.get("/github/callback",response_model=UserTokenOut)
async def github_callback(request: Request,code: str, token_service : Annotated[AuthService, Depends()]):
    # Exchange code for access token
    
    headers = {"Accept": "application/json"}
    
    data = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.GITHUB_REDIRECT_URL,
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(ProviderURL.GITHUB_TOKEN_URL, headers=headers, data=data)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, 
                detail=BaseOutFail(
                    message=ErrorMessage.FAILED_TO_OBTAIN_TOKEN.description,
                    error_code= ErrorMessage.FAILED_TO_OBTAIN_TOKEN.value
                ).model_dump()
            )   
        access_token = response.json().get("access_token")

        headers.update({"Authorization": f"token {access_token}"})
    
    
        response = await client.get(ProviderURL.GITHUB_USER_INFO_URL, headers=headers)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=BaseOutFail(
                    message=ErrorMessage.FAILED_TO_OBTAIN_USER_INFO.description,
                    error_code= ErrorMessage.FAILED_TO_OBTAIN_USER_INFO.value
                ).model_dump()
            )
            
        user_info = response.json()
        
    
    user_input = RegisterProviderInput(
                    first_name= user_info["name"] or "",
                    last_name= user_info["name"] or "",
                    email= user_info["email"],
                    phone_number=None,
                    lang="en",
                    picture = user_info["avatar_url"],
                    country_code="cmr"
                ) 
    
    code = await token_service.make_provider_auth(user_provider_id=f'{user_info["id"]}',provider=Provider.GITHUB,user_input=user_input)
    
    redirect_url = f"{request.session.get('redirect_url')}?code={code}" 
    
    return RedirectResponse(redirect_url)


@router.get("/google/callback",response_model=UserTokenOut)
async def google_callback(request: Request,code: str, token_service : Annotated[AuthService, Depends()]):
    # Exchange the authorization code for an access token
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URL,
        "grant_type": "authorization_code",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with httpx.AsyncClient() as client:
        token_response = await client.post(ProviderURL.GOOGLE_TOKEN_URL, data=data, headers=headers)
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=token_response.status_code,
                detail=BaseOutFail(
                    message=ErrorMessage.FAILED_TO_OBTAIN_TOKEN.description,
                    error_code= ErrorMessage.FAILED_TO_OBTAIN_TOKEN.value
                ).model_dump()
            )
        token_data = token_response.json()
        access_token = token_data["access_token"]

        # Use the access token to get user info
        user_info_response = await client.get(ProviderURL.GOOGLE_USER_INFO_URL, headers={"Authorization": f"Bearer {access_token}"})
        if user_info_response.status_code != 200:
            raise HTTPException(
                status_code=user_info_response.status_code,
                detail=BaseOutFail(
                    message=ErrorMessage.FAILED_TO_OBTAIN_USER_INFO.description,
                    error_code= ErrorMessage.FAILED_TO_OBTAIN_USER_INFO.value
                ).model_dump()
            )
        user_info = user_info_response.json()
    
    user_input = RegisterProviderInput(
                    first_name=user_info["given_name"],
                    last_name=user_info["family_name"],
                    email= user_info["email"],
                    phone_number= None,
                    lang="en",
                    picture = user_info["picture"],
                    country_code="cmr"
                )

    code = await token_service.make_provider_auth(user_provider_id=user_info["id"],provider=Provider.GOOGLE,user_input=user_input)

    redirect_url = f"{request.session.get('redirect_url')}?code={code}" 
    
    return RedirectResponse(redirect_url)

@router.get("/linkedin/callback",response_model=UserTokenOut)
async def linkedin_callback(request: Request,code: str, token_service : Annotated[AuthService, Depends()]):
    # Exchange the authorization code for an access token
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URL,
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "client_secret": settings.LINKEDIN_CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with httpx.AsyncClient() as client:
        token_response = await client.post(ProviderURL.LINKEDIN_TOKEN_URL, data=data, headers=headers)
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=token_response.status_code,
                detail=BaseOutFail(
                    message=ErrorMessage.FAILED_TO_OBTAIN_TOKEN.description,
                    error_code= ErrorMessage.FAILED_TO_OBTAIN_TOKEN.value
                ).model_dump()
            )
        token_data = token_response.json()
        access_token = token_data["access_token"]

        # Use the access token to get user profile info
        user_info_headers = {"Authorization": f"Bearer {access_token}"}
        
        # Get user basic profile
        user_info_response = await client.get(ProviderURL.LINKEDIN_USER_INFO_URL, headers=user_info_headers)
        if user_info_response.status_code != 200:
            raise HTTPException(
                status_code=user_info_response.status_code,
                detail=BaseOutFail(
                    message=ErrorMessage.FAILED_TO_OBTAIN_USER_INFO.description,
                    error_code= ErrorMessage.FAILED_TO_OBTAIN_USER_INFO.value
                ).model_dump()
            )
        user_info = user_info_response.json()
        # Get user email address
        user_email_response = await client.get(ProviderURL.LINKEDIN_USER_EMAIL_URL, headers=user_info_headers)
        if user_email_response.status_code != 200:
            raise HTTPException(
                status_code=user_email_response.status_code,
                detail=BaseOutFail(
                    message=ErrorMessage.FAILED_TO_OBTAIN_USER_INFO.description,
                    error_code= ErrorMessage.FAILED_TO_OBTAIN_USER_INFO.value
                ).model_dump()
            )
        user_email_data = user_email_response.json()
        email = user_email_data["elements"][0]["handle~"]["emailAddress"]

        user_input = RegisterProviderInput(
                    first_name=user_info["localizedFirstName"],
                    last_name=user_info["localizedLastName"],
                    email= email,
                    phone_number= None,
                    lang="en",
                    picture ="",
                    country_code= "cmr"
                )
    

    code = await token_service.make_provider_auth(user_provider_id=user_info["id"],provider=Provider.LINKEDIN,user_input=user_input)

    redirect_url = f"{request.session.get('redirect_url')}?code={code}" 
    
    return RedirectResponse(redirect_url)

@router.get("/facebook/callback")
async def facebook_callback(request: Request, code: str, token_service: Annotated[AuthService, Depends()]):


    async with httpx.AsyncClient() as client:
        # Step 1: Exchange code for access token
        token_response = await client.get(
            "https://graph.facebook.com/v16.0/oauth/access_token",
            params={
                "client_id": settings.FACEBOOK_CLIENT_ID,
                "redirect_uri": settings.FACEBOOK_REDIRECT_URL,
                "client_secret": settings.FACEBOOK_CLIENT_SECRET,
                "code": code,
            },
        )

        if token_response.status_code != 200:
            raise HTTPException(
                    status_code=token_response.status_code,
                    detail=BaseOutFail(
                        message=ErrorMessage.FAILED_TO_OBTAIN_TOKEN.description,
                        error_code= ErrorMessage.FAILED_TO_OBTAIN_TOKEN.value
                    ).model_dump()
                )

        access_token = token_response.json().get("access_token")


        # Step 2: Fetch user profile
        user_response = await client.get(
            "https://graph.facebook.com/me",
            params={
                "fields": "id,name,email,picture",
                "access_token": access_token,
            },
        )

        if user_response.status_code != 200:
            raise HTTPException(
                    status_code=user_response.status_code,
                    detail=BaseOutFail(
                        message=ErrorMessage.FAILED_TO_OBTAIN_USER_INFO.description,
                        error_code= ErrorMessage.FAILED_TO_OBTAIN_USER_INFO.value
                    ).model_dump()
                )

        user_data = user_response.json()

        # Step 3: Parse and normalize user info
        name_parts = user_data.get("name", "").split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        email = user_data.get("email")
        picture = user_data.get("picture", {}).get("data", {}).get("url")

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=BaseOutFail(
                    message=ErrorMessage.EMAIL_NOT_FOUND.describe,
                    error_code= ErrorMessage.EMAIL_NOT_FOUND.value
                ).model_dump()
            )

    user_input = RegisterProviderInput(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_number=None,
        lang="en",
        picture=picture,
        country_code="CM"
    )

    # Step 4: Process provider auth & generate code
    provider_user_id = user_data.get("id")
    code = await token_service.make_provider_auth(
        user_provider_id=provider_user_id,
        provider=Provider.FACEBOOK,
        user_input=user_input
    )

        
    redirect_url = f"{request.session.get('redirect_url')}?code={code}"
    return RedirectResponse(redirect_url)



@router.post("/code-auth",response_model=UserTokenOut)
async def code_auth(response: Response,request: Request,
    form_data: AuthCodeInput, token_service : Annotated[AuthService, Depends()],user_service : Annotated[UserService , Depends()]
) :
    code = await token_service.delete_temp_auth_code(form_data.code)
    
    
    if code == None  : 
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=BaseOutFail(
                    message=ErrorMessage.CODE_NOT_EXIST.describe,
                    error_code= ErrorMessage.CODE_NOT_EXIST.value
                ).model_dump()
            )
        
        
    if code.end_time.tzinfo is None:
        code.end_time = code.end_time.replace(tzinfo=timezone.utc) 
    
    if code.end_time <= datetime.now(timezone.utc)  : 
        
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=BaseOutFail(
                    message=ErrorMessage.CODE_HAS_EXPIRED.describe,
                    error_code= ErrorMessage.CODE_HAS_EXPIRED.value
                ).model_dump()
            )
    
    user = await user_service.get_by_id(user_id=code.user_id)
    refresh_token, token = await token_service.generate_refresh_token(user_id=user.id)
    
    response.set_cookie(
        key="device_id", 
        value=refresh_token.id,
        max_age=60*60*24*365,  # 1 year expiration
        secure=True,            # Send only over HTTPS
        httponly=True,          # Make the cookie inaccessible to JavaScript
        samesite="None"          # Prevent sending in cross-site requests
    )
    
    access_token =  create_access_token(data={"sub": user.id})

    return {
            "access_token" : Token(
                token=access_token, token_type="bearer", expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,refresh_token= token,device_id=refresh_token.id
            ),
            "user" :user
        }





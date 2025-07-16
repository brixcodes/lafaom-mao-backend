from fastapi import APIRouter, Depends, HTTPException,status
from typing import Annotated

from fastapi.responses import JSONResponse
from src.helper.utils import NotificationHelper
from src.redis_client import get_from_redis, set_to_redis

from src.api.auth.utils import  get_current_active_user
from src.api.user.dependencies import get_user
from src.api.user.models import User
from src.helper.schemas import BaseOutFail, ErrorMessage
from src.api.user.service import UserService
from src.api.user.schemas import ( UserListInput, UserListOutSuccess, UserOutSuccess,  UserUpdateInput, UsersOutSuccess)

router = APIRouter()


@router.get("/stats/get-user-stat",tags=["Stats"])
async def get_user_dashboard_stat(current_user: Annotated[User, Depends(get_current_active_user)]):
    
    return  {
        "data" : {
            
        },
        "message" : "Client stats fetch successfully"
    }    
@router.post("/users/list", response_model=UserListOutSuccess,tags=["Users"])
async def read_user_list( input: UserListInput , user_service: UserService = Depends(),):

    users = await user_service.get_users_by_id_lists(user_ids=input.user_ids)
    return  {"data" : users, "message":"Users list fetch successfully" }


@router.get("/users/{user_id}", response_model=UserOutSuccess,tags=["Users"])
async def read_user(user : Annotated[User, Depends(get_user)]):

    return  {"data" : user, "message":"Users fetch successfully" }


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    user_update_input: UserUpdateInput,
    user : Annotated[User, Depends(get_user)],
    user_service: UserService = Depends(),
):
    user_email = await user_service.get_by_email(user_email=user_update_input.email)
    if user_email is not None and user_email.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,            
            detail=BaseOutFail(
                message=ErrorMessage.EMAIL_ALREADY_TAKEN.description,
                error_code= ErrorMessage.EMAIL_ALREADY_TAKEN.value
            ).model_dump()
        )
        
    # user_phone = await user_service.get_by_phone(user_phone=user_update_input.phone_number)
    # if user_phone is not None and user_phone.id != user.id:
        
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,            
    #         detail=BaseOutFail(
    #             message=ErrorMessage.PHONE_NUMBER_ALREADY_TAKEN.description,   
    #             error_code= ErrorMessage.PHONE_NUMBER_ALREADY_TAKEN.value
    #         ).model_dump()
    #     )
    
    user = await user_service.update(user_id, user_update_input)
    
    return  {"data" : user, "message":"Users updated successfully" }



@router.get('/setup-users',tags=["Users"])
async def setup_users(user_service: UserService = Depends()):
    await user_service.permission_set_up()
    
    return  {"data" : "Users setup successfully" }


@router.get('/test-get-data-to-redis',tags=["Test"])
async def get_data_redis(test_number : int):
    cached = await get_from_redis(f"test:{test_number}")
    if cached:
        return  {"data" : cached }

    return  {"message" : "no data" }
    
@router.get('/test-add-data-to-redis',tags=["Test"])
async def add_data_redis(test_number : int):
    await set_to_redis(
                        f"test:{test_number}", f"test:{test_number}", ex=60
                    ) 
    cached = await get_from_redis(f"test:{test_number}")
    if cached:
        return  {"data" : cached }

    return  {"message" : "npo data found after add" }

@router.get('/test-send-email',tags=["Test"])
async def test_email(email : str):
    
    data = {
            "to_email" : email,
            "subject":"Email Validation",
            "template_name":"verify_email.html" ,
            "lang":"en",
            "context":{
                    "code":"AZERTY",
                    "time": 30
                } 
        } 
    NotificationHelper.send_smtp_email(data=data)

    return  {"message" : "email send" }

# @router.delete("/{user_id}")
# async def delete_user(
#     user_id: str,
#     user_service: UserService = Depends(),
#     user: Mapping = Depends(get_user),
# ):
#     user = user_service.delete(user_id)
#     return user    
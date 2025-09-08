from typing import List
from fastapi import Depends
from src.database import get_session_async
from src.api.user.models import (DeviceType, NotificationChannel, PermissionEnum, User, UserPermission, UserRole, Role, RoleEnum, UserStatusEnum)
from src.api.auth.schemas import UpdateDeviceInput, UpdateUserInput, UpdateAccountSettingInput
from sqlmodel import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
import re

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self, session: AsyncSession = Depends(get_session_async)) -> None:
        self.session = session

    async def get(self):
        statement = select(User)
        result = await self.session.execute(statement)
        users = result.scalars().all()
        return users

    async def create(self, user_create_input, password_hash: bool = False):
        if not password_hash:
            user_create_input.password = pwd_context.hash(user_create_input.password)
        user = User(**user_create_input.model_dump())
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: str):
        statement = select(User).where(User.id == user_id)
        result = await self.session.execute(statement)
        user = result.scalars().first()
        return user


    async def get_by_email(self, user_email: str):
        statement = select(User).where(User.email == user_email)
        result = await self.session.execute(statement)
        user = result.scalars().first()
        return user

    async def get_by_account(self, account: str):
        statement = select(User).where(
            or_(User.email == account, User.phone_number == account)
        )
        result = await self.session.execute(statement)
        user = result.scalars().first()
        return user

    async def get_by_phone(self, user_phone: str):
        statement = select(User).where(User.phone_number == user_phone)
        result = await self.session.execute(statement)
        user = result.scalars().first()
        return user
    
    
    async def get_users_by_id_lists(self, user_ids: List[str]):
        statement = select(User).where(
            User.id.in_(user_ids)
        )
        result = await self.session.execute(statement)
        users = result.scalars().all()
        return users

    async def update(self, user_id, user_update_input):
        statement = select(User).where(User.id == user_id)
        result = await self.session.execute(statement)
        user = result.scalars().one()
        for key, value in user_update_input.dict().items():
            setattr(user, key, value)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_password(self, user_id: str, password: str):
        statement = select(User).where(User.id == user_id)
        result = await self.session.execute(statement)
        user = result.scalars().one()
        user.password = pwd_context.hash(password)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_profile_image(self, user_id: str, picture: str):
        statement = select(User).where(User.id == user_id)
        result = await self.session.execute(statement)
        user = result.scalars().one()
        user.picture = picture
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_account_setting(self, user_id: str, input: UpdateAccountSettingInput):
        statement = select(User).where(User.id == user_id)
        result = await self.session.execute(statement)
        user = result.scalars().one()

        if input.prefer_notification is not None:
            user.prefer_notification = input.prefer_notification

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_phone_or_email(self, user_id: str, account: str):
        statement = select(User).where(User.id == user_id)
        result = await self.session.execute(statement)
        user = result.scalars().one()

        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'  # Simple regex for email validation

        if not re.match(email_regex, account):
            user.phone_number = account
        else:
            user.email = account

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_profile(self, user_id: str, input: UpdateUserInput):
        statement = select(User).where(User.id == user_id)
        result = await self.session.execute(statement)
        user = result.scalars().one()

        user.first_name = input.first_name
        user.last_name = input.last_name
        user.country_code = input.country_code
        user.lang = input.lang

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def update_device_id(self, user_id: str,device_type : str , input: UpdateDeviceInput):
        statement = select(User).where(User.id == user_id)
        result = await self.session.execute(statement)
        user = result.scalars().one()
        
        if device_type == DeviceType.ANDROID:
            user.android_token = input.device_id
        elif device_type == DeviceType.IOS:
            user.ios_token = input.device_id
        elif device_type == DeviceType.WEB:
            user.web_token = input.device_id

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    

    

    async def delete_user(self, user_id: str):
        statement = select(User).where(User.id == user_id)
        result = await self.session.execute(statement)
        user = result.scalars().one()
        await self.session.delete(user)
        await self.session.commit()
        return user



    async def permission_set_up(self):
        statement = select(User).where(User.email == "admin@laakam.com")
        result = await self.session.execute(statement)
        user = result.scalars().first()

        if user is None:
            user = User(
                first_name="admin",
                last_name="admin",
                country_code="CM",
                email="admin@laakam.com",
                phone_number="0000000000",
                lang="en",
                status=UserStatusEnum.ACTIVE,
                prefer_notification=NotificationChannel.EMAIL,
                password=pwd_context.hash("admin")
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

        admin = None
        for role in RoleEnum:
            statement = select(Role).where(Role.name == role.value)
            result = await self.session.execute(statement)
            role_data = result.scalars().first()
            if role_data is None:
                role_data = Role(name=role)
                self.session.add(role_data)

            if role_data.name == RoleEnum.ADMIN:
                admin = role_data

        await self.session.commit()
        await self.session.refresh(admin)

        if admin is not None:
            for permission in PermissionEnum:
                statement = (
                    select(UserPermission).where(UserPermission.role_id == admin.id)
                    .where(UserPermission.permission == permission.value)
                )
                result = await self.session.execute(statement)
                user_permission = result.scalars().first()
                if user_permission is None:
                    user_permission = UserPermission(
                        role_id=admin.id,
                        permission=permission.value
                    )
                    self.session.add(user_permission)

        await self.session.commit()

        statement = select(UserRole).where(UserRole.user_id == user.id).where(UserRole.role_id == admin.id)
        result = await self.session.execute(statement)
        user_role = result.scalars().first()

        if user_role is None:
            user_role = UserRole(
                user_id=user.id,
                role_id=admin.id
            )
            self.session.add(user_role)

            await self.session.commit()

        return True

    async def has_all_permissions(self,user_id :str, permissions : list = []) -> bool: 
        statement = select(UserRole.role_id).where(UserRole.user_id == user_id)
        
        roles_result = await self.session.execute(statement)
        roles = roles_result.scalars().all()
        
        statement = (select(UserPermission).where(UserPermission.user_id == user_id or UserPermission.role_id.in_(roles))
                        .where(UserPermission.permission.in_(permissions)))
        
        
        values_result = await self.session.execute(statement)
        values = values_result.all()
        
        if len(values) == len(permissions) :
            return True
        
        return False 
    
    async def has_any_permissions(self,user_id :str,  permissions : list = []) -> bool: 
        statement = select(UserRole.role_id).where(UserRole.user_id == user_id)
        
        roles_result = await self.session.execute(statement)
        roles = roles_result.scalars().all()
    
    
        
        statement = (select(UserPermission).where(UserPermission.user_id == user_id or UserPermission.role_id.in_(roles))
                        .where(UserPermission.permission.in_(permissions)))
        
        
        values_result = await self.session.execute(statement)
        values = values_result.all()
        
        if len(values)> 1 :
            return True
        
        return False 
    
    def has_all_role(self,user_id :str, role : list = []) -> bool: 
        
        roles = self.roles
        
        for elt in roles :
            if not (elt.name in role) :
                return False
        
        return True
    
    def has_any_role(self,user_id :str, role : list = []) -> bool: 
        
        roles = self.roles
        
        for elt in roles :
            if elt.name in role :
                return True
        
        return False



from sqlmodel import  Field
from src.helper.model import CustomBaseModel
from typing import List, Optional
from  datetime import datetime
from sqlalchemy import  JSON, Text


class PostCategory(CustomBaseModel,table=True):
    __tablename__ = "post_categories"
    title: str = Field( max_length=255)
    slug : str = Field( max_length=255, index=True, unique=True)
    description : str =  Field(sa_column=Text,nullable=False)

class Post(CustomBaseModel, table=True):
    __tablename__ = "posts"
    
    user_id: str = Field(foreign_key="users.id", nullable=False)
    author_name: str = Field( max_length=255)
    title: str = Field( max_length=255, index=True, unique=True)
    slug : str = Field( max_length=255, index=True, unique=True)
    cover_image: str = Field(default="", max_length=255)
    summary: str = Field(default=None, max_length=255)
    published_at: Optional[datetime] = Field(default=None)
    tags: List[str] = Field(default=None, sa_column=Field(default=None, sa_column_kwargs={"type_": JSON}).sa_column)  
    category_id : str = Field(foreign_key="post_categories.id", nullable=False)
    
    

class PostSection(CustomBaseModel,table=True):
    
    __tablename__ = "post_sections"
    
    title: str = Field( max_length=255)
    cover_image: Optional[str] = Field(default="", max_length=255)
    Content : str =  Field(sa_column=Text,nullable=False) 
    position : int = Field(default=1)
    post_id : str = Field(foreign_key="posts.id", nullable=False)
    
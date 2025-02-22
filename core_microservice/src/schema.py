from sqlmodel import SQLModel, Field
from typing import List
from sqlalchemy import Text, Column
from pydantic import EmailStr
from datetime import datetime

# schema to create a user
class UserCreate(SQLModel):
    username: str = Field(min_length=5, max_length=100)
    email: EmailStr
    password: str = Field(min_length=7)


class UserLogin(SQLModel):
    email: EmailStr
    password: str

class UserNameTag(SQLModel):
    id: int
    username: str


# story info schema
class StoryInfo(SQLModel):
    name: str
    blurb: str = Field(sa_column=Column(Text))

# schema to create a project
class StoryCreate(SQLModel):
    user_id: int
    info: StoryInfo

# schema to create a chapter
class ChapterCreate(SQLModel):
    story_id: int
    title: str 
    content: str = Field(sa_column=Column(Text))

# schema to update a chapter
class ChapterUpdate(SQLModel):
    id: int
    title: str
    is_published: bool 
    updated_at: datetime = datetime.utcnow()
    content: str = Field(sa_column=Column(Text))

# schema for a chapter response
class ChapterResponse(SQLModel):
    id: int 
    story_id: int 
    is_published: bool 
    title: str
    content: str = Field(sa_column=Column(Text))

# schema for shallow story response
class StoryResponse(SQLModel):
    id: int
    name: str
    blurb: str = Field(sa_column=Column(Text))
    author: UserNameTag

class UIStoriesResponse(SQLModel):
    page: int
    page_count: int
    stories: List[StoryResponse]
    
# schema for user response
class UserResponse(SQLModel):
    id: int
    username: str
    email: str

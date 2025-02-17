from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Text, UniqueConstraint, MetaData
from datetime import datetime

# Create metadata object with naming convention
metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})

# Set SQLModel metadata
SQLModel.metadata = metadata


class User(SQLModel, table=True):

    # main cols
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # relationship
    projects: List["Project"] = Relationship(back_populates='user')


class Project(SQLModel, table=True):

    # main cols
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='user.id')
    name: str = Field(unique=True, index=True)
    created_at: datetime  = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # relationships
    user: Optional["User"] = Relationship(back_populates='projects')
    chapters: List["Chapter"] = Relationship(back_populates='project')


class Chapter(SQLModel, table=True):

    # main cols
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key='project.id')
    title: str = Field(index=True)
    content: str = Field(sa_type=Text)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # relationships
    project: Optional["Project"] = Relationship(back_populates='chapters')

    # constraints
    __table_args__ = (
        UniqueConstraint('project_id', 'title', name='unique_chapter_title_per_project'),
    )

    
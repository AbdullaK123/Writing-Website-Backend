from fastapi import APIRouter, Request, Depends, HTTPException
from sqlmodel import Session
from src.models import User
from src.services.auth import auth_service, get_current_active_user
from src.database import get_db
from src.schema import (
    UserCreate,
    UserLogin,
    UserResponse
)


router = APIRouter(
    prefix='/api/users',
    tags=['users'],
    responses={404:{'description': 'Not found'}}
)


@router.post('/register', response_model=UserResponse)
def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> UserResponse:
    return auth_service.create_user(request, user_data, db)



@router.post('/login', response_model=UserResponse)
def login(
    request: Request,
    login_data: UserLogin,
    db: Session = Depends(get_db)
) -> UserResponse:
    return auth_service.login(request, login_data, db)

    
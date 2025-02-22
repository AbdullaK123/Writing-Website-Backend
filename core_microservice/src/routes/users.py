from fastapi import APIRouter, Request, Depends
from sqlmodel import Session
from src.services.auth import auth_service
from src.schema import UserCreate, UserLogin, UserResponse
from src.models import User
from src.database import get_db

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    responses={404: {"description": "Not Found"}}
)

def create_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email
    )


# create a user
@router.post('/register', response_model=UserResponse)
async def register(
    request: Request,
    user_data: UserCreate,
    db:Session = Depends(get_db)
) -> UserResponse:
    
    user = auth_service.create_user(user_data, db)

    auth_service.create_session(request, user)

    return create_user_response(user)


# log in route
@router.post("/login", response_model=UserResponse)
async def login(
    request: Request,
    login_data: UserLogin,
    db: Session = Depends(get_db)
) -> UserResponse:

    # authenticate the user
    user = auth_service.authenticate_user(login_data, db)

    # create the users session
    auth_service.create_session(request, user)

    return create_user_response(user)
    

# get the current user route
@router.get("/me", response_model=UserResponse)
async def get_user(
    request: Request,
    current_user: User = Depends(
        lambda req=Request, db=Depends(get_db):
        auth_service.get_current_user(req, db)
    )
) -> UserResponse:
    return create_user_response(current_user)

# log out route
@router.post('/logout', response_model=dict[str, str])
async def logout(request: Request) -> dict[str, str]:
    auth_service.clear_session(request)
    return {"message": "Successfully logged out"}
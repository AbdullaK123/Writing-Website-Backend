from passlib.context import CryptContext
from src.database import get_db
from fastapi import Depends, HTTPException, status, Request
from src.schema import UserCreate, UserLogin
from src.models import User
from sqlmodel import Session, select
from pydantic import EmailStr


class AuthService:

    def __init__(self):
        self.pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_session(self, request: Request, user: User) -> None:
        request.session["user_id"] = int(user.id)
        request.session["email"] = user.email
        request.session["username"] = user.username

    def clear_session(self, request: Request) -> None:
        request.session.clear()

    def get_user_by_username(
        self,
        username: str,
        db:Session
    ) -> User:
        try: 
            statement = select(User).where(User.username == username)
            return db.exec(statement).first()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A database error occurred"
            )
        
    def get_user_by_email(
        self,
        email: EmailStr,
        db:Session
    ) -> User:
        try: 
            statement = select(User).where(User.email == email)
            return db.exec(statement).first()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A database error occurred"
            )


    def get_user_by_id(
        self,
        id: int,
        db:Session
    ) -> User:
        try: 
            return db.get(User, id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A database error occurred"
            )

    def create_user(
        self,
        user_data: UserCreate,
        db:Session
    ) -> User:
        try: 
            # check if the user exists
            user = self.get_user_by_username(user_data.username, db)

            if user:
                raise HTTPException(
                    status_code=400,
                    detail="A user already exists with that username"
                )
            
            user = self.get_user_by_email(user_data.email, db)

            if user:
                raise HTTPException(
                    status_code=400,
                    detail="A user already exists with that email"
                )

            # user to create
            user_to_create = User(
                email=user_data.email,
                username=user_data.username,
                password_hash=self.hash_password(user_data.password)
            )
            
            db_user = User.model_validate(user_to_create)

            db.add(db_user)
            db.commit()
            db.refresh(db_user)

            return db_user
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A database error occurred"
            )


    def get_current_user(
        self,
        request: Request,
        db: Session
    ) -> User:
        # try getting the user id
        user_id = request.session.get("user_id")
        if not user_id:
            return None

        # return the user from their id
        user = self.get_user_by_id(user_id, db)
        return user



    def authenticate_user(
        self,
        login_data: UserLogin,
        db: Session
    ) -> User:
        # get the user by email
        user = self.get_user_by_email(login_data.email, db)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if not self.verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        return user

    def require_authenticated(
        self,
        request: Request,
        db: Session
    ) -> User:
        # get the current user
        user = self.get_current_user(request, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        return user


auth_service = AuthService()
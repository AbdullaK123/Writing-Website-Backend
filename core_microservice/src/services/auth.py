from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, Request, Depends, status
from jose import jwt, JWTError
from src.models import User
from typing import Optional, Union
from src.settings import app_config
from src.database import get_db
from sqlmodel import Session, select
from redis import Redis
from datetime import datetime, timedelta
from src.schema import (
    UserCreate,
    UserLogin,
    TokenResponse,
    UserResponse
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

class AuthService:

    def __init__(self):
        self.pwd_context = CryptContext(
            schemes=['bcrypt'],
            deprecated='auto'
        )
        self.redis = Redis(
            host=app_config.REDIS_HOST,
            port=app_config.REDIS_PORT
        )
        try:
            self.redis.ping()
        except Exception as e:
            raise Exception(f"Failed to connect to redis: {e}")

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(
        self,
        data: dict
    ) -> dict:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=int(app_config.TOKEN_EXPIRE_TIME))
        to_encode.update({
            'exp': expire, 'type': "access"
        })
        return jwt.encode(to_encode, app_config.SECRET_KEY, app_config.AUTH_ALGO)
    
    def create_refresh_token(
        self,
        data: dict
    ) -> dict:
        to_encode=data.copy()
        expire = datetime.utcnow() + timedelta(days=int(app_config.REFRESH_TOKEN_EXPIRE_TIME))
        to_encode.update({
            'exp': expire, 'type': "refresh"
        })
        return jwt.encode(to_encode, app_config.SECRET_KEY, app_config.AUTH_ALGO)

    def create_user(
        self,
        request: Request,
        user_data: UserCreate,
        db: Session
    ) -> UserResponse:
        try:

            user = self.get_user(user_data.username, db)

            if user:
                raise HTTPException(
                    status_code=400,
                    detail="A user already exists with that username"
                )

            user_to_create = User(
                username=user_data.username,
                email=user_data.email,
                password_hash=self.hash_password(user_data.password)
            )

            db.add(user_to_create)
            db.commit()
            db.refresh(user_to_create)

            login_data = UserLogin(
                email=user_data.email,
                password=user_data.password
            )

            return self.login(request, login_data, db)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"A database error occurred: {e}"
            )
        

    def verify_refresh_token(
        self,
        refresh_token: str
    ) -> TokenResponse:
        try:

            payload = jwt.decode(refresh_token, app_config.SECRET_KEY, algorithms=[app_config.AUTH_ALGO])

            if payload.get('type') != "refresh":
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token type"
                )
            
            username = payload.get('sub')

            if not username:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token"
                )
            
            token_key = f"refresh_token:{username}:{refresh_token}"

            if not self.redis.exists(token_key):
                raise HTTPException(
                    status_code=401,
                    detail="Token has been revoked"
                )
            
            access_token = self.create_access_token(data={'sub': username})

            return TokenResponse(access_token=access_token, refresh_token=refresh_token)

        except JWTError:
            raise HTTPException(
                status_code=401,
                detail="Invalid token refresh"
            )
        
    def login(
        self,
        request: Request,
        login_data: UserLogin,
        db: Session
    ) -> UserResponse:
        try:
            user = self.authenticate_user(login_data.email, login_data.password, db)

            access_token = self.create_access_token(data={'sub': user.username})
            refresh_token = self.create_refresh_token(data={'sub': user.username})

            self.redis.setex(
                f"refresh_token:{user.username}:{refresh_token}",
                60*60*24*7,
                1
            )

            token_response=TokenResponse(access_token=access_token, refresh_token=refresh_token)

            return UserResponse(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    token_data=token_response
                )
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"A database error occured: {e}"
            )
        
    def logout(
        self,
        user: User,
        refresh_token: str
    ) -> dict:
        try:
            payload = jwt.decode(refresh_token, app_config.SECRET_KEY, algorithms=[app_config.AUTH_ALGO])

            username = payload.get('sub')

            token_key = f"refresh_toke:{username}:{refresh_token}"

            self.redis.delete(token_key)

            return {"message": "Successfully logged out"}

        except JWTError:
            return {"message": "Successfully logged out"}
    
    @staticmethod
    def get_user(
        username: str,
        db: Session
    ) -> Optional[User]:
        statement = select(User).where(User.username == username)
        return db.exec(statement).first()
    
    def authenticate_user(
        self,
        username: str,
        password: str,
        db: Session
    ) -> User:
        user = self.get_user(username, db)
        if not user or not self.verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
        return user
    
    @staticmethod
    def get_current_user(
        db: Session,
        token: str
    ) -> User:
        
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'}
        )
        
        try:

            # decode the token
            payload = jwt.decode(token, app_config.SECRET_KEY, algorithms=[app_config.AUTH_ALGO])

            # find the username and if it is none raise an exception
            username: str = payload.get('sub')
            if username is None:
                raise credentials_exception

            # check the db and if it is not there raise an exception
            user = AuthService.get_user(username, db)
            if user is None:
                raise credentials_exception
            
            return user
        
        except JWTError:
            raise credentials_exception
        
        
auth_service = AuthService()
    

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    return AuthService.get_current_user(db, token)


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    
    if not current_user:
        raise HTTPException(
            code=400,
            detail="Inactive User"
        )
    
    return current_user
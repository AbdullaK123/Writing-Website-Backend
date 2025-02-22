from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from src.services.redis import redis_service
from src.settings import app_config
from src.routes import users, stories


app = FastAPI(
    title="App Backend API",
    description="The backend API for my AO3 clone",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[app_config.ALLOWED_DOMAIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(
    SessionMiddleware,
    secret_key=app_config.SECRET_KEY,
    session_cookie="session",
    max_age=app_config.SESSION_LIFETIME,
    same_site="lax",
    https_only=True,
    backend=redis_service
)

app.include_router(users.router)
app.include_router(stories.router)
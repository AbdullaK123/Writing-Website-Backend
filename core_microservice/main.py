from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.settings import app_config
from src.routes import users, stories, chapters


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

app.include_router(stories.router)
app.include_router(chapters.router)
app.include_router(users.router)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    DATABASE_URL: str 
    DATABASE_MIGRATION_URL: str
    SECRET_KEY:str
    REDIS_HOST: str
    REDIS_PORT: int
    APP_PORT: int
    ALLOWED_DOMAIN:str
    TOKEN_EXPIRE_TIME: str
    REFRESH_TOKEN_EXPIRE_TIME: str
    AUTH_ALGO: str

    class Config:
        env_file = '.env'


app_config = Settings()
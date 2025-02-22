from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    DATABASE_URL: str 
    DATABASE_MIGRATION_URL: str
    SECRET_KEY:str
    REDIS_HOST: str
    REDIS_PORT: int
    APP_PORT: int
    ALLOWED_DOMAIN:str
    SESSION_LIFETIME:int = 24*60*60

    class Config:
        env_file = '.env'


app_config = Settings()
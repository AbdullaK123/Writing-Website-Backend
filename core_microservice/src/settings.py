from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    DATABASE_URL: str 
    DATABASE_MIGRATION_URL: str

    class Config:
        env_file = '.env'


app_config = Settings()
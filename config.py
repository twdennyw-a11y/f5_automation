import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./f5_portal.db"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "b3921867dd11cc2ba5df489f6b986b2d139e8a7ea39151e309f4581c15f93539")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    
    # Optional Real F5 Env Configs
    F5_HOST: str = os.getenv("F5_HOST", "")
    F5_USER: str = os.getenv("F5_USER", "admin")
    F5_PASS: str = os.getenv("F5_PASS", "admin")

settings = Settings()

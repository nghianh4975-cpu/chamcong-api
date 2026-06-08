from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///chamcong.db"
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    APP_NAME: str = "Chấm Công Thông Minh"
    WORK_START_TIME: str = "08:00"
    WORK_END_TIME: str = "17:00"
    LATE_TOLERANCE_MINUTES: int = 5

    # IP Whitelist - cho phép truy cập. Để trống = cho phép tất cả.
    # Nhiều IP thì cách nhau bằng dấu phẩy. VD: "113.185.0.1,192.168.1.0/24"
    ALLOWED_IPS: str = ""

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # MySQL 配置
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_HOST: str
    MYSQL_PORT: str = "3306"
    MYSQL_DB: str

    # JWT 配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # 阿里云配置
    ALIYUN_BUCKET_NAME: str
    ALIYUN_ACCESSKEY_ID: str
    ALIYUN_ACCESSKEY_SECRET: str
    ALIYUN_ENDPOINT: str

    # 大模型配置
    LLM_API_KEY: str
    LLM_BASE_URL: str
    LLM_MODEL_NAME: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
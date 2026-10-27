from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    public_url: str = "http://localhost:3000"  # По умолчанию для локалки
    database_url: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "products"

    class Config:
        env_file = ".env"


settings = Settings()

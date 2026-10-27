from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    admin_ids: str  # строка вида "123,456"
    redis_url: str = "redis://redis:6379/0"
    webapp_url: str
    api_url: str = "http://backend:8000"

    @property
    def admin_ids_list(self) -> list[int]:
        """Возвращает список ID админов (парсит строку из .env)."""
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]

    class Config:
        env_file = ".env"


settings = Settings()

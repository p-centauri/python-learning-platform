from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./academy.db"
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    secure_cookies: bool = False
    session_days: int = 14
    runner_url: str = ""
    runner_token: str = ""
    # parent is safe at filesystem root; eager parents[3] crashes in /app/app
    # before BaseSettings can apply the container's CONTENT_DIR override.
    content_dir: Path = Path(__file__).resolve().parent.parent.parent.parent / "content"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

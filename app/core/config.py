from functools import lru_cache
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application configuration using Pydantic Settings.
    Values are loaded from environment variables and a .env file.
    """
    # App Settings
    app_name: str = "ParamedicAI"
    debug: bool = True

    # OpenAI Settings
    # Using SecretStr prevents the key from being accidentally printed in logs
    openai_api_key: SecretStr
    model_name: str = "gpt-4o"

    # Configuration for loading the environment data
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="BA_",
        extra="ignore"  # Safely ignore extra env vars that don't match our model
    )

@lru_cache
def get_settings() -> Settings:
    """
    Ensures the Settings instance is created only once (Singleton pattern).
    """
    return Settings()
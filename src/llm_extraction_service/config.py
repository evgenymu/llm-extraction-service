"""Runtime settings, read from environment variables or a local .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # No default: which model runs decides output quality, so it must be chosen
    # explicitly rather than inherited from code.
    llm_model: str
    ollama_host: str = "http://localhost:11434"
    # A cold start loads the weights into memory, which took ~25 s on the
    # development machine. The timeout must cover that first request.
    llm_timeout_seconds: float = 60.0

"""Load settings from environment."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-08-01-preview"
    azure_openai_chat_deployment: str = "gpt-4o-mini"

    # Azure Speech
    azure_speech_key: str = ""
    azure_speech_region: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    @property
    def is_azure_openai_configured(self) -> bool:
        return bool(self.azure_openai_endpoint and self.azure_openai_api_key)

    @property
    def is_azure_speech_configured(self) -> bool:
        return bool(self.azure_speech_key and self.azure_speech_region)


settings = Settings()

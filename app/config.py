from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Claude OAuth Gateway"
    host: str = "0.0.0.0"
    port: int = 8765

    gateway_api_key: str = "change-this-local-key"

    data_dir: str = "./data"

    default_model: str = "claude-sonnet"
    available_models: str = (
        "claude-sonnet,claude-opus,claude-haiku"
    )

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @property
    def models(self) -> list[str]:
        return [
            model.strip()
            for model in self.available_models.split(",")
            if model.strip()
        ]


settings = Settings()

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # Ollama / LiteLLM
    ollama_api_base: str = Field(
        default="http://127.0.0.1:11434",
        validation_alias="OLLAMA_API_BASE",
    )
    raip_target_model: str = Field(
        default="ollama/ministral-3:3b",
        validation_alias="RAIP_TARGET_MODEL",
    )
    raip_judge_model: str | None = Field(
        default=None,
        validation_alias="RAIP_JUDGE_MODEL",
        description="If unset, same as target model (dev only).",
    )

    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    celery_broker_url: str | None = Field(default=None, validation_alias="CELERY_BROKER_URL")
    celery_result_backend: str | None = Field(
        default=None,
        validation_alias="CELERY_RESULT_BACKEND",
    )

    mlflow_tracking_uri: str = Field(
        default="http://localhost:5000",
        validation_alias="MLFLOW_TRACKING_URI",
    )
    mlflow_experiment: str = Field(default="raip-mvp1", validation_alias="MLFLOW_EXPERIMENT")

    # MinIO (S3-compatible)
    minio_endpoint_url: str = Field(
        default="http://localhost:9000",
        validation_alias="MINIO_ENDPOINT_URL",
    )
    minio_access_key: str = Field(default="minioadmin", validation_alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", validation_alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="raip", validation_alias="MINIO_BUCKET")
    minio_region: str = Field(default="us-east-1", validation_alias="MINIO_REGION")

    api_host: str = Field(default="0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(default=8000, validation_alias="API_PORT")

    @property
    def effective_judge_model(self) -> str:
        return self.raip_judge_model or self.raip_target_model

    @property
    def celery_broker(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def celery_backend(self) -> str:
        return self.celery_result_backend or self.redis_url


@lru_cache
def get_settings() -> Settings:
    return Settings()

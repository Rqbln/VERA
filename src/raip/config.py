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
        default="ollama/llama3.1:8b-instruct-q8_0",
        validation_alias="RAIP_TARGET_MODEL",
    )
    raip_judge_model: str | None = Field(
        default=None,
        validation_alias="RAIP_JUDGE_MODEL",
        description="If unset, same as target model (dev only).",
    )

    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    redis_run_ttl_seconds: int = Field(
        default=604800,
        validation_alias="REDIS_RUN_TTL_SECONDS",
        description="TTL for run records in Redis (0 = no expiry). Default 7 days.",
    )

    celery_broker_url: str | None = Field(default=None, validation_alias="CELERY_BROKER_URL")
    celery_result_backend: str | None = Field(
        default=None,
        validation_alias="CELERY_RESULT_BACKEND",
    )

    mlflow_tracking_uri: str = Field(
        default="http://localhost:5000",
        validation_alias="MLFLOW_TRACKING_URI",
    )
    mlflow_experiment: str = Field(default="raip-mvp2", validation_alias="MLFLOW_EXPERIMENT")
    raip_mlflow_disabled: bool = Field(
        default=False,
        validation_alias="RAIP_MLFLOW_DISABLED",
        description="When true (lite mode), skip all MLflow logging instead of failing.",
    )

    # Artifact storage backend: auto -> MinIO if reachable else local filesystem.
    raip_artifact_backend: str = Field(
        default="auto",
        validation_alias="RAIP_ARTIFACT_BACKEND",
        description="auto | minio | local",
    )
    raip_local_artifacts_dir: str = Field(
        default="./.raip-artifacts",
        validation_alias="RAIP_LOCAL_ARTIFACTS_DIR",
    )
    raip_public_api_url: str = Field(
        default="",
        validation_alias="RAIP_PUBLIC_API_URL",
        description="Browser-reachable API base used to build local artifact URLs (lite mode).",
    )

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

    raip_postgres_url: str = Field(
        default="postgresql://raip:raip@localhost:5433/raip",
        validation_alias="RAIP_POSTGRES_URL",
    )
    raip_timescale_url: str = Field(
        default="postgresql://raip:raip@localhost:5434/raip_ts",
        validation_alias="RAIP_TIMESCALE_URL",
    )
    raip_signing_key_id: str = Field(
        default="openbao-transit-dev",
        validation_alias="RAIP_SIGNING_KEY_ID",
    )

    @property
    def effective_judge_model(self) -> str:
        return self.raip_judge_model or self.raip_target_model

    @property
    def mlflow_enabled(self) -> bool:
        """MLflow is used only when not explicitly disabled and a tracking URI is set."""
        if self.raip_mlflow_disabled:
            return False
        return bool((self.mlflow_tracking_uri or "").strip())

    @property
    def celery_broker(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def celery_backend(self) -> str:
        return self.celery_result_backend or self.redis_url


@lru_cache
def get_settings() -> Settings:
    return Settings()

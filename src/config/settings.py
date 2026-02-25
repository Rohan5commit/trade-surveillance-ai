from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = Field(default="development", alias="ENVIRONMENT")
    demo_mode: bool = Field(default=False, alias="DEMO_MODE")
    require_api_key: bool = Field(default=True, alias="REQUIRE_API_KEY")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    postgres_url: str = Field(default="", alias="POSTGRES_URL")
    redis_url: str = Field(default="", alias="REDIS_URL")
    neo4j_uri: str = Field(default="", alias="NEO4J_URI")
    neo4j_user: str = Field(default="", alias="NEO4J_USER")
    neo4j_password: str = Field(default="", alias="NEO4J_PASSWORD")
    kafka_bootstrap_servers: str = Field(default="", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_security_protocol: str = Field(default="", alias="KAFKA_SECURITY_PROTOCOL")
    kafka_ssl_keyfile: str = Field(default="", alias="KAFKA_SSL_KEYFILE")
    kafka_ssl_certfile: str = Field(default="", alias="KAFKA_SSL_CERTFILE")
    kafka_ssl_cafile: str = Field(default="", alias="KAFKA_SSL_CAFILE")
    mlflow_tracking_uri: str = Field(default="", alias="MLFLOW_TRACKING_URI")
    drift_psi_threshold: float = Field(default=0.25, alias="DRIFT_PSI_THRESHOLD")
    retrain_dataset_path: str = Field(default="", alias="RETRAIN_DATASET_PATH")

    jwt_secret: str = Field(default="dev-insecure-secret", alias="JWT_SECRET")
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")


settings = Settings()

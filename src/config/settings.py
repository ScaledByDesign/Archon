"""
Configuration settings for the FastAPI backend services.
Handles environment variables and validation using Pydantic.
"""

import os
from typing import List, Optional, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator, validator
from enum import Enum
from functools import lru_cache


class Environment(str, Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    
    # MongoDB Settings
    mongodb_host: str = Field(default="localhost", env="MONGODB_HOST")
    mongodb_port: int = Field(default=27017, env="MONGODB_PORT")
    mongodb_username: Optional[str] = Field(default=None, env="MONGODB_USERNAME")
    mongodb_password: Optional[str] = Field(default=None, env="MONGODB_PASSWORD")
    mongodb_database: str = Field(default="rag_system", env="MONGODB_DATABASE")
    mongodb_auth_source: str = Field(default="admin", env="MONGODB_AUTH_SOURCE")
    
    # Redis Settings
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_ssl: bool = Field(default=False, env="REDIS_SSL")
    
    # PostgreSQL Settings (for Authentik)
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_username: str = Field(default="postgres", env="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", env="POSTGRES_PASSWORD")
    postgres_database: str = Field(default="authentik", env="POSTGRES_DB")
    
    @property
    def mongodb_url(self) -> str:
        """Construct MongoDB connection URL"""
        if self.mongodb_username and self.mongodb_password:
            return (
                f"mongodb://{self.mongodb_username}:{self.mongodb_password}@"
                f"{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_database}"
                f"?authSource={self.mongodb_auth_source}"
            )
        return f"mongodb://{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_database}"
    
    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL"""
        scheme = "rediss" if self.redis_ssl else "redis"
        if self.redis_password:
            return f"{scheme}://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"{scheme}://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def postgres_url(self) -> str:
        """Construct PostgreSQL connection URL"""
        return (
            f"postgresql://{self.postgres_username}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
        )


class VaultSettings(BaseSettings):
    """HashiCorp Vault configuration"""
    
    vault_addr: str = Field(default="http://localhost:8200", env="VAULT_ADDR")
    vault_token: Optional[str] = Field(default=None, env="VAULT_TOKEN")
    vault_role_id: Optional[str] = Field(default=None, env="VAULT_ROLE_ID")
    vault_secret_id: Optional[str] = Field(default=None, env="VAULT_SECRET_ID")
    vault_verify_ssl: bool = Field(default=True, env="VAULT_VERIFY_SSL")
    vault_namespace: Optional[str] = Field(default=None, env="VAULT_NAMESPACE")
    
    # Secret paths
    vault_secret_path: str = Field(default="secret/data/rag-system", env="VAULT_SECRET_PATH")
    vault_database_path: str = Field(default="database/creds", env="VAULT_DATABASE_PATH")


class QdrantSettings(BaseSettings):
    """Qdrant vector database configuration"""
    
    qdrant_host: str = Field(default="localhost", env="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, env="QDRANT_PORT")
    qdrant_grpc_port: int = Field(default=6334, env="QDRANT_GRPC_PORT")
    qdrant_api_key: Optional[str] = Field(default=None, env="QDRANT_API_KEY")
    qdrant_https: bool = Field(default=False, env="QDRANT_HTTPS")
    qdrant_timeout: int = Field(default=30, env="QDRANT_TIMEOUT")
    
    # Collection settings
    qdrant_collection_prefix: str = Field(default="rag_", env="QDRANT_COLLECTION_PREFIX")
    qdrant_vector_size: int = Field(default=1536, env="QDRANT_VECTOR_SIZE")  # OpenAI embeddings
    qdrant_distance_metric: str = Field(default="Cosine", env="QDRANT_DISTANCE_METRIC")
    
    @property
    def qdrant_url(self) -> str:
        """Construct Qdrant connection URL"""
        scheme = "https" if self.qdrant_https else "http"
        return f"{scheme}://{self.qdrant_host}:{self.qdrant_port}"


class AuthSettings(BaseSettings):
    """Authentication and security configuration"""
    
    # OAuth2 Settings
    oauth_client_id: Optional[str] = Field(default=None, env="FASTAPI_OAUTH_CLIENT_ID")
    oauth_client_secret: Optional[str] = Field(default=None, env="FASTAPI_OAUTH_CLIENT_SECRET")
    oauth_redirect_uri: Optional[str] = Field(default="http://localhost:8000/api/auth/callback", env="FASTAPI_OAUTH_REDIRECT_URI")
    oauth_scope: str = Field(default="openid email profile rag:api", env="OAUTH_SCOPE")
    oauth_provider_url: str = Field(default="https://authentik-server:9443", env="OAUTH_PROVIDER_URL")
    
    # JWT Settings
    jwt_secret_key: Optional[str] = Field(default=None, env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="RS256", env="JWT_ALGORITHM")
    jwt_expiration_time: int = Field(default=3600, env="JWT_EXPIRATION_TIME")  # 1 hour
    jwt_refresh_expiration_time: int = Field(default=86400, env="JWT_REFRESH_EXPIRATION_TIME")  # 24 hours
    jwt_issuer: str = Field(default="rag-system", env="JWT_ISSUER")
    jwt_audience: str = Field(default="rag-system-api", env="JWT_AUDIENCE")
    
    # Session Settings
    session_secret_key: Optional[str] = Field(default=None, env="SESSION_SECRET_KEY")
    session_cookie_name: str = Field(default="session", env="SESSION_COOKIE_NAME")
    session_max_age: int = Field(default=3600, env="SESSION_MAX_AGE")  # 1 hour
    
    # Security Settings
    bcrypt_rounds: int = Field(default=12, env="BCRYPT_ROUNDS")
    password_min_length: int = Field(default=8, env="PASSWORD_MIN_LENGTH")
    
    # CORS Settings
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:8080,http://localhost:8000", env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: str = Field(default="GET,POST,PUT,DELETE,OPTIONS", env="CORS_ALLOW_METHODS")
    cors_allow_headers: str = Field(default="*", env="CORS_ALLOW_HEADERS")
    
    # Trusted Hosts
    trusted_hosts: str = Field(default="localhost,127.0.0.1,*.localhost", env="TRUSTED_HOSTS")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    @property
    def cors_allow_methods_list(self) -> List[str]:
        """Convert comma-separated CORS methods to list"""
        return [method.strip() for method in self.cors_allow_methods.split(",") if method.strip()]
    
    @property
    def trusted_hosts_list(self) -> List[str]:
        """Convert comma-separated trusted hosts to list"""
        return [host.strip() for host in self.trusted_hosts.split(",") if host.strip()]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


class LLMSettings(BaseSettings):
    """Large Language Model configuration"""
    
    # OpenAI Settings
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_organization: Optional[str] = Field(default=None, env="OPENAI_ORGANIZATION")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-ada-002", env="OPENAI_EMBEDDING_MODEL")
    
    # Anthropic Settings
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-sonnet-20240229", env="ANTHROPIC_MODEL")
    
    # LiteLLM Settings
    litellm_base_url: Optional[str] = Field(default=None, env="LITELLM_BASE_URL")
    litellm_api_key: Optional[str] = Field(default=None, env="LITELLM_API_KEY")
    
    # Model Parameters
    max_tokens: int = Field(default=1000, env="LLM_MAX_TOKENS")
    temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    top_p: float = Field(default=1.0, env="LLM_TOP_P")


class RabbitMQSettings(BaseSettings):
    """RabbitMQ message queue configuration"""
    
    rabbitmq_host: str = Field(default="localhost", env="RABBITMQ_HOST")
    rabbitmq_port: int = Field(default=5672, env="RABBITMQ_PORT")
    rabbitmq_username: str = Field(default="guest", env="RABBITMQ_USERNAME")
    rabbitmq_password: str = Field(default="guest", env="RABBITMQ_PASSWORD")
    rabbitmq_vhost: str = Field(default="/", env="RABBITMQ_VHOST")
    rabbitmq_ssl: bool = Field(default=False, env="RABBITMQ_SSL")
    
    # Queue Settings
    rabbitmq_exchange: str = Field(default="rag_system", env="RABBITMQ_EXCHANGE")
    rabbitmq_routing_key: str = Field(default="document.process", env="RABBITMQ_ROUTING_KEY")
    rabbitmq_queue_durable: bool = Field(default=True, env="RABBITMQ_QUEUE_DURABLE")
    
    @property
    def rabbitmq_url(self) -> str:
        """Construct RabbitMQ connection URL"""
        scheme = "amqps" if self.rabbitmq_ssl else "amqp"
        return (
            f"{scheme}://{self.rabbitmq_username}:{self.rabbitmq_password}@"
            f"{self.rabbitmq_host}:{self.rabbitmq_port}{self.rabbitmq_vhost}"
        )


class AppSettings(BaseSettings):
    """Main application settings"""
    
    # Application Info
    app_name: str = Field(default="Production RAG System", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    app_description: str = Field(
        default="Secure, scalable RAG system with vector search and LLM integration",
        env="APP_DESCRIPTION"
    )
    
    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server Settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    reload: bool = Field(default=False, env="RELOAD")
    
    # API Settings
    api_prefix: str = Field(default="/api", env="API_PREFIX")
    docs_url: Optional[str] = Field(default="/docs", env="DOCS_URL")
    redoc_url: Optional[str] = Field(default="/redoc", env="REDOC_URL")
    openapi_url: Optional[str] = Field(default="/openapi.json", env="OPENAPI_URL")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Performance
    max_request_size: int = Field(default=16 * 1024 * 1024, env="MAX_REQUEST_SIZE")  # 16MB
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    
    # Feature Flags
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_tracing: bool = Field(default=False, env="ENABLE_TRACING")
    enable_health_checks: bool = Field(default=True, env="ENABLE_HEALTH_CHECKS")
    
    # Component Settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    vault: VaultSettings = Field(default_factory=VaultSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    rabbitmq: RabbitMQSettings = Field(default_factory=RabbitMQSettings)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @validator("environment", pre=True)
    @classmethod
    def parse_environment(cls, v):
        if isinstance(v, str):
            return Environment(v.lower())
        return v
    
    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_testing(self) -> bool:
        return self.environment == Environment.TESTING


@lru_cache()
def get_settings() -> AppSettings:
    """Get cached application settings"""
    return AppSettings()


# Global settings instance
settings = get_settings()

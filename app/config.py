"""
Cấu hình ứng dụng — load từ biến môi trường (.env).
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- SQL Server ---
    SQL_SERVER_HOST: str = "localhost"
    SQL_SERVER_PORT: int = 1433
    SQL_SERVER_DB: str = "usedCars"
    SQL_SERVER_USER: str = "sa"
    SQL_SERVER_PASSWORD: str = "123456"
    SQL_READONLY_USER: str = "rag_chatbot_readonly"
    SQL_READONLY_PASSWORD: str = "123456"

    # --- Qdrant ---
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "xe_inventory"

    # --- LLM ---
    LLM_MODEL: str = ""           # Model name cho LLM chính
    LLM_BASE_URL: str = ""        # Endpoint OpenAI-compatible gateway
    API_KEY: str = ""             # API key cho LLM_BASE_URL

    # --- Vehicle Pricing Vision ---
    VISION_API_KEY: str = ""      # API key Beeknoee cho phan tich anh dinh gia xe
    VISION_BASE_URL: str = "https://platform.beeknoee.com/api/v1"
    VISION_MODEL: str = ""        # Vision model tren Beeknoee

    # --- Internal Pricing ---
    PRICING_INTERNAL_TOKEN: str = ""
    PRICING_MONGO_URI: str = ""
    PRICING_MONGO_DB: str = "pricing"
    PRICING_MONGO_COLLECTION: str = "ai_vehicle_valuations"
    PRICING_CLOUDINARY_ALLOWED_DOMAINS: str = "res.cloudinary.com"
    PRICING_MAX_IMAGES: int = 20
    PRICING_SCHEMA_VERSION: str = "vehicle-pricing-v2"
    PRICING_IMAGE_HASH_TIMEOUT_SECONDS: int = 2

    # --- Cloudinary ---
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # --- Embedding ---
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_BASE_URL: str = ""
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BATCH_SIZE: int = 32

    # --- Redis ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_SESSION_TTL: int = 86400
    REDIS_RECONCILE_INTERVAL: int = 60
    REDIS_RETRY_INTERVAL: int = 5
    REDIS_RETRY_MAX_ATTEMPTS: int = 10

    # --- App ---
    ADMIN_API_KEY: str = "your_secret_key"
    MAX_HISTORY_TURNS: int = 6
    SQL_QUERY_TIMEOUT: int = 10
    SYNC_INTERVAL_MINUTES: int = 15
    QDRANT_SCORE_THRESHOLD: float = 0.4

    @property
    def sqlserver_connection_string(self) -> str:
        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.SQL_SERVER_HOST},{self.SQL_SERVER_PORT};"
            f"DATABASE={self.SQL_SERVER_DB};"
            f"UID={self.SQL_SERVER_USER};"
            f"PWD={self.SQL_SERVER_PASSWORD};"
            f"TrustServerCertificate=yes;"
        )

    @property
    def sqlserver_readonly_connection_string(self) -> str:
        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.SQL_SERVER_HOST},{self.SQL_SERVER_PORT};"
            f"DATABASE={self.SQL_SERVER_DB};"
            f"UID={self.SQL_READONLY_USER};"
            f"PWD={self.SQL_READONLY_PASSWORD};"
            f"TrustServerCertificate=yes;"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def pricing_cloudinary_domains(self) -> set[str]:
        raw = self.PRICING_CLOUDINARY_ALLOWED_DOMAINS.strip()
        if not raw:
            return set()
        return {item.strip().lower() for item in raw.split(",") if item.strip()}


@lru_cache()
def get_settings() -> Settings:
    return Settings()

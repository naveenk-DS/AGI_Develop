from pydantic_settings import BaseSettings
from pydantic import Field
from loguru import logger
import sys

class Settings(BaseSettings):
    # App Settings
    app_name: str = "NAVIX AI Operating System"
    environment: str = Field("development", pattern="^(development|production|testing)$")
    debug: bool = True
    
    # LLM Settings
    ollama_url: str = "http://127.0.0.1:11434"
    navix_model: str = "qwen2.5:7b"
    vision_model: str = "llava:7b"
    
    # Vector DB
    qdrant_host: str = "127.0.0.1"
    qdrant_port: int = 6333
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

try:
    config = Settings()
except Exception as e:
    logger.error(f"Configuration Validation Failed: {e}")
    sys.exit(1)

def setup_logging():
    """Configure centralized structured logging for the entire app."""
    logger.remove()  # Remove default handler
    
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    logger.add(sys.stdout, format=log_format, level="DEBUG" if config.debug else "INFO")
    logger.add("logs/navix_core.log", rotation="50 MB", retention="10 days", compression="zip", format=log_format, level="INFO")
    logger.info("Structured logging initialized")


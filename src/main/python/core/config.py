"""
Configuration settings for Dual Asset Bot
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "DualAssetBot"
    app_env: str = "development"
    debug: bool = True
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/dual_asset_bot"
    redis_url: str = "redis://localhost:6379/0"
    
    # Binance API
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None
    binance_testnet: bool = True
    
    # Trading Configuration
    default_investment_amount: float = 100.0  # USDT
    max_single_investment_ratio: float = 0.2  # 20% of total capital
    min_apr_threshold: float = 0.15  # 15% minimum annual percentage rate
    risk_level: int = 5  # 1-10, where 10 is most aggressive
    
    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create global settings instance
settings = Settings()
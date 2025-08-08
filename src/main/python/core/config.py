"""
Configuration settings for Dual Asset Bot
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

# Find project root directory (where .env file is located)
current_dir = Path(__file__).resolve().parent
# core -> python -> main -> src -> project_root
project_root = current_dir.parent.parent.parent.parent  # Go up to project root

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "DualAssetBot"
    app_env: str = "development"
    debug: bool = True
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/dual_asset_bot.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Binance API
    # Separate keys for testnet and production
    binance_testnet_api_key: Optional[str] = None
    binance_testnet_api_secret: Optional[str] = None
    binance_production_api_key: Optional[str] = None
    binance_production_api_secret: Optional[str] = None
    
    # Environment selection
    binance_use_testnet: bool = False  # True for testnet, False for production
    
    # Legacy support (will be deprecated)
    binance_api_key: Optional[str] = None  # Fallback for old config
    binance_api_secret: Optional[str] = None  # Fallback for old config
    binance_testnet: bool = False  # Legacy field
    
    # Production Safety Settings
    demo_mode: bool = True  # Simulate trades by default
    max_trade_amount: float = 10.0  # Maximum trade amount in USDT
    trading_enabled: bool = False  # Master switch for trading
    use_public_data_only: bool = False  # Use only public API endpoints
    
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
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Task Configuration
    enable_automated_trading: bool = False  # Safety switch
    max_concurrent_trades: int = 5
    trading_cooldown_minutes: int = 15
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = str(project_root / ".env")
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file

# Create global settings instance
settings = Settings()
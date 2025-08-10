"""
Main FastAPI application for Dual Asset Bot
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
from loguru import logger

# Import routers
from api.routers import market, dual_investment, account, trading, tasks

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Dual Asset Bot API",
    description="API for Binance Dual Investment Auto Trading Bot",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3010", "http://localhost:8081"],  # React dev server + API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(market.router)
app.include_router(dual_investment.router)
app.include_router(account.router)
app.include_router(trading.router)
app.include_router(tasks.router)

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    from services.binance_service import binance_service
    try:
        binance_service._initialize_client()
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize services: {e}")

# Health check response model
class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Dual Asset Bot API"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": os.getenv("APP_ENV", "development")
    }

@app.get("/api/v1/status")
async def get_status():
    """Get bot status"""
    from services.binance_service import binance_service
    
    connected = binance_service.test_connection()
    
    return {
        "bot_running": connected,
        "binance_connected": connected,
        "strategies_active": 0,
        "last_check": None,
        "message": "Bot is running" if connected else "Bot not connected to Binance"
    }

if __name__ == "__main__":
    import uvicorn
    from core.config import settings
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
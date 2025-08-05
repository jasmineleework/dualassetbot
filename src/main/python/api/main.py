"""
Main FastAPI application for Dual Asset Bot
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

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
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {
        "bot_running": False,
        "strategies_active": 0,
        "last_check": None,
        "message": "Bot not yet implemented"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
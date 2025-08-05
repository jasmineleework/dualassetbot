"""
Account management API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from services.binance_service import binance_service
from loguru import logger

router = APIRouter(prefix="/api/v1/account", tags=["account"])

@router.get("/balance")
async def get_account_balance():
    """Get account balance for all assets"""
    try:
        balances = binance_service.get_account_balance()
        
        # Calculate total value in USDT
        total_usdt = 0
        for asset, balance in balances.items():
            if asset == 'USDT':
                total_usdt += balance['total']
            else:
                # Try to get price in USDT
                try:
                    price = binance_service.get_symbol_price(f"{asset}USDT")
                    total_usdt += balance['total'] * price
                except:
                    # Skip if can't get price
                    pass
        
        return {
            "balances": balances,
            "total_value_usdt": total_usdt
        }
    except Exception as e:
        logger.error(f"Failed to get account balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/assets")
async def get_available_assets():
    """Get list of assets available for dual investment"""
    # For now, return common assets
    return {
        "assets": ["BTC", "ETH", "BNB", "SOL", "MATIC"],
        "base_currency": "USDT"
    }
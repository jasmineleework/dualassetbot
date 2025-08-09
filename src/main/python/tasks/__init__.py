"""
Celery tasks package for DualAssetBot
"""
from .update_products import (
    update_dual_investment_products,
    warmup_cache,
    invalidate_product_cache
)

__all__ = [
    'update_dual_investment_products',
    'warmup_cache',
    'invalidate_product_cache'
]
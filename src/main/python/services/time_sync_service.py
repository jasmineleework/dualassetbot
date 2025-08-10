"""
Time synchronization service for Binance API
Handles timestamp synchronization to avoid API errors
"""
import time
import requests
from typing import Optional
from loguru import logger
from datetime import datetime

class TimeSyncService:
    """Service for synchronizing with Binance server time"""
    
    def __init__(self):
        self.time_offset = 0  # Offset in milliseconds
        self.last_sync = 0
        self.sync_interval = 3600  # Sync every hour
        
    def get_server_time(self) -> Optional[int]:
        """
        Get current server time from Binance
        
        Returns:
            Server timestamp in milliseconds
        """
        try:
            response = requests.get('https://api.binance.com/api/v3/time', timeout=5)
            if response.status_code == 200:
                return response.json()['serverTime']
        except Exception as e:
            logger.error(f"Failed to get Binance server time: {e}")
        return None
    
    def sync_time(self) -> bool:
        """
        Synchronize local time with Binance server
        
        Returns:
            True if sync successful
        """
        try:
            # Get server time
            server_time = self.get_server_time()
            if not server_time:
                logger.warning("Could not get server time, using local time")
                return False
            
            # Calculate offset
            local_time = int(time.time() * 1000)
            self.time_offset = server_time - local_time
            self.last_sync = time.time()
            
            # Log the offset
            offset_seconds = self.time_offset / 1000
            if abs(offset_seconds) > 1:
                logger.warning(f"Time offset detected: {offset_seconds:.2f} seconds")
                logger.info(f"Local time: {datetime.fromtimestamp(local_time/1000)}")
                logger.info(f"Server time: {datetime.fromtimestamp(server_time/1000)}")
            else:
                logger.debug(f"Time synchronized, offset: {self.time_offset}ms")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync time: {e}")
            return False
    
    def get_timestamp(self) -> int:
        """
        Get synchronized timestamp for API requests
        
        Returns:
            Synchronized timestamp in milliseconds
        """
        # Check if we need to resync
        if time.time() - self.last_sync > self.sync_interval:
            logger.info("Time sync interval exceeded, resyncing...")
            self.sync_time()
        
        # Return adjusted timestamp
        local_time = int(time.time() * 1000)
        synchronized_time = local_time + self.time_offset
        
        # Add a small buffer to account for network latency
        # Subtract 1000ms to ensure we're not ahead of server time
        synchronized_time -= 1000
        
        return synchronized_time
    
    def ensure_synced(self) -> bool:
        """
        Ensure time is synchronized
        
        Returns:
            True if synchronized
        """
        if self.last_sync == 0:
            logger.info("Initial time synchronization...")
            return self.sync_time()
        return True

# Create singleton instance
time_sync_service = TimeSyncService()
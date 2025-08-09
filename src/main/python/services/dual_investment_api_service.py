"""
Binance Dual Investment API Service
Handles real API calls to Binance Dual Investment endpoints
"""
import time
import hmac
import hashlib
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
from datetime import datetime
from loguru import logger
from binance.exceptions import BinanceAPIException


class DualInvestmentAPIService:
    """Service for interacting with Binance Dual Investment API"""
    
    def __init__(self, client):
        """
        Initialize the Dual Investment API service
        
        Args:
            client: Binance API client instance
        """
        self.client = client
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
    def get_product_list(
        self, 
        option_type: str, 
        exercised_coin: str, 
        invest_coin: str,
        page_size: int = 100,
        page_index: int = 1,
        retry_count: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get dual investment product list from Binance API
        
        Args:
            option_type: 'CALL' or 'PUT'
            exercised_coin: The coin to be exercised (e.g., 'BTC', 'USDT')
            invest_coin: The coin to invest (e.g., 'USDT', 'BTC')
            page_size: Number of products per page (max 100)
            page_index: Page number (starts from 1)
            retry_count: Current retry attempt number
            
        Returns:
            List of product dictionaries
        """
        try:
            # Log the request details
            logger.debug(f"Fetching dual products: {option_type} {exercised_coin}/{invest_coin} (page {page_index})")
            
            # Prepare parameters
            params = {
                'optionType': option_type,
                'exercisedCoin': exercised_coin,
                'investCoin': invest_coin,
                'pageSize': page_size,
                'pageIndex': page_index,
                'timestamp': int(time.time() * 1000),
                'recvWindow': 5000
            }
            
            # Make the API call
            response = self._make_signed_request('GET', '/sapi/v1/dci/product/list', params)
            
            if response and 'list' in response:
                product_count = len(response['list'])
                total_count = response.get('total', product_count)
                
                logger.info(
                    f"Successfully fetched {product_count}/{total_count} products "
                    f"for {option_type} {exercised_coin}/{invest_coin}"
                )
                
                # Log sample product for debugging
                if product_count > 0:
                    sample = response['list'][0]
                    logger.debug(f"Sample product: ID={sample.get('id')}, APR={sample.get('apr')}, "
                               f"Strike={sample.get('strikePrice')}")
                
                return response['list']
            else:
                logger.warning(f"Empty response for {option_type} {exercised_coin}/{invest_coin}")
                return []
                
        except BinanceAPIException as e:
            logger.error(f"Binance API error (attempt {retry_count + 1}/{self.max_retries}): "
                        f"Code={e.code}, Message={e.message}")
            
            # Handle specific error codes
            if e.code == -2015:  # Invalid API key/secret
                logger.error("Invalid API credentials - please check your API key and secret")
                return []
            elif e.code == -1121:  # Invalid symbol
                logger.error(f"Invalid symbol combination: {exercised_coin}/{invest_coin}")
                return []
            
            # Retry for other errors
            if retry_count < self.max_retries - 1:
                delay = self.retry_delay * (retry_count + 1)
                logger.info(f"Retrying after {delay} seconds...")
                time.sleep(delay)
                return self.get_product_list(
                    option_type, exercised_coin, invest_coin, 
                    page_size, page_index, retry_count + 1
                )
            
            logger.error(f"Failed after {self.max_retries} attempts")
            return []
            
        except Exception as e:
            logger.error(f"Unexpected error fetching dual products (attempt {retry_count + 1}/{self.max_retries}): {e}")
            
            # Retry logic
            if retry_count < self.max_retries - 1:
                delay = self.retry_delay * (retry_count + 1)
                logger.info(f"Retrying after {delay} seconds...")
                time.sleep(delay)
                return self.get_product_list(
                    option_type, exercised_coin, invest_coin,
                    page_size, page_index, retry_count + 1
                )
            
            # Final failure
            logger.error(f"Failed to fetch dual products after {self.max_retries} attempts: {e}")
            return []
    
    def _make_signed_request(self, method: str, path: str, params: dict) -> dict:
        """
        Make a signed request to Binance API using direct requests
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            params: Request parameters
            
        Returns:
            API response as dictionary
        """
        start_time = time.time()
        
        try:
            # Check if client has necessary attributes
            if not hasattr(self.client, 'API_KEY') or not hasattr(self.client, 'API_SECRET'):
                logger.error("API credentials not configured in client")
                raise ValueError("API credentials not configured")
            
            # Create signature
            query_string = urlencode(params)
            signature = hmac.new(
                self.client.API_SECRET.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            params['signature'] = signature
            
            # Log request (without sensitive data)
            logger.debug(f"API Request: {method} {path}")
            logger.debug(f"Parameters: optionType={params.get('optionType')}, "
                        f"exercisedCoin={params.get('exercisedCoin')}, "
                        f"investCoin={params.get('investCoin')}")
            
            # Build full URL and headers
            base_url = "https://api.binance.com"
            url = f"{base_url}{path}"
            headers = {'X-MBX-APIKEY': self.client.API_KEY}
            
            # Make the request using requests library directly
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers)
            else:
                response = requests.request(method, url, params=params, headers=headers)
            
            # Log response time
            elapsed = time.time() - start_time
            
            # Check response status
            if response.status_code == 200:
                logger.info(f"API Response: {path} took {elapsed:.2f}s")
                return response.json()
            else:
                logger.error(f"API Failed: {path} after {elapsed:.2f}s")
                logger.error(f"Status: {response.status_code}, Response: {response.text[:500]}")
                
                # Try to parse error response
                try:
                    error_data = response.json()
                    raise BinanceAPIException(response, response.status_code, error_data.get('msg', response.text))
                except (ValueError, KeyError):
                    raise BinanceAPIException(response, response.status_code, response.text)
            
        except BinanceAPIException:
            raise
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"API Failed: {path} after {elapsed:.2f}s - {e}")
            
            # Log detailed error information for debugging
            if hasattr(e, '__dict__'):
                logger.debug(f"Error details: {e.__dict__}")
                
            raise
    
    def get_all_products_for_pairs(
        self, 
        asset_pairs: List[tuple] = [('BTC', 'USDT'), ('ETH', 'USDT'), ('BNB', 'USDT')]
    ) -> List[Dict[str, Any]]:
        """
        Get all dual investment products for specified asset pairs
        
        Args:
            asset_pairs: List of (asset, quote) tuples
            
        Returns:
            Combined list of all products
        """
        all_products = []
        
        for asset, quote in asset_pairs:
            try:
                # BUY_LOW products (PUT options) - invest quote to potentially buy asset
                logger.info(f"Fetching BUY_LOW products for {asset}/{quote}")
                put_products = self.get_product_list('PUT', asset, quote)
                all_products.extend(put_products)
                
                # SELL_HIGH products (CALL options) - invest asset to potentially sell for quote
                logger.info(f"Fetching SELL_HIGH products for {asset}/{quote}")
                call_products = self.get_product_list('CALL', quote, asset)
                all_products.extend(call_products)
                
            except Exception as e:
                logger.error(f"Failed to get products for {asset}/{quote}: {e}")
                continue
        
        logger.info(f"Total products fetched: {len(all_products)}")
        return all_products
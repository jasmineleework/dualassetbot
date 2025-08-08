"""
Screenshot service for capturing Binance Futures charts
Uses Selenium WebDriver for browser automation
"""
import base64
import io
import time
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from PIL import Image
from loguru import logger
import os
import tempfile

class ScreenshotService:
    """Service for capturing trading charts from Binance Futures testnet"""
    
    # Binance Futures testnet URLs for different pairs
    FUTURES_URLS = {
        'BTCUSDT': 'https://testnet.binancefuture.com/en/futures/BTCUSDT',
        'ETHUSDT': 'https://testnet.binancefuture.com/en/futures/ETHUSDT',
        'BTCUSDC': 'https://testnet.binancefuture.com/en/futures/BTCUSDC_PERPETUAL',
        'ETHUSDC': 'https://testnet.binancefuture.com/en/futures/ETHUSDC_PERPETUAL'
    }
    
    def __init__(self):
        """Initialize the screenshot service"""
        self.driver = None
        self.headless = True  # Set to False for debugging
        
    def _init_driver(self):
        """Initialize Chrome WebDriver with optimal settings"""
        if self.driver:
            return
            
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_window_size(1920, 1080)
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            # Try with default options if custom options fail
            try:
                self.driver = webdriver.Chrome()
                logger.info("Chrome WebDriver initialized with default options")
            except Exception as e2:
                logger.error(f"Failed to initialize Chrome WebDriver with default options: {e2}")
                raise
    
    def capture_binance_chart(self, symbol: str = 'BTCUSDT') -> Optional[str]:
        """
        Capture Binance Futures chart for a given symbol
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            Base64 encoded screenshot or None if failed
        """
        if symbol not in self.FUTURES_URLS:
            logger.warning(f"Symbol {symbol} not supported, using BTCUSDT")
            symbol = 'BTCUSDT'
            
        url = self.FUTURES_URLS[symbol]
        
        try:
            # Initialize driver if needed
            self._init_driver()
            
            logger.info(f"Navigating to {url}")
            self.driver.get(url)
            
            # Wait for the chart to load
            wait = WebDriverWait(self.driver, 20)
            
            # Try multiple selectors for the chart container
            chart_selectors = [
                "div[class*='chart']",
                "div[id*='chart']",
                "iframe[id*='tradingview']",
                "div.chart-container",
                "canvas"
            ]
            
            chart_element = None
            for selector in chart_selectors:
                try:
                    chart_element = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if chart_element:
                        logger.info(f"Found chart element with selector: {selector}")
                        break
                except:
                    continue
            
            # Additional wait for chart data to load
            time.sleep(5)
            
            # Take screenshot
            screenshot = self.driver.get_screenshot_as_png()
            
            # Convert to base64
            img = Image.open(io.BytesIO(screenshot))
            
            # Optionally crop to chart area (if we found the element)
            if chart_element:
                try:
                    location = chart_element.location
                    size = chart_element.size
                    
                    # Crop the image to the chart area
                    left = location['x']
                    top = location['y']
                    right = left + size['width']
                    bottom = top + size['height']
                    
                    # Ensure coordinates are within image bounds
                    img_width, img_height = img.size
                    left = max(0, left)
                    top = max(0, top)
                    right = min(img_width, right)
                    bottom = min(img_height, bottom)
                    
                    if right > left and bottom > top:
                        img = img.crop((left, top, right, bottom))
                        logger.info(f"Cropped chart area: {right-left}x{bottom-top}")
                except Exception as e:
                    logger.warning(f"Could not crop to chart area: {e}")
            
            # Convert to base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            logger.info(f"Successfully captured chart for {symbol}")
            return img_base64
            
        except Exception as e:
            logger.error(f"Failed to capture chart: {e}")
            return None
    
    def capture_with_fallback(self, symbol: str = 'BTCUSDT') -> Dict[str, Any]:
        """
        Capture chart with fallback to static generation if browser fails
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Dictionary with chart data and metadata
        """
        result = {
            'success': False,
            'symbol': symbol,
            'source': None,
            'image_base64': None,
            'error': None
        }
        
        # Try browser screenshot first
        try:
            image_base64 = self.capture_binance_chart(symbol)
            if image_base64:
                result['success'] = True
                result['source'] = 'binance_futures'
                result['image_base64'] = image_base64
                return result
        except Exception as e:
            logger.warning(f"Browser screenshot failed: {e}")
            result['error'] = str(e)
        
        # Fallback to static chart generation
        try:
            from .chart_generator import ChartGenerator
            generator = ChartGenerator()
            image_base64 = generator.generate_candlestick_chart(symbol)
            if image_base64:
                result['success'] = True
                result['source'] = 'generated'
                result['image_base64'] = image_base64
                return result
        except Exception as e:
            logger.error(f"Fallback chart generation failed: {e}")
            result['error'] = f"Both methods failed: {result.get('error', '')}; {str(e)}"
        
        return result
    
    def save_screenshot(self, image_base64: str, filename: str = None) -> str:
        """
        Save base64 image to file
        
        Args:
            image_base64: Base64 encoded image
            filename: Optional filename (will generate if not provided)
            
        Returns:
            Path to saved file
        """
        if not filename:
            filename = f"chart_{int(time.time())}.png"
        
        # Create temp directory if it doesn't exist
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, filename)
        
        # Decode and save
        img_data = base64.b64decode(image_base64)
        with open(filepath, 'wb') as f:
            f.write(img_data)
        
        logger.info(f"Screenshot saved to {filepath}")
        return filepath
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome WebDriver closed")
            except:
                pass
            self.driver = None
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

# Singleton instance
screenshot_service = ScreenshotService()
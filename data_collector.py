"""
Market Data Collector
Real-time data collection from multiple cryptocurrency exchanges
"""
import ccxt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class MarketDataCollector:
    """Multi-exchange market data collector with error handling"""
    
    def __init__(self, config):
        self.config = config
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.logger = logging.getLogger(__name__)
        self._initialize_exchanges()
        self.last_fetch_time = {}
        self.market_data_cache = {}
    
    def _initialize_exchanges(self) -> None:
        """Initialize exchange connections with rate limiting"""
        exchange_classes = {
            'binance': ccxt.binance,
            'coinbase': ccxt.coinbase
        }
        
        for exchange_name in self.config.get_active_exchanges():
            try:
                if exchange_name in exchange_classes:
                    exchange_class = exchange_classes[exchange_name]
                    exchange_config = self.config.exchanges[exchange_name]
                    
                    self.exchanges[exchange_name] = exchange_class({
                        'apiKey': exchange_config.api_key,
                        'secret': exchange_config.api_secret,
                        'enableRateLimit': True,
                        'timeout': exchange_config.timeout * 1000,
                        'options': {
                            'defaultType': 'spot',
                            'adjustForTimeDifference': True
                        }
                    })
                    
                    # Test connection
                    self.exchanges[exchange_name].load_markets()
                    self.logger.info(f"Successfully connected to {exchange_name}")
                    
            except ccxt.AuthenticationError as e:
                self.logger.error(f"Authentication failed for {exchange_name}: {e}")
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error for {exchange_name}: {e}")
            except Exception as e:
                self.logger.error(f"Failed to initialize {exchange_name}: {e}")
    
    def fetch_ohlcv(
        self, 
        symbol: str, 
        timeframe: str = '1m',
        limit: int = 100,
        exchange_name: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV (Open, High, Low, Close, Volume) data
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe
            limit: Number of candles to fetch
            exchange_name: Specific exchange to use
            
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        exchanges_to_use = [exchange_name] if exchange_name else list(self.exchanges.keys())
        
        for name in exchanges_to_use:
            if name not in self.exchanges:
                continue
                
            try:
                exchange = self.exchanges[name]
                
                # Check rate limits
                current_time = time.time()
                if name in self.last_fetch_time:
                    time_since_last = current_time - self.last_fetch_time[name]
                    if time_since_last < 1.0 / exchange.rateLimit:
                        time.sleep(1.0 / exchange.rateLimit - time_since_last)
                
                # Fetch data
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                self.last_fetch_time[name] = time.time()
                
                if ohlcv and len(ohlcv) > 0:
                    df = pd.DataFrame(
                        ohlcv, 
                        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    )
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
"""
AMIN Configuration Management
Centralized configuration with environment variable support
"""
import os
import logging
from typing import Dict, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ExchangeConfig:
    """Exchange-specific configuration"""
    name: str
    api_key: str = ""
    api_secret: str = ""
    rate_limit: int = 10
    timeout: int = 30

@dataclass
class FirebaseConfig:
    """Firebase configuration"""
    project_id: str = ""
    credentials_path: str = ""
    collection_name: str = "amin_market_data"

class Config:
    """Central configuration manager"""
    
    def __init__(self):
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        # Exchange configurations
        self.exchanges = {
            "binance": ExchangeConfig(
                name="binance",
                api_key=os.getenv("BINANCE_API_KEY", ""),
                api_secret=os.getenv("BINANCE_API_SECRET", "")
            ),
            "coinbase": ExchangeConfig(
                name="coinbase",
                api_key=os.getenv("COINBASE_API_KEY", ""),
                api_secret=os.getenv("COINBASE_API_SECRET", "")
            )
        }
        
        # Firebase configuration
        self.firebase = FirebaseConfig(
            project_id=os.getenv("FIREBASE_PROJECT_ID", ""),
            credentials_path=os.getenv("FIREBASE_CREDENTIALS_PATH", ""),
            collection_name=os.getenv("FIREBASE_COLLECTION", "amin_market_data")
        )
        
        # Data processing settings
        self.data_settings = {
            "window_size": int(os.getenv("WINDOW_SIZE", "100")),
            "polling_interval": int(os.getenv("POLLING_INTERVAL", "60")),
            "symbols": os.getenv("SYMBOLS", "BTC/USDT,ETH/USDT").split(",")
        }
        
        # Model settings
        self.model_settings = {
            "prediction_horizon": int(os.getenv("PREDICTION_HORIZON", "5")),
            "confidence_threshold": float(os.getenv("CONFIDENCE_THRESHOLD", "0.7")),
            "retrain_interval": int(os.getenv("RETRAIN_INTERVAL", "3600"))
        }
        
        # Validate critical configurations
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate critical configuration parameters"""
        if not self.exchanges["binance"].api_key and self.environment == "production":
            logging.warning("Binance API key not configured")
        
        if not self.firebase.project_id and self.environment == "production":
            logging.error("Firebase project ID required for production")
            raise ValueError("Firebase configuration missing")
    
    def get_active_exchanges(self) -> list:
        """Get list of exchanges with API credentials configured"""
        active = []
        for name, exchange in self.exchanges.items():
            if exchange.api_key and exchange.api_secret:
                active.append(name)
        return active

# Global configuration instance
config = Config()
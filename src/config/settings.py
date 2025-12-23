"""
Configuration management for the trading platform
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ENV_PATH = Path(__file__).parent.parent.parent / '.env'
load_dotenv(ENV_PATH)

class DatabaseConfig:
    """Database connection configuration"""
    HOST = os.getenv('DB_HOST', 'localhost')
    PORT = int(os.getenv('DB_PORT', '5432'))
    NAME = os.getenv('DB_NAME', 'trading_db')
    USER = os.getenv('DB_USER', 'trading_user')
    PASSWORD = os.getenv('DB_PASSWORD', '')
    
    @classmethod
    def get_connection_string(cls):
        """Get PostgreSQL connection string"""
        return f"postgresql://{cls.USER}:{cls.PASSWORD}@{cls.HOST}:{cls.PORT}/{cls.NAME}"


class TradingConfig:
    """Trading platform configuration"""
    
    # Market settings
    MARKET = 'NSE'  # National Stock Exchange
    TIMEZONE = 'Asia/Kolkata'
    MARKET_OPEN = '09:15'
    MARKET_CLOSE = '15:30'
    
    # Data settings
    DEFAULT_TIMEFRAMES = ['1m', '5m', '15m', '1h', '1d']
    HISTORICAL_DATA_DAYS = 365  # Days of historical data to fetch
    
    # Risk management
    MAX_POSITION_SIZE = 0.1  # 10% of portfolio per position
    MAX_PORTFOLIO_RISK = 0.02  # 2% max risk per trade
    MAX_DRAWDOWN_LIMIT = 0.15  # 15% max drawdown before halt
    
    # Backtesting
    INITIAL_CAPITAL = 100000  # INR
    COMMISSION_RATE = 0.0003  # 0.03% per trade
    SLIPPAGE_RATE = 0.0001  # 0.01% slippage
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = Path(__file__).parent.parent.parent / 'logs'
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        cls.LOG_DIR.mkdir(exist_ok=True)


class DataConfig:
    """Data source configuration"""
    
    # yfinance settings
    YFINANCE_ENABLED = True
    YFINANCE_MAX_WORKERS = 5  # Parallel downloads
    
    # Cache settings
    CACHE_ENABLED = True
    CACHE_DIR = Path(__file__).parent.parent.parent / 'cache'
    CACHE_EXPIRY_HOURS = 24
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        cls.CACHE_DIR.mkdir(exist_ok=True)


# Initialize directories on import
TradingConfig.ensure_directories()
DataConfig.ensure_directories()

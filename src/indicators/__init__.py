"""
Technical Indicators Library

Comprehensive technical analysis indicators using TA-Lib and pandas-ta

Usage:
    from src.indicators import TrendIndicators, MomentumIndicators
    
    # Load data
    df = ...  # DataFrame with OHLCV data
    
    # Calculate indicators
    trend = TrendIndicators(df)
    ema_20 = trend.ema(period=20)
    rsi = MomentumIndicators(df).rsi(period=14)
"""

from .base import BaseIndicator
from .trend import TrendIndicators
from .momentum import MomentumIndicators
from .volatility import VolatilityIndicators
from .volume import VolumeIndicators
from .patterns import CandlestickPatterns
from .fibonacci import FibonacciLevels
from .support_resistance import SupportResistance
from .pivot_support_resistance import PivotSupportResistance

__all__ = [
    'BaseIndicator',
    'TrendIndicators',
    'MomentumIndicators',
    'VolatilityIndicators',
    'VolumeIndicators',
    'CandlestickPatterns',
    'FibonacciLevels',
    'SupportResistance',
    'PivotSupportResistance',
]

__version__ = '1.0.0'

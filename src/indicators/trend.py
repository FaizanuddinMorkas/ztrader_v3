"""
Trend indicators using TA-Lib and pandas-ta

Provides moving averages and trend-following indicators
"""

import pandas as pd
import numpy as np
from typing import Optional
import talib
import pandas_ta as ta

from .base import BaseIndicator


class TrendIndicators(BaseIndicator):
    """
    Trend-based technical indicators
    
    Includes moving averages and trend identification tools
    """
    
    # ============================================================================
    # Moving Averages
    # ============================================================================
    
    def ema(self, period: int = 20, column: str = 'close') -> pd.Series:
        """
        Exponential Moving Average (EMA)
        
        Fast-reacting moving average that gives more weight to recent prices
        
        Args:
            period: Number of periods (default: 20)
            column: Column to calculate on (default: 'close')
            
        Returns:
            Series with EMA values
        """
        self.validate_period(period)
        data = self.get_column(column)
        return pd.Series(talib.EMA(data, timeperiod=period), index=self.df.index, name=f'EMA_{period}')
    
    def sma(self, period: int = 20, column: str = 'close') -> pd.Series:
        """
        Simple Moving Average (SMA)
        
        Arithmetic mean of prices over the specified period
        
        Args:
            period: Number of periods (default: 20)
            column: Column to calculate on (default: 'close')
            
        Returns:
            Series with SMA values
        """
        self.validate_period(period)
        data = self.get_column(column)
        return pd.Series(talib.SMA(data, timeperiod=period), index=self.df.index, name=f'SMA_{period}')
    
    def wma(self, period: int = 20, column: str = 'close') -> pd.Series:
        """
        Weighted Moving Average (WMA)
        
        Moving average with linear weighting (recent prices weighted more)
        
        Args:
            period: Number of periods (default: 20)
            column: Column to calculate on (default: 'close')
            
        Returns:
            Series with WMA values
        """
        self.validate_period(period)
        data = self.get_column(column)
        return pd.Series(talib.WMA(data, timeperiod=period), index=self.df.index, name=f'WMA_{period}')
    
    def dema(self, period: int = 20, column: str = 'close') -> pd.Series:
        """
        Double Exponential Moving Average (DEMA)
        
        Faster-reacting EMA with reduced lag
        
        Args:
            period: Number of periods (default: 20)
            column: Column to calculate on (default: 'close')
            
        Returns:
            Series with DEMA values
        """
        self.validate_period(period)
        data = self.get_column(column)
        return pd.Series(talib.DEMA(data, timeperiod=period), index=self.df.index, name=f'DEMA_{period}')
    
    def tema(self, period: int = 20, column: str = 'close') -> pd.Series:
        """
        Triple Exponential Moving Average (TEMA)
        
        Fastest-reacting EMA with minimal lag
        
        Args:
            period: Number of periods (default: 20)
            column: Column to calculate on (default: 'close')
            
        Returns:
            Series with TEMA values
        """
        self.validate_period(period)
        data = self.get_column(column)
        return pd.Series(talib.TEMA(data, timeperiod=period), index=self.df.index, name=f'TEMA_{period}')
    
    # ============================================================================
    # Trend Identification
    # ============================================================================
    
    def adx(self, period: int = 14) -> pd.DataFrame:
        """
        Average Directional Index (ADX)
        
        Measures trend strength (0-100). Values > 25 indicate strong trend
        
        Args:
            period: Number of periods (default: 14)
            
        Returns:
            DataFrame with ADX, +DI, -DI columns
        """
        self.validate_period(period)
        
        adx = talib.ADX(self.df['high'], self.df['low'], self.df['close'], timeperiod=period)
        plus_di = talib.PLUS_DI(self.df['high'], self.df['low'], self.df['close'], timeperiod=period)
        minus_di = talib.MINUS_DI(self.df['high'], self.df['low'], self.df['close'], timeperiod=period)
        
        return pd.DataFrame({
            'ADX': adx,
            'PLUS_DI': plus_di,
            'MINUS_DI': minus_di
        }, index=self.df.index)
    
    def supertrend(self, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
        """
        SuperTrend Indicator (pandas-ta only)
        
        Trend-following indicator based on ATR
        
        Args:
            period: ATR period (default: 10)
            multiplier: ATR multiplier (default: 3.0)
            
        Returns:
            DataFrame with SuperTrend, direction, long, short columns
        """
        self.validate_period(period)
        
        # pandas-ta supertrend
        df_copy = self.df.copy()
        st = df_copy.ta.supertrend(length=period, multiplier=multiplier)
        
        return st
    
    def parabolic_sar(self, acceleration: float = 0.02, maximum: float = 0.2) -> pd.Series:
        """
        Parabolic SAR (Stop and Reverse)
        
        Trend-following indicator that provides entry/exit points
        
        Args:
            acceleration: Acceleration factor (default: 0.02)
            maximum: Maximum acceleration (default: 0.2)
            
        Returns:
            Series with SAR values
        """
        sar = talib.SAR(self.df['high'], self.df['low'], 
                       acceleration=acceleration, maximum=maximum)
        
        return pd.Series(sar, index=self.df.index, name='SAR')

"""
Volatility indicators using TA-Lib and pandas-ta

Provides volatility and price channel indicators
"""

import pandas as pd
import numpy as np
import talib
import pandas_ta as ta

from .base import BaseIndicator


class VolatilityIndicators(BaseIndicator):
    """
    Volatility-based technical indicators
    
    Includes Bollinger Bands, ATR, Keltner Channels, etc.
    """
    
    # ============================================================================
    # Volatility Measures
    # ============================================================================
    
    def atr(self, period: int = 14) -> pd.Series:
        """
        Average True Range (ATR)
        
        Measures market volatility
        
        Args:
            period: Number of periods (default: 14)
            
        Returns:
            Series with ATR values
        """
        self.validate_period(period)
        atr = talib.ATR(self.df['high'], self.df['low'], self.df['close'], timeperiod=period)
        return pd.Series(atr, index=self.df.index, name=f'ATR_{period}')
    
    def natr(self, period: int = 14) -> pd.Series:
        """
        Normalized Average True Range (NATR)
        
        ATR as a percentage of close price
        
        Args:
            period: Number of periods (default: 14)
            
        Returns:
            Series with NATR values
        """
        self.validate_period(period)
        natr = talib.NATR(self.df['high'], self.df['low'], self.df['close'], timeperiod=period)
        return pd.Series(natr, index=self.df.index, name=f'NATR_{period}')
    
    # ============================================================================
    # Price Channels
    # ============================================================================
    
    def bollinger_bands(self, period: int = 20, std: float = 2.0, 
                       column: str = 'close') -> pd.DataFrame:
        """
        Bollinger Bands
        
        Volatility bands around a moving average
        
        Args:
            period: MA period (default: 20)
            std: Standard deviation multiplier (default: 2.0)
            column: Column to calculate on (default: 'close')
            
        Returns:
            DataFrame with upper, middle, lower bands
        """
        self.validate_period(period)
        data = self.get_column(column)
        
        upper, middle, lower = talib.BBANDS(
            data,
            timeperiod=period,
            nbdevup=std,
            nbdevdn=std,
            matype=0
        )
        
        return pd.DataFrame({
            'BB_upper': upper,
            'BB_middle': middle,
            'BB_lower': lower,
            'BB_width': upper - lower,
            'BB_percent': (data - lower) / (upper - lower) * 100
        }, index=self.df.index)
    
    def keltner_channels(self, period: int = 20, atr_period: int = 10,
                        multiplier: float = 2.0) -> pd.DataFrame:
        """
        Keltner Channels
        
        Volatility bands based on ATR
        
        Args:
            period: EMA period (default: 20)
            atr_period: ATR period (default: 10)
            multiplier: ATR multiplier (default: 2.0)
            
        Returns:
            DataFrame with upper, middle, lower channels
        """
        df_copy = self.df.copy()
        kc = df_copy.ta.kc(length=period, scalar=multiplier, mamode='ema')
        return kc
    
    def donchian_channels(self, period: int = 20) -> pd.DataFrame:
        """
        Donchian Channels
        
        Price channels based on highest high and lowest low
        
        Args:
            period: Number of periods (default: 20)
            
        Returns:
            DataFrame with upper, middle, lower channels
        """
        df_copy = self.df.copy()
        dc = df_copy.ta.donchian(lower_length=period, upper_length=period)
        return dc
    
    # ============================================================================
    # Volatility Oscillators
    # ============================================================================
    
    def historical_volatility(self, period: int = 20, 
                             annualize: bool = True) -> pd.Series:
        """
        Historical Volatility
        
        Standard deviation of log returns
        
        Args:
            period: Number of periods (default: 20)
            annualize: Annualize the volatility (default: True)
            
        Returns:
            Series with volatility values
        """
        self.validate_period(period)
        
        # Calculate log returns
        log_returns = np.log(self.df['close'] / self.df['close'].shift(1))
        
        # Calculate rolling standard deviation
        volatility = log_returns.rolling(window=period).std()
        
        # Annualize if requested (assuming 252 trading days)
        if annualize:
            volatility = volatility * np.sqrt(252)
        
        return pd.Series(volatility, index=self.df.index, name=f'HV_{period}')

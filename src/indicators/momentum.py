"""
Momentum indicators using TA-Lib and pandas-ta

Provides oscillators and momentum-based indicators
"""

import pandas as pd
import numpy as np
import talib
import pandas_ta as ta

from .base import BaseIndicator


class MomentumIndicators(BaseIndicator):
    """
    Momentum-based technical indicators
    
    Includes oscillators like RSI, MACD, Stochastic, etc.
    """
    
    # ============================================================================
    # Oscillators
    # ============================================================================
    
    def rsi(self, period: int = 14, column: str = 'close') -> pd.Series:
        """
        Relative Strength Index (RSI)
        
        Momentum oscillator (0-100). Values > 70 = overbought, < 30 = oversold
        
        Args:
            period: Number of periods (default: 14)
            column: Column to calculate on (default: 'close')
            
        Returns:
            Series with RSI values
        """
        self.validate_period(period)
        data = self.get_column(column)
        return pd.Series(talib.RSI(data, timeperiod=period), index=self.df.index, name=f'RSI_{period}')
    
    def macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        Moving Average Convergence Divergence (MACD)
        
        Trend-following momentum indicator
        
        Args:
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line period (default: 9)
            
        Returns:
            DataFrame with MACD, signal, and histogram columns
        """
        macd, signal_line, histogram = talib.MACD(
            self.df['close'],
            fastperiod=fast,
            slowperiod=slow,
            signalperiod=signal
        )
        
        return pd.DataFrame({
            'MACD': macd,
            'MACD_signal': signal_line,
            'MACD_histogram': histogram
        }, index=self.df.index)
    
    def stochastic(self, k_period: int = 14, d_period: int = 3, 
                   slowing: int = 3) -> pd.DataFrame:
        """
        Stochastic Oscillator
        
        Momentum indicator comparing close to price range (0-100)
        
        Args:
            k_period: %K period (default: 14)
            d_period: %D period (default: 3)
            slowing: Slowing period (default: 3)
            
        Returns:
            DataFrame with %K and %D columns
        """
        slowk, slowd = talib.STOCH(
            self.df['high'],
            self.df['low'],
            self.df['close'],
            fastk_period=k_period,
            slowk_period=slowing,
            slowk_matype=0,
            slowd_period=d_period,
            slowd_matype=0
        )
        
        return pd.DataFrame({
            'STOCH_K': slowk,
            'STOCH_D': slowd
        }, index=self.df.index)
    
    def cci(self, period: int = 20) -> pd.Series:
        """
        Commodity Channel Index (CCI)
        
        Momentum oscillator. Values > +100 = overbought, < -100 = oversold
        
        Args:
            period: Number of periods (default: 20)
            
        Returns:
            Series with CCI values
        """
        self.validate_period(period)
        cci = talib.CCI(self.df['high'], self.df['low'], self.df['close'], timeperiod=period)
        return pd.Series(cci, index=self.df.index, name=f'CCI_{period}')
    
    def williams_r(self, period: int = 14) -> pd.Series:
        """
        Williams %R
        
        Momentum indicator (-100 to 0). Values > -20 = overbought, < -80 = oversold
        
        Args:
            period: Number of periods (default: 14)
            
        Returns:
            Series with Williams %R values
        """
        self.validate_period(period)
        willr = talib.WILLR(self.df['high'], self.df['low'], self.df['close'], timeperiod=period)
        return pd.Series(willr, index=self.df.index, name=f'WILLR_{period}')
    
    def roc(self, period: int = 12, column: str = 'close') -> pd.Series:
        """
        Rate of Change (ROC)
        
        Momentum indicator showing percentage change
        
        Args:
            period: Number of periods (default: 12)
            column: Column to calculate on (default: 'close')
            
        Returns:
            Series with ROC values
        """
        self.validate_period(period)
        data = self.get_column(column)
        roc = talib.ROC(data, timeperiod=period)
        return pd.Series(roc, index=self.df.index, name=f'ROC_{period}')
    
    def momentum(self, period: int = 10, column: str = 'close') -> pd.Series:
        """
        Momentum
        
        Difference between current price and price N periods ago
        
        Args:
            period: Number of periods (default: 10)
            column: Column to calculate on (default: 'close')
            
        Returns:
            Series with Momentum values
        """
        self.validate_period(period)
        data = self.get_column(column)
        mom = talib.MOM(data, timeperiod=period)
        return pd.Series(mom, index=self.df.index, name=f'MOM_{period}')
    
    # ============================================================================
    # Advanced Momentum (pandas-ta)
    # ============================================================================
    
    def stochrsi(self, period: int = 14, rsi_period: int = 14, 
                 k: int = 3, d: int = 3) -> pd.DataFrame:
        """
        Stochastic RSI
        
        Stochastic oscillator applied to RSI values
        
        Args:
            period: Stochastic period (default: 14)
            rsi_period: RSI period (default: 14)
            k: %K smoothing (default: 3)
            d: %D smoothing (default: 3)
            
        Returns:
            DataFrame with StochRSI K and D columns
        """
        df_copy = self.df.copy()
        stochrsi = df_copy.ta.stochrsi(length=rsi_period, rsi_length=rsi_period, k=k, d=d)
        return stochrsi
    
    def tsi(self, fast: int = 13, slow: int = 25, signal: int = 13) -> pd.DataFrame:
        """
        True Strength Index (TSI)
        
        Momentum oscillator based on double-smoothed momentum
        
        Args:
            fast: Fast period (default: 13)
            slow: Slow period (default: 25)
            signal: Signal period (default: 13)
            
        Returns:
            DataFrame with TSI and signal columns
        """
        df_copy = self.df.copy()
        tsi = df_copy.ta.tsi(fast=fast, slow=slow, signal=signal)
        return tsi

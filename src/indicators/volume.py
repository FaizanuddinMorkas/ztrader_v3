"""
Volume indicators using TA-Lib and pandas-ta

Provides volume-based indicators and money flow analysis
"""

import pandas as pd
import numpy as np
import talib
import pandas_ta as ta

from .base import BaseIndicator


class VolumeIndicators(BaseIndicator):
    """
    Volume-based technical indicators
    
    Includes OBV, VWAP, MFI, etc.
    """
    
    # ============================================================================
    # Volume Flow
    # ============================================================================
    
    def obv(self) -> pd.Series:
        """
        On-Balance Volume (OBV)
        
        Cumulative volume indicator based on price direction
        
        Returns:
            Series with OBV values
        """
        obv = talib.OBV(self.df['close'], self.df['volume'])
        return pd.Series(obv, index=self.df.index, name='OBV')
    
    def ad(self) -> pd.Series:
        """
        Accumulation/Distribution Line
        
        Volume indicator that measures money flow
        
        Returns:
            Series with A/D values
        """
        ad = talib.AD(self.df['high'], self.df['low'], self.df['close'], self.df['volume'])
        return pd.Series(ad, index=self.df.index, name='AD')
    
    def adosc(self, fast: int = 3, slow: int = 10) -> pd.Series:
        """
        Accumulation/Distribution Oscillator
        
        Difference between fast and slow A/D
        
        Args:
            fast: Fast period (default: 3)
            slow: Slow period (default: 10)
            
        Returns:
            Series with ADOSC values
        """
        adosc = talib.ADOSC(
            self.df['high'],
            self.df['low'],
            self.df['close'],
            self.df['volume'],
            fastperiod=fast,
            slowperiod=slow
        )
        return pd.Series(adosc, index=self.df.index, name='ADOSC')
    
    # ============================================================================
    # Money Flow
    # ============================================================================
    
    def mfi(self, period: int = 14) -> pd.Series:
        """
        Money Flow Index (MFI)
        
        Volume-weighted RSI. Values > 80 = overbought, < 20 = oversold
        
        Args:
            period: Number of periods (default: 14)
            
        Returns:
            Series with MFI values
        """
        self.validate_period(period)
        mfi = talib.MFI(
            self.df['high'],
            self.df['low'],
            self.df['close'],
            self.df['volume'],
            timeperiod=period
        )
        return pd.Series(mfi, index=self.df.index, name=f'MFI_{period}')
    
    def cmf(self, period: int = 20) -> pd.Series:
        """
        Chaikin Money Flow (CMF)
        
        Measures buying/selling pressure
        
        Args:
            period: Number of periods (default: 20)
            
        Returns:
            Series with CMF values
        """
        df_copy = self.df.copy()
        cmf = df_copy.ta.cmf(length=period)
        return cmf
    
    # ============================================================================
    # Volume-Weighted Prices
    # ============================================================================
    
    def vwap(self) -> pd.Series:
        """
        Volume Weighted Average Price (VWAP)
        
        Average price weighted by volume
        
        Returns:
            Series with VWAP values
        """
        df_copy = self.df.copy()
        vwap = df_copy.ta.vwap()
        return vwap
    
    def vwma(self, period: int = 20) -> pd.Series:
        """
        Volume Weighted Moving Average (VWMA)
        
        Moving average weighted by volume
        
        Args:
            period: Number of periods (default: 20)
            
        Returns:
            Series with VWMA values
        """
        df_copy = self.df.copy()
        vwma = df_copy.ta.vwma(length=period)
        return vwma
    
    # ============================================================================
    # Volume Analysis
    # ============================================================================
    
    def volume_sma(self, period: int = 20) -> pd.Series:
        """
        Volume Simple Moving Average
        
        Average volume over period
        
        Args:
            period: Number of periods (default: 20)
            
        Returns:
            Series with volume SMA values
        """
        self.validate_period(period)
        vol_sma = talib.SMA(self.df['volume'], timeperiod=period)
        return pd.Series(vol_sma, index=self.df.index, name=f'VOL_SMA_{period}')
    
    def volume_ratio(self, period: int = 20) -> pd.Series:
        """
        Volume Ratio
        
        Current volume / average volume
        
        Args:
            period: Number of periods for average (default: 20)
            
        Returns:
            Series with volume ratio values
        """
        vol_sma = self.volume_sma(period)
        ratio = self.df['volume'] / vol_sma
        return pd.Series(ratio, index=self.df.index, name=f'VOL_RATIO_{period}')

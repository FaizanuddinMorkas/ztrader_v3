"""
Base class for all technical indicators
"""

import pandas as pd
import numpy as np
from typing import Union, Optional


class BaseIndicator:
    """
    Base class for all technical indicators
    
    Provides common functionality for data validation and indicator calculation
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize indicator with OHLCV data
        
        Args:
            df: DataFrame with OHLCV data (open, high, low, close, volume)
        """
        self.df = df.copy()
        self.validate_data()
    
    def validate_data(self):
        """
        Validate that required columns exist in the DataFrame
        
        Raises:
            ValueError: If required columns are missing
        """
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in self.df.columns]
        
        if missing_cols:
            raise ValueError(
                f"Missing required columns: {missing_cols}. "
                f"DataFrame must contain: {required_cols}"
            )
    
    @staticmethod
    def validate_period(period: int, min_period: int = 1):
        """
        Validate period parameter
        
        Args:
            period: Period value to validate
            min_period: Minimum allowed period
            
        Raises:
            ValueError: If period is invalid
        """
        if not isinstance(period, int) or period < min_period:
            raise ValueError(f"Period must be an integer >= {min_period}")
    
    def get_column(self, column: str = 'close') -> pd.Series:
        """
        Get a specific column from the DataFrame
        
        Args:
            column: Column name (default: 'close')
            
        Returns:
            Series with the requested column data
            
        Raises:
            ValueError: If column doesn't exist
        """
        if column not in self.df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
        
        return self.df[column]

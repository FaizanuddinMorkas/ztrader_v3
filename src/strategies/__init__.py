"""
Trading strategies module
"""

from .base import BaseStrategy
from .multi_indicator import MultiIndicatorStrategy
from .multi_indicator_scored import MultiIndicatorScoredStrategy
from .signal_generator import SignalGenerator
from .signal_generator_scored import SignalGeneratorScored

__all__ = [
    'BaseStrategy',
    'MultiIndicatorStrategy',
    'MultiIndicatorScoredStrategy',
    'SignalGenerator',
    'SignalGeneratorScored',
]

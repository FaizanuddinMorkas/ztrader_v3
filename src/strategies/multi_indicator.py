"""
Multi-Indicator Trading Strategy

Combines trend, momentum, and volatility analysis with weighted confidence scoring.

Strategy Logic:
- Trend (40%): EMA 8/20/50, MACD
- Momentum (35%): RSI, Stochastic  
- Volatility (25%): ATR, Bollinger Bands
- Generates BUY signals with confidence ≥ 65%
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

from .base import BaseStrategy
from src.indicators import TrendIndicators, MomentumIndicators, VolatilityIndicators, FibonacciLevels, PivotSupportResistance as SupportResistance

logger = logging.getLogger(__name__)


class MultiIndicatorStrategy(BaseStrategy):
    """
    Multi-indicator composite strategy
    
    Analyzes trend, momentum, and volatility to generate high-confidence signals
    """
    
    # Weights for composite confidence
    TREND_WEIGHT = 0.40
    MOMENTUM_WEIGHT = 0.35
    VOLATILITY_WEIGHT = 0.25
    
    # Minimum confidence threshold
    MIN_CONFIDENCE = 65.0
    
    def calculate_indicators(self):
        """Calculate all required indicators"""
        logger.info(f"Calculating indicators for {self.symbol}")
        
        # Initialize indicator calculators
        trend = TrendIndicators(self.df)
        momentum = MomentumIndicators(self.df)
        volatility = VolatilityIndicators(self.df)
        
        # Trend indicators
        self.df['ema_8'] = trend.ema(period=8)
        self.df['ema_20'] = trend.ema(period=20)
        self.df['ema_50'] = trend.ema(period=50)
        
        macd_data = momentum.macd(fast=12, slow=26, signal=9)
        self.df['macd'] = macd_data['MACD']
        self.df['macd_signal'] = macd_data['MACD_signal']
        self.df['macd_hist'] = macd_data['MACD_histogram']
        
        # Momentum indicators
        self.df['rsi'] = momentum.rsi(period=14)
        
        stoch_data = momentum.stochastic(k_period=14, d_period=3)
        self.df['stoch_k'] = stoch_data['STOCH_K']
        self.df['stoch_d'] = stoch_data['STOCH_D']
        
        # Volatility indicators
        self.df['atr'] = volatility.atr(period=14)
        
        bb_data = volatility.bollinger_bands(period=20, std=2.0)
        self.df['bb_upper'] = bb_data['BB_upper']
        self.df['bb_middle'] = bb_data['BB_middle']
        self.df['bb_lower'] = bb_data['BB_lower']
        self.df['bb_width'] = bb_data['BB_width']
        
        # Fibonacci levels
        fib = FibonacciLevels(self.df)
        self.fib_levels = fib.get_all_levels(lookback=50)
        
        logger.info(f"✓ Indicators calculated for {self.symbol}")
    
    def analyze_trend(self) -> Dict:
        """
        Analyze trend indicators (40% weight)
        
        Checks:
        1. EMA 8 > EMA 20 > EMA 50 (bullish alignment)
        2. Price > EMA 8
        3. MACD > Signal
        4. MACD > 0
        5. MACD histogram increasing
        
        Returns:
            {score: 0-100, conditions_met: 0-5, details: dict}
        """
        latest = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        
        conditions = []
        
        # 1. EMA alignment
        ema_aligned = (latest['ema_8'] > latest['ema_20'] > latest['ema_50'])
        conditions.append(ema_aligned)
        
        # 2. Price > EMA 8
        price_above_ema8 = latest['close'] > latest['ema_8']
        conditions.append(price_above_ema8)
        
        # 3. MACD > Signal
        macd_bullish = latest['macd'] > latest['macd_signal']
        conditions.append(macd_bullish)
        
        # 4. MACD > 0
        macd_positive = latest['macd'] > 0
        conditions.append(macd_positive)
        
        # 5. MACD histogram increasing
        macd_hist_increasing = latest['macd_hist'] > prev['macd_hist']
        conditions.append(macd_hist_increasing)
        
        # Calculate score
        conditions_met = sum(conditions)
        score = (conditions_met / 5) * 100
        
        return {
            'score': score,
            'conditions_met': conditions_met,
            'total_conditions': 5,
            'details': {
                'ema_aligned': ema_aligned,
                'price_above_ema8': price_above_ema8,
                'macd_bullish': macd_bullish,
                'macd_positive': macd_positive,
                'macd_hist_increasing': macd_hist_increasing
            }
        }
    
    def analyze_momentum(self) -> Dict:
        """
        Analyze momentum indicators (35% weight)
        
        Checks:
        1. RSI between 40-75 (not oversold/overbought)
        2. Stochastic %K < 80 (not overbought)
        3. Stochastic %K > %D (bullish crossover)
        
        Returns:
            {score: 0-100, conditions_met: 0-3, details: dict}
        """
        latest = self.df.iloc[-1]
        
        conditions = []
        
        # 1. RSI in healthy range
        rsi_healthy = 40 <= latest['rsi'] <= 75
        conditions.append(rsi_healthy)
        
        # 2. Stochastic not overbought
        stoch_not_overbought = latest['stoch_k'] < 80
        conditions.append(stoch_not_overbought)
        
        # 3. Stochastic bullish crossover
        stoch_bullish = latest['stoch_k'] > latest['stoch_d']
        conditions.append(stoch_bullish)
        
        # Calculate score
        conditions_met = sum(conditions)
        score = (conditions_met / 3) * 100
        
        return {
            'score': score,
            'conditions_met': conditions_met,
            'total_conditions': 3,
            'details': {
                'rsi': latest['rsi'],
                'rsi_healthy': rsi_healthy,
                'stoch_k': latest['stoch_k'],
                'stoch_not_overbought': stoch_not_overbought,
                'stoch_bullish': stoch_bullish
            }
        }
    
    def analyze_volatility(self) -> Dict:
        """
        Analyze volatility indicators (25% weight)
        
        Checks:
        1. Price near lower Bollinger Band (potential bounce)
        2. ATR increasing (volatility expansion)
        3. Bollinger Band width expanding
        
        Returns:
            {score: 0-100, conditions_met: 0-3, details: dict}
        """
        latest = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        
        conditions = []
        
        # 1. Price near lower BB (within 10% of band)
        bb_range = latest['bb_upper'] - latest['bb_lower']
        distance_from_lower = latest['close'] - latest['bb_lower']
        near_lower_bb = distance_from_lower < (bb_range * 0.3)
        conditions.append(near_lower_bb)
        
        # 2. ATR increasing
        atr_increasing = latest['atr'] > prev['atr']
        conditions.append(atr_increasing)
        
        # 3. BB width expanding
        bb_expanding = latest['bb_width'] > prev['bb_width']
        conditions.append(bb_expanding)
        
        # Calculate score
        conditions_met = sum(conditions)
        score = (conditions_met / 3) * 100
        
        return {
            'score': score,
            'conditions_met': conditions_met,
            'total_conditions': 3,
            'details': {
                'near_lower_bb': near_lower_bb,
                'atr_increasing': atr_increasing,
                'bb_expanding': bb_expanding,
                'atr': latest['atr']
            }
        }
    
    def analyze(self) -> Dict:
        """
        Perform complete analysis
        
        Returns:
            Complete analysis with weighted confidence score
        """
        # Analyze each category
        trend_analysis = self.analyze_trend()
        momentum_analysis = self.analyze_momentum()
        volatility_analysis = self.analyze_volatility()
        
        # Calculate weighted confidence
        confidence = (
            trend_analysis['score'] * self.TREND_WEIGHT +
            momentum_analysis['score'] * self.MOMENTUM_WEIGHT +
            volatility_analysis['score'] * self.VOLATILITY_WEIGHT
        )
        
        # Count strong conditions (≥60% score)
        strong_conditions = sum([
            trend_analysis['score'] >= 60,
            momentum_analysis['score'] >= 60,
            volatility_analysis['score'] >= 60
        ])
        
        return {
            'confidence': confidence,
            'strong_conditions': strong_conditions,
            'trend': trend_analysis,
            'momentum': momentum_analysis,
            'volatility': volatility_analysis
        }
    
    def calculate_stop_loss(self, entry_price: float) -> float:
        """
        Calculate stop-loss using Support/Resistance levels
        
        Primary: 1% below nearest support level (actual swing low)
        Fallback: Conservative EMA/ATR-based if S/R too far
        
        Args:
            entry_price: Entry price
            
        Returns:
            Stop-loss price
        """
        latest = self.df.iloc[-1]
        
        # Primary: S/R-based stop-loss
        sr = SupportResistance(self.df)
        nearest_support = sr.get_nearest_support(entry_price, min_distance=0.005)  # Min 0.5% away
        
        if nearest_support:
            sl_sr = nearest_support['price'] * 0.99  # 1% below support
            risk_pct = (entry_price - sl_sr) / entry_price
            
            # Validate: Risk should be reasonable (0.5% to 5%)
            if 0.005 <= risk_pct <= 0.05:
                logger.info(f"S/R Stop-Loss: ₹{sl_sr:.2f} (below support at ₹{nearest_support['price']:.2f}, risk: {risk_pct*100:.1f}%)")
                return sl_sr
            else:
                logger.warning(f"S/R stop too far ({risk_pct*100:.1f}%), using fallback")
        
        # Fallback: Conservative technical stops
        sl_ema = latest['ema_8'] * 0.997  # 0.3% below EMA 8
        sl_atr = entry_price - (1.0 * latest['atr'])  # 1 ATR
        sl_fixed = entry_price * 0.98  # 2% fixed
        
        stop_loss = max(sl_ema, sl_atr, sl_fixed)  # Use tightest valid stop
        logger.info(f"Fallback Stop-Loss: ₹{stop_loss:.2f} (EMA={sl_ema:.2f}, ATR={sl_atr:.2f}, Fixed={sl_fixed:.2f})")
        
        return stop_loss
    
    def calculate_take_profit(self, entry_price: float, stop_loss: float) -> List[float]:
        """
        Calculate take-profit targets using Support/Resistance levels
        
        Primary: Uses actual resistance levels with R:R >= 1.5 validation
        Fallback: Risk-based targets if insufficient S/R levels found
        
        Uses actual Fibonacci resistance levels instead of arbitrary risk multiples:
        - Target 1: Nearest Fibonacci resistance (61.8% or 78.6%)
        - Target 2: Swing high (100% Fibonacci level)
        - Target 3: Fibonacci extension (127.2% or 161.8%)
        
        Falls back to risk-based targets if Fibonacci levels are below entry price.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop-loss price
            
        Returns:
            List of [tp1, tp2, tp3]
        """
        risk = entry_price - stop_loss
        
        # Get S/R-based targets
        sr = SupportResistance(self.df)
        resistance_targets = sr.get_resistance_targets(
            entry_price=entry_price,
            stop_loss=stop_loss,
            min_rr=1.5,  # Minimum 1:1.5 R:R
            count=3
        )
        
        # If we have valid S/R targets, use them
        if len(resistance_targets) >= 3:
            tp1 = resistance_targets[0]['price']
            tp2 = resistance_targets[1]['price']
            tp3 = resistance_targets[2]['price']
            
            logger.info(
                f"S/R Targets: "
                f"T1=₹{tp1:.2f} (R:R {resistance_targets[0]['rr_ratio']:.1f}, {resistance_targets[0]['touches']} touches), "
                f"T2=₹{tp2:.2f} (R:R {resistance_targets[1]['rr_ratio']:.1f}, {resistance_targets[1]['touches']} touches), "
                f"T3=₹{tp3:.2f} (R:R {resistance_targets[2]['rr_ratio']:.1f}, {resistance_targets[2]['touches']} touches)"
            )
            
        elif len(resistance_targets) > 0:
            # Partial S/R + risk-based fallback
            targets = [r['price'] for r in resistance_targets]
            
            # Add risk-based targets to fill gaps
            while len(targets) < 3:
                mult = 1.5 + (len(targets) * 0.5)
                targets.append(entry_price + (risk * mult))
            
            tp1, tp2, tp3 = sorted(targets)[:3]
            logger.info(f"Mixed Targets (S/R + Risk): T1=₹{tp1:.2f}, T2=₹{tp2:.2f}, T3=₹{tp3:.2f}")
            
        else:
            # Full fallback: Risk-based targets
            tp1 = entry_price + (risk * 1.5)
            tp2 = entry_price + (risk * 2.0)
            tp3 = entry_price + (risk * 2.5)
            logger.info(f"Risk-Based Targets (no S/R found): T1=₹{tp1:.2f}, T2=₹{tp2:.2f}, T3=₹{tp3:.2f}")
        
        return [tp1, tp2, tp3]
    
    def generate_signal(self) -> Optional[Dict]:
        """
        Generate trading signal
        
        Signal generated if:
        - At least 2 strong conditions (≥60% score)
        - Composite confidence ≥ 65%
        - Minimum 50 candles available
        
        Returns:
            Signal dictionary or None
        """
        # Calculate indicators if not done
        if 'ema_8' not in self.df.columns:
            self.calculate_indicators()
        
        # Perform analysis
        analysis = self.analyze()
        
        # Check signal criteria
        if analysis['confidence'] < self.MIN_CONFIDENCE:
            logger.info(f"{self.symbol}: Confidence {analysis['confidence']:.1f}% < {self.MIN_CONFIDENCE}% threshold")
            return None
        
        if analysis['strong_conditions'] < 2:
            logger.info(f"{self.symbol}: Only {analysis['strong_conditions']} strong conditions (need ≥2)")
            return None
        
        # Calculate entry, stop-loss, and targets
        entry_price = self.get_current_price()
        stop_loss = self.calculate_stop_loss(entry_price)
        targets = self.calculate_take_profit(entry_price, stop_loss)
        
        # Format signal
        signal = self.format_signal(
            signal_type='BUY',
            confidence=analysis['confidence'],
            entry=entry_price,
            stop_loss=stop_loss,
            targets=targets,
            analysis=analysis
        )
        
        logger.info(f"✅ {self.symbol}: BUY signal generated (confidence: {analysis['confidence']:.1f}%)")
        
        return signal

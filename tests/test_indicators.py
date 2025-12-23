"""
Test script for technical indicators library

Demonstrates usage of all indicator categories
"""

import sys
import pandas as pd
from src.data.storage import OHLCVDB
from src.indicators import (
    TrendIndicators,
    MomentumIndicators,
    VolatilityIndicators,
    VolumeIndicators,
    CandlestickPatterns
)


def test_indicators():
    """Test all indicator categories"""
    
    print("=" * 80)
    print("TECHNICAL INDICATORS LIBRARY TEST")
    print("=" * 80)
    
    # Load sample data
    print("\n[1/6] Loading data...")
    db = OHLCVDB()
    df = db.get_ohlcv('RELIANCE.NS', '75m', limit=500)
    print(f"✓ Loaded {len(df)} candles for RELIANCE.NS (75m)")
    
    # Test Trend Indicators
    print("\n[2/6] Testing Trend Indicators...")
    trend = TrendIndicators(df)
    df['EMA_20'] = trend.ema(period=20)
    df['SMA_50'] = trend.sma(period=50)
    df['DEMA_20'] = trend.dema(period=20)
    adx_data = trend.adx(period=14)
    df['ADX'] = adx_data['ADX']
    print(f"✓ EMA_20: {df['EMA_20'].iloc[-1]:.2f}")
    print(f"✓ SMA_50: {df['SMA_50'].iloc[-1]:.2f}")
    print(f"✓ ADX: {df['ADX'].iloc[-1]:.2f}")
    
    # Test Momentum Indicators
    print("\n[3/6] Testing Momentum Indicators...")
    momentum = MomentumIndicators(df)
    df['RSI'] = momentum.rsi(period=14)
    macd_data = momentum.macd()
    df['MACD'] = macd_data['MACD']
    df['MACD_signal'] = macd_data['MACD_signal']
    stoch_data = momentum.stochastic()
    df['STOCH_K'] = stoch_data['STOCH_K']
    print(f"✓ RSI: {df['RSI'].iloc[-1]:.2f}")
    print(f"✓ MACD: {df['MACD'].iloc[-1]:.2f}")
    print(f"✓ Stochastic %K: {df['STOCH_K'].iloc[-1]:.2f}")
    
    # Test Volatility Indicators
    print("\n[4/6] Testing Volatility Indicators...")
    volatility = VolatilityIndicators(df)
    df['ATR'] = volatility.atr(period=14)
    bb_data = volatility.bollinger_bands(period=20)
    df['BB_upper'] = bb_data['BB_upper']
    df['BB_lower'] = bb_data['BB_lower']
    print(f"✓ ATR: {df['ATR'].iloc[-1]:.2f}")
    print(f"✓ BB Upper: {df['BB_upper'].iloc[-1]:.2f}")
    print(f"✓ BB Lower: {df['BB_lower'].iloc[-1]:.2f}")
    
    # Test Volume Indicators
    print("\n[5/6] Testing Volume Indicators...")
    volume = VolumeIndicators(df)
    df['OBV'] = volume.obv()
    df['MFI'] = volume.mfi(period=14)
    print(f"✓ OBV: {df['OBV'].iloc[-1]:.0f}")
    print(f"✓ MFI: {df['MFI'].iloc[-1]:.2f}")
    
    # Test Candlestick Patterns
    print("\n[6/6] Testing Candlestick Patterns...")
    patterns = CandlestickPatterns(df)
    df['HAMMER'] = patterns.hammer()
    df['DOJI'] = patterns.doji()
    df['ENGULFING'] = patterns.engulfing()
    
    # Find recent patterns
    recent_patterns = []
    if df['HAMMER'].iloc[-1] != 0:
        recent_patterns.append(f"Hammer ({df['HAMMER'].iloc[-1]})")
    if df['DOJI'].iloc[-1] != 0:
        recent_patterns.append(f"Doji ({df['DOJI'].iloc[-1]})")
    if df['ENGULFING'].iloc[-1] != 0:
        recent_patterns.append(f"Engulfing ({df['ENGULFING'].iloc[-1]})")
    
    if recent_patterns:
        print(f"✓ Recent patterns: {', '.join(recent_patterns)}")
    else:
        print("✓ No patterns detected in last candle")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total indicators calculated: {len([col for col in df.columns if col not in ['open', 'high', 'low', 'close', 'volume', 'time']])}")
    print(f"Data points: {len(df)}")
    print("\nLast candle indicators:")
    print(f"  Price: {df['close'].iloc[-1]:.2f}")
    print(f"  EMA(20): {df['EMA_20'].iloc[-1]:.2f}")
    print(f"  RSI(14): {df['RSI'].iloc[-1]:.2f}")
    print(f"  ATR(14): {df['ATR'].iloc[-1]:.2f}")
    print(f"  MFI(14): {df['MFI'].iloc[-1]:.2f}")
    
    # Signal example
    print("\nSimple Signal Example:")
    if df['EMA_20'].iloc[-1] > df['SMA_50'].iloc[-1] and df['RSI'].iloc[-1] < 70:
        print("  🟢 BULLISH: EMA > SMA and RSI not overbought")
    elif df['EMA_20'].iloc[-1] < df['SMA_50'].iloc[-1] and df['RSI'].iloc[-1] > 30:
        print("  🔴 BEARISH: EMA < SMA and RSI not oversold")
    else:
        print("  ⚪ NEUTRAL: No clear signal")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)


if __name__ == '__main__':
    test_indicators()

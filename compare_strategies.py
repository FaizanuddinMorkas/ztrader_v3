#!/usr/bin/env python3
"""
Compare Filtered vs Scored Fundamental Strategies

Tests both approaches with AI sentiment analysis included.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.storage import get_storage
from src.strategies.multi_indicator import MultiIndicatorStrategy
from src.strategies.multi_indicator_scored import MultiIndicatorScoredStrategy
from src.analysis.sentiment import NewsSentimentAnalyzer
from src.analysis.fundamentals import get_fundamentals

def test_strategy(strategy_class, symbols, use_filter=True):
    """Test a strategy on given symbols"""
    storage = get_storage()
    analyzer = NewsSentimentAnalyzer()
    
    signals = []
    filtered_count = 0
    
    for symbol in symbols:
        # Get data
        df = storage.get_ohlcv(symbol, timeframe='1d', limit=365)
        if df is None or len(df) < 100:
            continue
        
        # Get fundamentals
        fundamentals = get_fundamentals(symbol)
        
        # Check fundamental filter (only for filtered strategy)
        if use_filter and fundamentals:
            pe = fundamentals.get('pe_ratio')
            roe = fundamentals.get('roe')
            debt_equity = fundamentals.get('debt_equity')
            
            # Apply filter
            if pe and (pe < 5 or pe > 50):
                filtered_count += 1
                continue
            if roe and roe < 10:
                filtered_count += 1
                continue
            if debt_equity and debt_equity > 2.0:
                filtered_count += 1
                continue
        
        # Create strategy and generate signal
        strategy = strategy_class(df, symbol, timeframe='1d')
        strategy.calculate_indicators()
        signal = strategy.generate_signal(fundamentals=fundamentals)
        
        if signal and signal['confidence'] >= 65.0:
            # Add AI sentiment
            signal = analyzer.enhance_signal(signal, include_technical=True, timeframe='1d')
            signals.append(signal)
    
    return signals, filtered_count

def main():
    print("="*80)
    print("COMPARING FUNDAMENTAL STRATEGIES (WITH AI SENTIMENT)")
    print("="*80)
    print()
    
    # Test symbols
    symbols = ['SBIN.NS', 'BPCL.NS', 'TCS.NS', 'VEDL.NS', 'RELIANCE.NS', 'INFY.NS']
    
    print(f"Testing {len(symbols)} symbols")
    print()
    
    # Strategy 1: Filtered (current)
    print("-" * 80)
    print("STRATEGY 1: FILTERED FUNDAMENTALS (Current)")
    print("-" * 80)
    
    signals1, filtered1 = test_strategy(MultiIndicatorStrategy, symbols, use_filter=True)
    
    print(f"\nResults:")
    print(f"  Total symbols: {len(symbols)}")
    print(f"  Filtered out: {filtered1}")
    print(f"  Analyzed: {len(symbols) - filtered1}")
    print(f"  Signals generated: {len(signals1)}")
    
    if signals1:
        print(f"\n  Signals:")
        for sig in signals1:
            orig_conf = sig.get('original_confidence', sig['confidence'])
            final_conf = sig['confidence']
            sentiment_adj = sig.get('sentiment_adjusted', 0)
            print(f"    {sig['symbol']}: {final_conf:.1f}% (Tech: {orig_conf:.1f}%, Sentiment: {sentiment_adj:+d})")
    
    print()
    
    # Strategy 2: Scored (new)
    print("-" * 80)
    print("STRATEGY 2: SCORED FUNDAMENTALS (New)")
    print("-" * 80)
    
    signals2, filtered2 = test_strategy(MultiIndicatorScoredStrategy, symbols, use_filter=False)
    
    print(f"\nResults:")
    print(f"  Total symbols: {len(symbols)}")
    print(f"  Filtered out: {filtered2}")  # Should be 0
    print(f"  Analyzed: {len(symbols)}")
    print(f"  Signals generated: {len(signals2)}")
    
    if signals2:
        print(f"\n  Signals:")
        for sig in signals2:
            tech_conf = sig.get('technical_confidence', 0)
            fund_adj = sig.get('fundamental_adjustment', 0)
            orig_conf = sig.get('original_confidence', tech_conf + fund_adj)
            final_conf = sig['confidence']
            sentiment_adj = sig.get('sentiment_adjusted', 0)
            fund_score = sig.get('fundamental_score', 0)
            print(f"    {sig['symbol']}: {final_conf:.1f}% (Tech: {tech_conf:.1f}%, Fund: {fund_score:+d}, Sentiment: {sentiment_adj:+d})")
    
    print()
    print("="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    print(f"Filtered Strategy: {len(signals1)} signals from {len(symbols) - filtered1} stocks")
    print(f"Scored Strategy:   {len(signals2)} signals from {len(symbols)} stocks")
    print(f"Difference:        {len(signals2) - len(signals1):+d} more signals")
    print()
    
    # Show fundamental breakdown for scored strategy
    if signals2:
        print("Fundamental Score Breakdown (Scored Strategy):")
        for sig in signals2:
            if 'fundamental_breakdown' in sig:
                print(f"\n  {sig['symbol']}:")
                for metric, score in sig['fundamental_breakdown'].items():
                    print(f"    {metric}: {score}")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Test the new fundamental scoring strategy

Usage: python3 test_scored_strategy.py
"""

import sys
sys.path.insert(0, '/Users/faizanuddinmorkas/Work/Personal/ztrader_new')

from src.strategies.multi_indicator_scored import MultiIndicatorScoredStrategy
from src.data.storage import DatabaseConnection
from src.analysis.fundamentals import get_fundamentals
import pandas as pd

def main():
    print("="*80)
    print("TESTING FUNDAMENTAL SCORING STRATEGY")
    print("="*80)
    print()
    
    # Test symbols
    symbols = ['SBIN.NS', 'BPCL.NS', 'RELIANCE.NS']
    
    db = DatabaseConnection()
    
    for symbol in symbols:
        print(f"\n{'-'*80}")
        print(f"Testing: {symbol}")
        print('-'*80)
        
        # Get OHLCV data
        query = """
            SELECT timestamp, open, high, low, close, volume
            FROM ohlcv_data
            WHERE symbol = %s AND timeframe = '1d'
            ORDER BY timestamp DESC
            LIMIT 365
        """
        
        data = db.execute_query(query, (symbol,))
        if not data or len(data) < 100:
            print(f"  ❌ Insufficient data")
            continue
        
        df = pd.DataFrame(data)
        df = df.sort_values('timestamp').reset_index(drop=True)
        df.set_index('timestamp', inplace=True)
        
        # Get fundamentals
        fundamentals = get_fundamentals(symbol)
        
        # Create strategy
        strategy = MultiIndicatorScoredStrategy(df, symbol, timeframe='1d')
        strategy.calculate_indicators()
        
        # Generate signal
        signal = strategy.generate_signal(fundamentals=fundamentals)
        
        if signal:
            print(f"  ✅ Signal Generated:")
            print(f"     Type: {signal['signal_type']}")
            print(f"     Technical Confidence: {signal['technical_confidence']:.1f}%")
            print(f"     Fundamental Score: {signal['fundamental_score']:+d}")
            print(f"     Fundamental Adjustment: {signal['fundamental_adjustment']:+.1f}%")
            print(f"     Final Confidence: {signal['confidence']:.1f}%")
            print(f"     Entry: ₹{signal['entry_price']:.2f}")
            print(f"     Stop: ₹{signal['stop_loss']:.2f}")
            print(f"     Target: ₹{signal['targets'][0]:.2f}")
            print(f"     R:R: 1:{signal['risk_reward_ratio']:.1f}")
            
            if 'fundamental_breakdown' in signal:
                print(f"\n     Fundamental Breakdown:")
                for metric, score in signal['fundamental_breakdown'].items():
                    print(f"       {metric}: {score}")
        else:
            print(f"  ❌ No signal (confidence too low)")
    
    print(f"\n{'='*80}")
    print("Test complete!")
    print('='*80)

if __name__ == '__main__':
    main()

"""
Test multi-indicator strategy with real data

Tests signal generation for a few Nifty 100 stocks
"""

import sys
import logging
from src.data.storage import InstrumentsDB, OHLCVDB
from src.strategies import MultiIndicatorStrategy

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_strategy():
    """Test strategy with real data"""
    
    print("=" * 80)
    print("MULTI-INDICATOR STRATEGY TEST")
    print("=" * 80)
    
    # Get test symbols
    instruments_db = InstrumentsDB()
    ohlcv_db = OHLCVDB()
    
    symbols = instruments_db.get_nifty_100()[:10]  # Test with first 10
    print(f"\nTesting with {len(symbols)} symbols")
    print()
    
    signals = []
    
    for i, symbol in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}] Analyzing {symbol}...")
        
        try:
            # Load data (1 year of daily data)
            df = ohlcv_db.get_ohlcv(symbol, '1d', limit=365)
            
            if len(df) < 50:
                print(f"  ⚠️  Insufficient data ({len(df)} candles)")
                continue
            
            # Create strategy
            strategy = MultiIndicatorStrategy(symbol, df)
            
            # Generate signal
            signal = strategy.generate_signal()
            
            if signal:
                signals.append(signal)
                print(f"  ✅ BUY Signal!")
                print(f"     Confidence: {signal['confidence']:.1f}%")
                print(f"     Entry: ₹{signal['entry_price']}")
                print(f"     Stop Loss: ₹{signal['stop_loss']}")
                print(f"     Target: ₹{signal['target1']}")
                print(f"     Risk:Reward = 1:{signal['risk_reward_ratio']:.1f}")
            else:
                print(f"  ⚪ No signal")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Symbols analyzed: {len(symbols)}")
    print(f"Signals generated: {len(signals)}")
    
    if signals:
        print(f"\nGenerated Signals:")
        for signal in signals:
            print(f"\n{signal['symbol']}:")
            print(f"  Confidence: {signal['confidence']:.1f}%")
            print(f"  Entry: ₹{signal['entry_price']}")
            print(f"  Stop Loss: ₹{signal['stop_loss']} (Risk: ₹{signal['risk']})")
            print(f"  Target 1: ₹{signal['target1']} (Reward: ₹{signal['reward']})")
            print(f"  Risk:Reward: 1:{signal['risk_reward_ratio']:.1f}")
            
            # Show analysis details
            analysis = signal['analysis']
            print(f"  Trend: {analysis['trend']['score']:.0f}% ({analysis['trend']['conditions_met']}/5)")
            print(f"  Momentum: {analysis['momentum']['score']:.0f}% ({analysis['momentum']['conditions_met']}/3)")
            print(f"  Volatility: {analysis['volatility']['score']:.0f}% ({analysis['volatility']['conditions_met']}/3)")
    
    print("\n" + "=" * 80)
    print("✅ STRATEGY TEST COMPLETE!")
    print("=" * 80)


if __name__ == '__main__':
    test_strategy()

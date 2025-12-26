"""
Daily Signals Script

Generates and sends daily trading signals for Nifty 100 stocks

Usage:
    python daily_signals.py              # Generate signals with default settings
    python daily_signals.py --test       # Test mode (no notifications)
    python daily_signals.py --symbols RELIANCE.NS TCS.NS  # Specific symbols
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import argparse
import logging
from datetime import datetime

from src.strategies.signal_generator import SignalGenerator
from src.notifications import TelegramNotifier
from src.analysis import NewsSentimentAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_signals.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Generate daily trading signals')
    parser.add_argument('--test', action='store_true', help='Test mode (no notifications)')
    parser.add_argument('--symbols', nargs='+', help='Specific symbols to analyze')
    parser.add_argument('--no-filter', action='store_true', help='Disable fundamental filtering')
    parser.add_argument('--min-confidence', type=float, default=65.0, help='Minimum confidence (default: 65)')
    parser.add_argument('--sentiment', action='store_true', help='Enable Gemini sentiment analysis')
    parser.add_argument('--timeframe', type=str, default='1d', choices=['1d', '75m'], 
                       help='Timeframe for analysis: 1d (daily) or 75m (intraday)')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("DAILY TRADING SIGNALS")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Timeframe: {args.timeframe.upper()}")
    print(f"Mode: {'TEST' if args.test else 'LIVE'}")
    print()
    
    # Generate signals
    logger.info("Starting signal generation...")
    # Initialize signal generator with timeframe
    generator = SignalGenerator(timeframe=args.timeframe, lookback=365)
    
    signals = generator.generate_signals(
        symbols=args.symbols,
        use_fundamental_filter=not args.no_filter,
        min_confidence=args.min_confidence
    )
    
    # Sentiment analysis (optional)
    if args.sentiment and signals:
        print()
        print("=" * 80)
        print("ANALYZING NEWS SENTIMENT WITH AI")
        print("=" * 80)
        
        try:
            analyzer = NewsSentimentAnalyzer()
            signals = analyzer.batch_enhance_signals(signals)
            print(f"\n✅ Sentiment analysis complete for {len(signals)} signals")
        except ImportError:
            logger.warning("Gemini not configured. Install google-generativeai and set GEMINI_API_KEY.")
            print("\n⚠️  Gemini not configured")
            print("To enable sentiment analysis:")
            print("1. Install: pip install google-generativeai")
            print("2. Get API key: https://makersuite.google.com/app/apikey")
            print("3. Set GEMINI_API_KEY in .env")
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            print(f"\n❌ Sentiment analysis error: {e}")
    
    # Display signals
    print()
    print("=" * 80)
    print(f"SIGNALS GENERATED: {len(signals)}")
    print("=" * 80)
    
    if signals:
        for i, signal in enumerate(signals, 1):
            print(f"\n{'='*60}")
            print(f"[{i}] {signal['symbol']}")
            print(f"{'='*60}")
            
            # STRATEGY SIGNAL (Your Multi-Indicator System)
            print(f"\n📊 STRATEGY SIGNAL (Multi-Indicator):")
            print(f"    Signal Type: {signal['signal_type']}")
            
            # Show sentiment adjustment if available
            if 'sentiment' in signal:
                sentiment_emoji = "🟢" if signal['sentiment']['sentiment'] == 'bullish' else "🔴" if signal['sentiment']['sentiment'] == 'bearish' else "⚪"
                print(f"    {sentiment_emoji} News Sentiment: {signal['sentiment']['sentiment'].upper()} ({signal['sentiment']['confidence']}%)")
                print(f"    Strategy Confidence: {signal['original_confidence']:.1f}%")
                print(f"    Final Confidence: {signal['confidence']:.1f}% ({signal['sentiment_adjusted']:+d} from news)")
            else:
                print(f"    Confidence: {signal['confidence']:.1f}%")
            
            print(f"    Entry: ₹{signal['entry_price']}")
            print(f"    Stop Loss: ₹{signal['stop_loss']} (Risk: ₹{signal['risk']})")
            print(f"    Target 1: ₹{signal['target1']} (Reward: ₹{signal['reward']})")
            print(f"    Risk:Reward: 1:{signal['risk_reward_ratio']:.1f}")
            
            # AI TECHNICAL ANALYSIS (DeepSeek Analysis)
            if 'technical_analysis' in signal:
                tech = signal['technical_analysis']
                pred_emoji = "📈" if tech['prediction'] == 'bullish' else "📉" if tech['prediction'] == 'bearish' else "➡️"
                rec_emoji = "✅" if tech['recommendation'] == 'buy' else "⏸️" if tech['recommendation'] == 'hold' else "❌"
                
                print(f"\n🤖 AI TECHNICAL ANALYSIS (Gemma-3-27B):")
                print(f"    {pred_emoji} AI Prediction: {tech['prediction'].upper()} ({tech['confidence']}%)")
                print(f"    {rec_emoji} AI Recommendation: {tech['recommendation'].upper()}")
                print(f"    ⏰ Timeframe: {tech['timeframe']}")
                print(f"    💪 Signal Strength: {tech['strength'].upper()}")
                if tech.get('reasoning'):
                    print(f"    💡 AI Reasoning: {tech['reasoning']}")
                
                # Show AI-generated trade levels if available
                if tech.get('ai_entry'):
                    print(f"\n🎯 AI SUGGESTED LEVELS:")
                    print(f"    Entry: ₹{tech['ai_entry']:.2f}")
                    print(f"    Stop Loss: ₹{tech['ai_stop']:.2f} (Risk: ₹{tech['ai_entry'] - tech['ai_stop']:.2f})")
                    print(f"    Target 1: ₹{tech['ai_target1']:.2f} (Reward: ₹{tech['ai_target1'] - tech['ai_entry']:.2f})")
                    if tech.get('ai_target2'):
                        print(f"    Target 2: ₹{tech['ai_target2']:.2f} (Reward: ₹{tech['ai_target2'] - tech['ai_entry']:.2f})")
                    
                    ai_risk = tech['ai_entry'] - tech['ai_stop']
                    ai_reward = tech['ai_target1'] - tech['ai_entry']
                    ai_rr = ai_reward / ai_risk if ai_risk > 0 else 0
                    print(f"    Risk:Reward: 1:{ai_rr:.1f}")
                    
                    # Calculate hybrid setup (best of both)
                    print(f"\n💎 HYBRID SETUP (Best of Both):")
                    
                    # Use better entry (closer to support)
                    hybrid_entry = min(signal['entry_price'], tech['ai_entry'])
                    # Use tighter stop (less risk)
                    hybrid_stop = max(signal['stop_loss'], tech['ai_stop'])
                    # Use higher target (more reward)
                    hybrid_target = max(signal['target1'], tech['ai_target1'])
                    
                    hybrid_risk = hybrid_entry - hybrid_stop
                    hybrid_reward = hybrid_target - hybrid_entry
                    hybrid_rr = hybrid_reward / hybrid_risk if hybrid_risk > 0 else 0
                    
                    print(f"    Entry: ₹{hybrid_entry:.2f} ({'AI' if hybrid_entry == tech['ai_entry'] else 'Strategy'})")
                    print(f"    Stop Loss: ₹{hybrid_stop:.2f} ({'AI' if hybrid_stop == tech['ai_stop'] else 'Strategy'})")
                    print(f"    Target: ₹{hybrid_target:.2f} ({'AI' if hybrid_target == tech['ai_target1'] else 'Strategy'})")
                    print(f"    Risk: ₹{hybrid_risk:.2f} | Reward: ₹{hybrid_reward:.2f}")
                    print(f"    Risk:Reward: 1:{hybrid_rr:.1f} ⭐")
            
            # FINAL DECISION HELPER
            if 'technical_analysis' in signal:
                strategy_bullish = signal['signal_type'] == 'BUY'
                ai_bullish = tech['prediction'] == 'bullish'
                ai_recommends_buy = tech['recommendation'] == 'buy'
                
                if strategy_bullish and ai_bullish and ai_recommends_buy:
                    print(f"\n✅ STRONG CONSENSUS: Both Strategy & AI agree - BUY")
                elif strategy_bullish and ai_bullish:
                    print(f"\n⚠️  MODERATE: Strategy & AI bullish, but AI suggests {tech['recommendation'].upper()}")
                elif strategy_bullish and not ai_bullish:
                    print(f"\n⚠️  CONFLICT: Strategy says BUY, AI says {tech['prediction'].upper()}")
                    print(f"    → Proceed with caution or skip this trade")
    else:
        print("\nNo signals generated today.")
    
    # Send notifications
    if not args.test and signals:
        print()
        print("=" * 80)
        print("SENDING NOTIFICATIONS")
        print("=" * 80)
        
        try:
            notifier = TelegramNotifier()
            
            # Send individual signals
            stats = notifier.send_signals(
                signals,
                min_confidence=args.min_confidence,
                priority_threshold=90.0
            )
            
            print(f"\nTelegram notifications:")
            print(f"  Sent: {stats['sent']}")
            print(f"  Priority: {stats['priority_sent']}")
            print(f"  Failed: {stats['failed']}")
            
            # Send summary
            notifier.send_summary(signals)
            
        except ImportError:
            logger.warning("Telegram not configured. Install python-telegram-bot and set environment variables.")
            print("\n⚠️  Telegram not configured")
            print("To enable notifications:")
            print("1. Install: pip install python-telegram-bot")
            print("2. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
        
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
            print(f"\n❌ Error sending notifications: {e}")
    
    print()
    print("=" * 80)
    print("✅ DAILY SIGNALS COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()

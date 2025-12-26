"""
Daily Signals Script

Generates and sends daily trading signals for Nifty 100 stocks

Usage:
    python daily_signals.py              # Generate signals with default settings
    python daily_signals.py --test       # Test mode (no notifications)
    python daily_signals.py --symbols RELIANCE.NS TCS.NS  # Specific symbols
"""

import sys
import argparse
import logging
import asyncio
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.strategies.signal_generator_scored import SignalGeneratorScored
from src.notifications.telegram import TelegramNotifier
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


def escape_markdown(text: str) -> str:
    """Escape special markdown characters for Telegram"""
    # Only escape the most critical markdown characters that cause parsing issues
    # Don't escape . and ! as they're common in text
    text = text.replace('*', '\\*')  # Asterisk for bold/italic
    text = text.replace('_', '\\_')  # Underscore for italic
    text = text.replace('[', '\\[')  # Square brackets for links
    text = text.replace('`', '\\`')  # Backticks for code
    return text


def format_telegram_message(signal: dict) -> str:
    """
    Format signal for Telegram with complete details
    
    Args:
        signal: Signal dictionary with all analysis data
        
    Returns:
        Formatted markdown message
    """
    confidence_emoji = "🟢" if signal['confidence'] > 90 else "🟡" if signal['confidence'] >= 75 else "⚪"
    
    # Start with basic signal info
    lines = [
        f"{confidence_emoji} *{signal['symbol']} - BUY SIGNAL*",
        ""
    ]
    
    # Sentiment if available
    if 'sentiment' in signal:
        sent = signal['sentiment']
        sent_emoji = "🟢" if sent['sentiment'] == 'bullish' else "🔴" if sent['sentiment'] == 'bearish' else "⚪"
        lines.extend([
            f"{sent_emoji} *News Sentiment:* {sent['sentiment'].upper()} ({sent['confidence']}%)",
            f"*Strategy Confidence:* {signal.get('original_confidence', signal['confidence']):.1f}%",
            f"*Final Confidence:* {signal['confidence']:.1f}% ({signal.get('sentiment_adjusted', 0):+d} from news)",
        ])
    else:
        lines.append(f"*Confidence:* {signal['confidence']:.1f}%")
    
    lines.extend([
        "",
        "*📊 STRATEGY SIGNAL:*",
        f"💰 Entry: ₹{signal['entry_price']:.2f}",
        f"🛑 Stop Loss: ₹{signal['stop_loss']:.2f} (Risk: ₹{signal['risk']:.2f})",
        f"🎯 Target 1: ₹{signal['target1']:.2f} (Reward: ₹{signal['reward']:.2f})",
        f"📊 Risk:Reward: 1:{signal['risk_reward_ratio']:.1f}",
    ])
    
    # AI Technical Analysis if available
    if 'technical_analysis' in signal:
        tech = signal['technical_analysis']
        pred_emoji = "📈" if tech['prediction'] == 'bullish' else "📉" if tech['prediction'] == 'bearish' else "➡️"
        rec_emoji = "✅" if tech['recommendation'] == 'buy' else "⏸️" if tech['recommendation'] == 'hold' else "❌"
        
        lines.extend([
            "",
            "*🤖 AI ANALYSIS (Gemma-3-27B):*",
            f"{pred_emoji} Prediction: {tech['prediction'].upper()} ({tech['confidence']}%)",
            f"{rec_emoji} Recommendation: {tech['recommendation'].upper()}",
            f"⏰ Timeframe: {tech['timeframe']}",
            f"💪 Strength: {tech['strength'].upper()}",
        ])
        
        # Key Factors
        if tech.get('key_factors'):
            factors = tech['key_factors']
            if isinstance(factors, list):
                factors_text = ", ".join(factors)
            else:
                factors_text = str(factors)
            lines.append(f"🔑 Key Factors: {factors_text}")
        
        # AI Suggested Levels
        if tech.get('ai_entry'):
            lines.extend([
                "",
                "*🎯 AI SUGGESTED LEVELS:*",
                f"Entry: ₹{tech['ai_entry']:.2f}",
                f"Stop: ₹{tech['ai_stop']:.2f}",
                f"Target 1: ₹{tech['ai_target1']:.2f}",
            ])
            
            if tech.get('ai_target2'):
                lines.append(f"Target 2: ₹{tech['ai_target2']:.2f}")
            
            # Calculate AI R:R
            ai_risk = tech['ai_entry'] - tech['ai_stop']
            ai_reward = tech['ai_target1'] - tech['ai_entry']
            ai_rr = ai_reward / ai_risk if ai_risk > 0 else 0
            lines.append(f"R:R: 1:{ai_rr:.1f}")
            
            # Hybrid Setup
            hybrid_entry = min(signal['entry_price'], tech['ai_entry'])
            hybrid_stop = max(signal['stop_loss'], tech['ai_stop'])
            hybrid_target = max(signal['target1'], tech['ai_target1'])
            hybrid_risk = hybrid_entry - hybrid_stop
            hybrid_reward = hybrid_target - hybrid_entry
            hybrid_rr = hybrid_reward / hybrid_risk if hybrid_risk > 0 else 0
            
            lines.extend([
                "",
                "*💎 HYBRID SETUP (Best of Both):*",
                f"Entry: ₹{hybrid_entry:.2f}",
                f"Stop: ₹{hybrid_stop:.2f}",
                f"Target: ₹{hybrid_target:.2f}",
                f"R:R: 1:{hybrid_rr:.1f} ⭐",
            ])
        
        # AI Reasoning (AI keeps it within 1200-1500 chars as per prompt)
        if tech.get('reasoning'):
            # Escape markdown characters in reasoning to avoid telegram parsing errors
            escaped_reasoning = escape_markdown(tech['reasoning'])
            
            lines.extend([
                "",
                "*📝 AI REASONING:*",
                escaped_reasoning
            ])
        
        # Consensus
        strategy_bullish = signal['signal_type'] == 'BUY'
        ai_bullish = tech['prediction'] == 'bullish'
        ai_recommends_buy = tech['recommendation'] == 'buy'
        
        lines.append("")
        if strategy_bullish and ai_bullish and ai_recommends_buy:
            lines.append("✅ *STRONG CONSENSUS:* Both Strategy & AI agree - BUY")
        elif strategy_bullish and ai_bullish:
            lines.append(f"⚠️ *MODERATE:* Both bullish, AI suggests {tech['recommendation'].upper()}")
        elif strategy_bullish and not ai_bullish:
            lines.append(f"⚠️ *CONFLICT:* Strategy BUY, AI {tech['prediction'].upper()}")
    
    lines.extend([
        "",
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ])
    
    return "\n".join(lines)


def format_summary_message(signals: list) -> str:
    """Format summary message for Telegram"""
    if not signals:
        return f"""📊 *Daily Signal Summary*
Date: {datetime.now().strftime('%Y-%m-%d')}

No signals generated today."""
    
    high_conf = sum(1 for s in signals if s['confidence'] > 90)
    med_conf = sum(1 for s in signals if 75 <= s['confidence'] <= 90)
    low_conf = sum(1 for s in signals if s['confidence'] < 75)
    
    symbols = ', '.join([s['symbol'] for s in signals[:5]])
    if len(signals) > 5:
        symbols += f" +{len(signals)-5} more"
    
    return f"""📊 *Daily Signal Summary*
Date: {datetime.now().strftime('%Y-%m-%d')}

Total Signals: *{len(signals)}*
🟢 High Confidence (>90%): {high_conf}
🟡 Medium Confidence (75-90%): {med_conf}
⚪ Low Confidence (<75%): {low_conf}

Symbols: {symbols}"""


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Generate daily trading signals')
    parser.add_argument('--test', action='store_true', help='Test mode (no notifications)')
    parser.add_argument('--no-notify', action='store_true', help='Disable Telegram notifications')
    parser.add_argument('--symbols', nargs='+', help='Specific symbols to analyze')
    parser.add_argument('--test-symbol', type=str, help='Test with single symbol (e.g., RELIANCE.NS)')
    parser.add_argument('--no-filter', action='store_true', help='Disable fundamental filtering')
    parser.add_argument('--min-confidence', type=float, default=65.0, help='Minimum confidence (default: 65)')
    parser.add_argument('--sentiment', action='store_true', help='Enable Gemini sentiment analysis')
    parser.add_argument('--timeframe', type=str, default='1d', choices=['1d', '75m'], 
                       help='Timeframe for analysis: 1d (daily) or 75m (intraday)')
    
    args = parser.parse_args()
    
    # Handle test-symbol as alias for symbols
    if args.test_symbol:
        args.symbols = [args.test_symbol]
    
    print("=" * 80)
    print("DAILY TRADING SIGNALS (SCORED FUNDAMENTALS)")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Timeframe: {args.timeframe.upper()}")
    print(f"Mode: {'TEST' if args.test else 'LIVE'}")
    print()
    
    # Initialize components
    logger.info("Starting signal generation...")
    generator = SignalGeneratorScored(timeframe=args.timeframe, lookback=365)
    
    # Get symbols to analyze
    if args.symbols is None:
        from src.data.storage import InstrumentsDB
        instruments_db = InstrumentsDB()
        symbols = instruments_db.get_nifty_100()
    else:
        symbols = args.symbols
    
    print(f"Analyzing {len(symbols)} symbols...")
    print()
    
    # Initialize AI analyzer if sentiment is enabled
    analyzer = None
    if args.sentiment:
        try:
            analyzer = NewsSentimentAnalyzer(compact_mode=True)
            print("✅ AI sentiment analysis enabled")
        except ImportError:
            logger.warning("AI not available")
            print("⚠️  AI sentiment analysis not available")
            analyzer = None
    
    # Initialize Telegram notifier if notifications enabled
    notifier = None
    if not args.test and not args.no_notify:
        try:
            notifier = TelegramNotifier(broadcast_to_users=True)
            print("✅ Telegram notifications enabled (broadcast mode)")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram: {e}")
            print(f"⚠️  Telegram not available: {e}")
            notifier = None
    
    print()
    print("=" * 80)
    print("STREAMING SIGNAL GENERATION")
    print("=" * 80)
    print()
    
    # Track statistics
    total_signals = 0
    sent_signals = 0
    
    # STREAMING APPROACH: Process one symbol at a time
    for i, symbol in enumerate(symbols, 1):
        try:
            print(f"[{i}/{len(symbols)}] Analyzing {symbol}...")
            
            # Step 1: Generate signal for this symbol
            signals = generator.generate_signals(
                symbols=[symbol],
                use_fundamental_filter=False,
                min_confidence=args.min_confidence
            )
            
            if not signals:
                print(f"  ↳ No signal (confidence < {args.min_confidence}%)")
                continue
            
            signal = signals[0]
            total_signals += 1
            print(f"  ✅ Signal generated (confidence: {signal['confidence']:.1f}%)")
            
            # Step 2: Enhance with AI if enabled
            if analyzer:
                print(f"  🤖 Running AI analysis...")
                try:
                    enhanced = analyzer.batch_enhance_signals([signal])
                    if enhanced:
                        signal = enhanced[0]
                        print(f"  ✅ AI analysis complete")
                except Exception as e:
                    logger.error(f"AI analysis failed for {symbol}: {e}")
                    print(f"  ⚠️  AI analysis failed, using base signal")
            
            # Step 3: Send to Telegram immediately
            if notifier:
                print(f"  📤 Sending to Telegram...")
                try:
                    message = format_telegram_message(signal)
                    priority = signal['confidence'] > 90.0
                    
                    async def send_signal():
                        return await notifier.send_message(message, priority=priority)
                    
                    success = asyncio.run(send_signal())
                    if success:
                        sent_signals += 1
                        print(f"  ✅ Sent to users")
                    else:
                        print(f"  ❌ Failed to send")
                except Exception as e:
                    logger.error(f"Failed to send {symbol}: {e}")
                    print(f"  ❌ Send failed: {e}")
            
            # Display signal details
            print(f"  📊 Entry: ₹{signal['entry_price']:.2f}, Stop: ₹{signal['stop_loss']:.2f}, Target: ₹{signal['target1']:.2f}")
            print()
            
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
            print(f"  ❌ Error: {e}")
            print()
    
    # Send summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Symbols analyzed: {len(symbols)}")
    print(f"Signals generated: {total_signals}")
    print(f"Signals sent: {sent_signals}")
    
    if notifier and total_signals > 0:
        print()
        print("Sending summary message...")
        try:
            summary = format_summary_message([])  # We don't have all signals in memory anymore
            summary = f"""📊 *Daily Signal Summary*
Date: {datetime.now().strftime('%Y-%m-%d')}

Total Signals: *{total_signals}*
Successfully Sent: {sent_signals}

Signals were sent individually as they were generated."""
            
            async def send_summary_msg():
                return await notifier.send_summary(summary)
            
            asyncio.run(send_summary_msg())
            print("✅ Summary sent")
        except Exception as e:
            logger.error(f"Failed to send summary: {e}")
            print(f"❌ Summary failed: {e}")
    
    print()
    print("=" * 80)
    print("✅ DAILY SIGNALS COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()

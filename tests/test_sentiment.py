"""
Test news sentiment analysis for specific symbols

Checks which symbols have recent news and analyzes sentiment
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.analysis import NewsSentimentAnalyzer

def test_news_sentiment(symbols):
    """Test sentiment analysis for given symbols"""
    
    print("=" * 80)
    print("NEWS SENTIMENT ANALYSIS TEST")
    print("=" * 80)
    
    analyzer = NewsSentimentAnalyzer()
    
    for i, symbol in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] {symbol}")
        print("-" * 80)
        
        # Fetch news
        news = analyzer.fetch_news(symbol, days=7)
        
        if news:
            print(f"Found {len(news)} recent articles:")
            for j, article in enumerate(news[:3], 1):
                print(f"  {j}. {article['title']}")
                print(f"     ({article['publisher']} - {article['published'].strftime('%Y-%m-%d')})")
            
            # Analyze sentiment
            print("\nAnalyzing sentiment with Gemini AI...")
            sentiment = analyzer.analyze_sentiment(symbol, news)
            
            sentiment_emoji = "🟢" if sentiment['sentiment'] == 'bullish' else "🔴" if sentiment['sentiment'] == 'bearish' else "⚪"
            print(f"\n{sentiment_emoji} Sentiment: {sentiment['sentiment'].upper()}")
            print(f"Confidence: {sentiment['confidence']}%")
            print(f"Impact: {sentiment['impact']:+d} points")
            print(f"Summary: {sentiment['summary']}")
        else:
            print("⚪ No recent news found")
    
    print("\n" + "=" * 80)
    print("✅ SENTIMENT ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    # Test with major stocks that usually have news
    test_symbols = [
        'RELIANCE.NS',   # Reliance Industries
        'TCS.NS',        # TCS
        'INFY.NS',       # Infosys
        'HDFCBANK.NS',   # HDFC Bank
        'ICICIBANK.NS',  # ICICI Bank
        'SBIN.NS',       # State Bank
        'BHARTIARTL.NS', # Airtel
        'ITC.NS',        # ITC
    ]
    
    # Use command line args if provided
    if len(sys.argv) > 1:
        test_symbols = sys.argv[1:]
    
    test_news_sentiment(test_symbols)

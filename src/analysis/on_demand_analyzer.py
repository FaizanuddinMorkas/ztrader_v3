"""
On-Demand Stock Analysis Module

Provides comprehensive AI-powered analysis for individual stocks on-demand.
Reuses existing sentiment analysis and AI integration infrastructure.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import yfinance as yf
import pandas as pd
from pathlib import Path

from src.analysis.sentiment import NewsSentimentAnalyzer
from src.data.fundamentals import FundamentalsDownloader
from src.strategies.multi_indicator_scored import MultiIndicatorScoredStrategy

logger = logging.getLogger(__name__)


class OnDemandAnalyzer:
    """
    Provides on-demand AI analysis for any stock symbol
    """
    
    def __init__(self):
        """Initialize the analyzer with required components"""
        self.sentiment_analyzer = NewsSentimentAnalyzer()
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = int(os.getenv('INTERACTIVE_BOT_CACHE_TTL', '3600'))
        self.news_days = int(os.getenv('INTERACTIVE_BOT_NEWS_DAYS', '7'))
        self.data_period = os.getenv('INTERACTIVE_BOT_DATA_PERIOD', '2y')
        self.analysis_timeout = int(os.getenv('INTERACTIVE_BOT_ANALYSIS_TIMEOUT', '60'))
        
        logger.info(f"OnDemandAnalyzer initialized (cache_ttl={self.cache_ttl}s, news_days={self.news_days})")
    
    def analyze_symbol(self, symbol: str) -> Dict:
        """
        Complete analysis pipeline for a single symbol
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            
        Returns:
            Dictionary containing complete analysis:
            {
                'symbol': str,
                'current_price': float,
                'price_change': float,
                'technical_analysis': {...},
                'fundamental_analysis': {...},
                'news_sentiment': {...},
                'ai_recommendation': {...},
                'risk_factors': list,
                'key_insights': list,
                'timestamp': datetime
            }
        """
        logger.info(f"Starting analysis for {symbol}")
        
        # Check cache first
        cache_key = f"{symbol}_{datetime.now().strftime('%Y%m%d%H')}"
        if cache_key in self.cache:
            cache_time = self.cache[cache_key]['timestamp']
            if (datetime.now() - cache_time).seconds < self.cache_ttl:
                logger.info(f"Returning cached analysis for {symbol}")
                return self.cache[cache_key]['data']
        
        try:
            # Step 1: Download OHLCV data
            logger.info(f"Downloading {self.data_period} OHLCV data for {symbol}")
            ohlcv_data = self._download_ohlcv(symbol, period=self.data_period)
            
            if ohlcv_data is None or len(ohlcv_data) < 50:
                raise ValueError(f"Insufficient data for {symbol}")
            
            # Step 2: Get fundamentals
            logger.info(f"Fetching fundamentals for {symbol}")
            fundamentals = self._get_fundamentals(symbol)
            
            # Step 3: Analyze news sentiment
            logger.info(f"Analyzing news sentiment for {symbol} (last {self.news_days} days)")
            sentiment = self._analyze_news_sentiment(symbol, days=self.news_days)
            
            # Step 4: Get AI technical analysis
            logger.info(f"Running AI analysis for {symbol}")
            ai_analysis = self._get_ai_analysis(symbol, ohlcv_data, fundamentals, sentiment)
            
            # Step 5: Generate technical indicators
            logger.info(f"Calculating technical indicators for {symbol}")
            technical = self._calculate_technical_analysis(ohlcv_data)
            
            # Step 6: Compile complete analysis
            current_price = float(ohlcv_data['Close'].iloc[-1])
            prev_close = float(ohlcv_data['Close'].iloc[-2])
            price_change = ((current_price - prev_close) / prev_close) * 100
            
            analysis = {
                'symbol': symbol,
                'current_price': current_price,
                'price_change': price_change,
                'technical_analysis': technical,
                'fundamental_analysis': fundamentals,
                'news_sentiment': sentiment,
                'ai_recommendation': ai_analysis,
                'risk_factors': self._identify_risk_factors(fundamentals, technical, sentiment),
                'key_insights': self._generate_key_insights(technical, fundamentals, sentiment, ai_analysis),
                'timestamp': datetime.now()
            }
            
            # Cache the result
            self.cache[cache_key] = {
                'data': analysis,
                'timestamp': datetime.now()
            }
            
            logger.info(f"Analysis completed for {symbol}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            raise
    
    def _download_ohlcv(self, symbol: str, period: str = '2y') -> Optional[pd.DataFrame]:
        """
        Download historical OHLCV data using yfinance
        
        Args:
            symbol: Stock symbol
            period: Data period (e.g., '1y', '2y', '5y')
            
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data.empty:
                logger.warning(f"No data returned for {symbol}")
                return None
            
            logger.info(f"Downloaded {len(data)} candles for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error downloading data for {symbol}: {e}")
            return None
    
    def _get_fundamentals(self, symbol: str) -> Dict:
        """
        Fetch fundamental data using yfinance
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with fundamental metrics
        """
        try:
            downloader = FundamentalsDownloader()
            fundamentals = downloader.download_fundamentals(symbol)
            
            if not fundamentals:
                logger.warning(f"No fundamentals available for {symbol}")
                return {}
            
            # Simplify field names for report
            simplified = {
                'pe_ratio': fundamentals.get('trailing_pe', 0),
                'market_cap': fundamentals.get('market_cap', 0),
                'debt_equity': fundamentals.get('debt_to_equity', 0),
                'roe': fundamentals.get('return_on_equity', 0) * 100 if fundamentals.get('return_on_equity') else 0,
                'dividend_yield': fundamentals.get('dividend_yield', 0) * 100 if fundamentals.get('dividend_yield') else 0,
            }
            
            # Calculate fundamental score (0-100)
            score = self._calculate_fundamental_score(simplified)
            simplified['score'] = score
            
            return simplified
            
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {e}")
            return {}
    
    def _analyze_news_sentiment(self, symbol: str, days: int = 7) -> Dict:
        """
        Analyze recent news sentiment
        
        Args:
            symbol: Stock symbol
            days: Number of days to look back
            
        Returns:
            Dictionary with sentiment analysis
        """
        try:
            # Use get_news_sentiment which fetches news and analyzes it
            result = self.sentiment_analyzer.get_news_sentiment(symbol, timeframe='1d')
            
            if not result:
                return {
                    'sentiment': 'neutral',
                    'confidence': 0,
                    'impact': 0,
                    'article_count': 0,
                    'topics': []
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment for {symbol}: {e}")
            return {
                'sentiment': 'neutral',
                'confidence': 0,
                'impact': 0,
                'article_count': 0,
                'topics': []
            }
    
    def _get_ai_analysis(self, symbol: str, ohlcv: pd.DataFrame, 
                         fundamentals: Dict, sentiment: Dict) -> Dict:
        """
        Get comprehensive AI analysis using existing infrastructure
        
        Args:
            symbol: Stock symbol
            ohlcv: OHLCV DataFrame
            fundamentals: Fundamental metrics
            sentiment: Sentiment analysis results
            
        Returns:
            Dictionary with AI recommendation
        """
        try:
            # Ensure sentiment is a dict
            if not isinstance(sentiment, dict):
                sentiment = {
                    'sentiment': 'neutral',
                    'confidence': 0,
                    'impact': 0
                }
            
            # Convert OHLCV DataFrame to list format expected by analyzer
            ohlcv_data = []
            for idx, row in ohlcv.iterrows():
                ohlcv_data.append({
                    'date': idx.strftime('%Y-%m-%d'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                })
            
            # Create a signal dict for analyze_technical_indicators
            signal = {
                'symbol': symbol,
                'entry_price': float(ohlcv['Close'].iloc[-1]),
                'sentiment': sentiment,
                'ohlcv_data': ohlcv_data,
                'fundamentals': {
                    'trailing_pe': fundamentals.get('pe_ratio', 0),
                    'price_to_book': fundamentals.get('pb_ratio', 0),
                    'return_on_equity': fundamentals.get('roe', 0) / 100 if fundamentals.get('roe') else 0,
                    'debt_to_equity': fundamentals.get('debt_equity', 0),
                    'market_cap': fundamentals.get('market_cap', 0) / 1e7  # Convert to Crores
                },
                'analysis': {}  # Empty for now
            }
            
            # Use analyze_technical_indicators for AI analysis
            ai_result = self.sentiment_analyzer.analyze_technical_indicators(symbol, signal)
            
            if not ai_result or not isinstance(ai_result, dict):
                return self._get_default_ai_result('Insufficient data for AI analysis')
            
            # Extract relevant fields - map from parser output
            return {
                'recommendation': ai_result.get('recommendation', 'hold').upper(),
                'confidence': ai_result.get('confidence', 50),
                'entry': ai_result.get('ai_entry'),
                'stop_loss': ai_result.get('ai_stop'),
                'target1': ai_result.get('ai_target1'),
                'target2': ai_result.get('ai_target2'),
                'timeframe': ai_result.get('timeframe', 'N/A'),
                'strength': ai_result.get('strength', 'moderate'),
                'reasoning': ai_result.get('reasoning', 'AI analysis completed')
            }
            
        except Exception as e:
            logger.error(f"Error in AI analysis for {symbol}: {e}", exc_info=True)
            return self._get_default_ai_result(f'Error: {str(e)}')
    
    def _get_default_ai_result(self, reason: str) -> Dict:
        """Return default AI result"""
        return {
            'recommendation': 'N/A',
            'confidence': 0,
            'entry': None,
            'stop_loss': None,
            'target1': None,
            'target2': None,
            'timeframe': 'N/A',
            'strength': 'unknown',
            'reasoning': reason
        }
    
    def _calculate_technical_analysis(self, ohlcv: pd.DataFrame) -> Dict:
        """
        Calculate technical indicators
        
        Args:
            ohlcv: OHLCV DataFrame
            
        Returns:
            Dictionary with technical analysis
        """
        try:
            import talib
            import numpy as np
            
            # Convert to numpy arrays with correct dtype
            close = np.array(ohlcv['Close'].values, dtype=np.float64)
            high = np.array(ohlcv['High'].values, dtype=np.float64)
            low = np.array(ohlcv['Low'].values, dtype=np.float64)
            volume = np.array(ohlcv['Volume'].values, dtype=np.float64)
            
            # Calculate indicators
            rsi = talib.RSI(close, timeperiod=14)
            macd, signal, hist = talib.MACD(close)
            
            # Determine trend
            ema20 = talib.EMA(close, timeperiod=20)
            ema50 = talib.EMA(close, timeperiod=50)
            
            current_price = close[-1]
            trend = 'Bullish' if ema20[-1] > ema50[-1] else 'Bearish'
            
            # Support and resistance (simple pivot points)
            pivot = (high[-1] + low[-1] + close[-1]) / 3
            support = 2 * pivot - high[-1]
            resistance = 2 * pivot - low[-1]
            
            # RSI signal
            rsi_current = rsi[-1]
            if rsi_current > 70:
                rsi_signal = 'Overbought'
            elif rsi_current < 30:
                rsi_signal = 'Oversold'
            else:
                rsi_signal = 'Neutral'
            
            # MACD signal
            macd_signal = 'Bullish' if macd[-1] > signal[-1] else 'Bearish'
            
            # Volume trend
            vol_ma = talib.SMA(volume, timeperiod=20)
            volume_trend = 'Increasing' if volume[-1] > vol_ma[-1] else 'Decreasing'
            
            return {
                'trend': trend,
                'support': round(float(support), 2),
                'resistance': round(float(resistance), 2),
                'rsi': round(float(rsi_current), 2),
                'rsi_signal': rsi_signal,
                'macd_signal': macd_signal,
                'volume_trend': volume_trend
            }
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return {
                'trend': 'Unknown',
                'support': 0,
                'resistance': 0,
                'rsi': 50,
                'rsi_signal': 'Neutral',
                'macd_signal': 'Neutral',
                'volume_trend': 'Unknown'
            }
    
    def _calculate_fundamental_score(self, fundamentals: Dict) -> int:
        """Calculate fundamental score (0-100)"""
        score = 50  # Base score
        
        # P/E ratio (lower is better, up to 25)
        pe = fundamentals.get('pe_ratio', 0)
        if 0 < pe < 15:
            score += 15
        elif 15 <= pe < 25:
            score += 10
        elif 25 <= pe < 35:
            score += 5
        
        # ROE (higher is better)
        roe = fundamentals.get('roe', 0)
        if roe > 20:
            score += 15
        elif roe > 15:
            score += 10
        elif roe > 10:
            score += 5
        
        # Debt/Equity (lower is better)
        de = fundamentals.get('debt_equity', 0)
        if 0 <= de < 0.5:
            score += 10
        elif 0.5 <= de < 1.0:
            score += 5
        
        # Dividend yield
        div_yield = fundamentals.get('dividend_yield', 0)
        if div_yield > 2:
            score += 10
        elif div_yield > 1:
            score += 5
        
        return min(100, max(0, score))
    
    def _identify_risk_factors(self, fundamentals: Dict, technical: Dict, sentiment: Dict) -> list:
        """Identify potential risk factors"""
        risks = []
        
        # Fundamental risks
        pe = fundamentals.get('pe_ratio', 0)
        if pe > 40:
            risks.append(f"High P/E ratio ({pe:.1f}) suggests potential overvaluation")
        
        de = fundamentals.get('debt_equity', 0)
        if de > 2:
            risks.append(f"High debt/equity ratio ({de:.2f}) indicates financial leverage risk")
        
        # Technical risks
        rsi = technical.get('rsi', 50)
        if rsi > 75:
            risks.append("RSI indicates overbought conditions")
        elif rsi < 25:
            risks.append("RSI indicates oversold conditions")
        
        # Sentiment risks
        if sentiment.get('sentiment') == 'bearish':
            risks.append("Negative news sentiment may impact short-term performance")
        
        if not risks:
            risks.append("No significant risk factors identified")
        
        return risks
    
    def _generate_key_insights(self, technical: Dict, fundamentals: Dict, 
                               sentiment: Dict, ai_analysis: Dict) -> list:
        """Generate key insights from analysis"""
        insights = []
        
        # Technical insights
        if technical['trend'] == 'Bullish' and technical['rsi'] < 70:
            insights.append("Strong bullish trend with room for upside")
        
        if technical['macd_signal'] == 'Bullish' and technical['volume_trend'] == 'Increasing':
            insights.append("Bullish MACD crossover confirmed by volume")
        
        # Fundamental insights
        score = fundamentals.get('score', 50)
        if score > 75:
            insights.append("Strong fundamental metrics support long-term value")
        
        # Sentiment insights
        if sentiment.get('sentiment') == 'bullish' and sentiment.get('confidence', 0) > 75:
            insights.append("Highly positive news sentiment provides tailwind")
        
        # AI insights
        if ai_analysis.get('confidence', 0) > 80:
            insights.append(f"AI analysis shows high confidence {ai_analysis.get('recommendation')} signal")
        
        if not insights:
            insights.append("Mixed signals suggest cautious approach")
        
        return insights
    
    def _escape_markdown(self, text: str) -> str:
        """Escape special markdown characters"""
        if text is None:
            return 'N/A'
        text = str(text)
        # Escape markdown special characters
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    def format_summary(self, analysis: Dict) -> str:
        """
        Format quick summary for immediate viewing
        
        Args:
            analysis: Complete analysis dictionary
            
        Returns:
            Concise summary message
        """
        symbol = analysis['symbol']
        price = analysis['current_price']
        change = analysis['price_change']
        change_emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
        
        tech = analysis['technical_analysis']
        fund = analysis['fundamental_analysis']
        sent = analysis['news_sentiment']
        ai = analysis['ai_recommendation']
        
        msg = f"📊 *QUICK SUMMARY - {symbol}*\n\n"
        msg += f"*Price*: ₹{price:,.2f} ({change_emoji}{change:+.2f}%)\n"
        msg += f"*Date*: {analysis['timestamp'].strftime('%Y-%m-%d %H:%M')}\n\n"
        
        msg += f"🤖 *AI Recommendation*: {ai.get('recommendation', 'HOLD')} ({ai.get('confidence', 50)}%)\n"
        msg += f"📈 *Trend*: {tech['trend']}\n"
        msg += f"📰 *Sentiment*: {sent.get('sentiment', 'neutral').title()} ({sent.get('confidence', 50)}%)\n"
        msg += f"💼 *Fundamental Score*: {fund.get('score', 50)}/100\n\n"
        
        msg += "⏳ _Sending detailed analysis..._"
        
        return msg
    
    def format_detailed_sections(self, analysis: Dict) -> list:
        """
        Format detailed analysis split into logical sections
        
        Args:
            analysis: Complete analysis dictionary
            
        Returns:
            List of message sections
        """
        sections = []
        
        symbol = analysis['symbol']
        tech = analysis['technical_analysis']
        fund = analysis['fundamental_analysis']
        sent = analysis['news_sentiment']
        ai = analysis['ai_recommendation']
        
        # Section 1: Technical Analysis
        msg1 = f"📈 *TECHNICAL ANALYSIS - {symbol}*\n\n"
        msg1 += f"*Trend*: {tech['trend']}\n"
        msg1 += f"*Support*: ₹{tech['support']:,.2f}\n"
        msg1 += f"*Resistance*: ₹{tech['resistance']:,.2f}\n"
        msg1 += f"*RSI*: {tech['rsi']} ({tech['rsi_signal']})\n"
        msg1 += f"*MACD*: {tech['macd_signal']}\n"
        msg1 += f"*Volume*: {tech['volume_trend']}"
        sections.append(msg1)
        
        # Section 2: Fundamental Analysis
        msg2 = f"💼 *FUNDAMENTAL ANALYSIS - {symbol}*\n\n"
        pe = fund.get('pe_ratio', 0)
        msg2 += f"*P/E Ratio*: {f'{pe:.2f}' if pe else 'N/A'}\n"
        msg2 += f"*Market Cap*: ₹{fund.get('market_cap', 0)/1e12:.2f}T\n"
        de = fund.get('debt_equity', 0)
        msg2 += f"*Debt/Equity*: {f'{de:.2f}' if de else 'N/A'}\n"
        roe = fund.get('roe', 0)
        msg2 += f"*ROE*: {f'{roe:.2f}' if roe else 'N/A'}%\n"
        dy = fund.get('dividend_yield', 0)
        msg2 += f"*Dividend Yield*: {f'{dy:.2f}' if dy else 'N/A'}%\n"
        msg2 += f"*Overall Score*: {fund.get('score', 50)}/100"
        sections.append(msg2)
        
        # Section 3: News Sentiment
        msg3 = f"📰 *NEWS SENTIMENT - {symbol}*\n\n"
        msg3 += f"*Period*: Last 7 Days\n"
        msg3 += f"*Sentiment*: {sent.get('sentiment', 'neutral').title()}\n"
        msg3 += f"*Confidence*: {sent.get('confidence', 50)}%\n"
        msg3 += f"*Articles Analyzed*: {sent.get('article_count', 0)}\n"
        msg3 += f"*Market Impact*: {sent.get('impact', 0):+d}"
        sections.append(msg3)
        
        # Section 4: AI Recommendation (can be long)
        msg4 = f"🤖 *AI RECOMMENDATION - {symbol}*\n\n"
        msg4 += f"*Action*: {ai.get('recommendation', 'HOLD')}\n"
        msg4 += f"*Confidence*: {ai.get('confidence', 50)}%\n"
        msg4 += f"*Strength*: {ai.get('strength', 'moderate').title()}\n"
        msg4 += f"*Timeframe*: {ai.get('timeframe', 'N/A')}\n\n"
        
        # Trade levels if available
        entry = ai.get('entry')
        stop_loss = ai.get('stop_loss')
        target1 = ai.get('target1')
        target2 = ai.get('target2')
        
        if entry is not None and stop_loss is not None and target1 is not None:
            msg4 += "*Trade Levels:*\n"
            msg4 += f"• Entry: ₹{entry:,.2f}\n"
            msg4 += f"• Stop Loss: ₹{stop_loss:,.2f}\n"
            msg4 += f"• Target 1: ₹{target1:,.2f}\n"
            if target2 is not None:
                msg4 += f"• Target 2: ₹{target2:,.2f}\n"
            msg4 += "\n"
        
        # Full AI reasoning
        reasoning = ai.get('reasoning', 'N/A')
        msg4 += f"*AI Reasoning:*\n{reasoning}"
        sections.append(msg4)
        
        # Section 5: Risk & Insights
        msg5 = f"⚠️ *RISK FACTORS & INSIGHTS - {symbol}*\n\n"
        msg5 += "*Risk Factors:*\n"
        for risk in analysis['risk_factors'][:3]:
            msg5 += f"• {risk}\n"
        msg5 += "\n*Key Insights:*\n"
        for insight in analysis['key_insights'][:3]:
            msg5 += f"• {insight}\n"
        msg5 += "\n━━━━━━━━━━━━━━━━━━━━\n"
        msg5 += "_Analysis powered by AI • Not financial advice_"
        sections.append(msg5)
        
        return sections
    
    def format_report(self, analysis: Dict) -> str:
        """
        Legacy method - returns summary only
        Use format_summary() and format_detailed_sections() for new implementation
        """
        return self.format_summary(analysis)
        """
        Format analysis into user-friendly Telegram message
        
        Args:
            analysis: Complete analysis dictionary
            
        Returns:
            Formatted Telegram message with Markdown
        """
        symbol = analysis['symbol']
        price = analysis['current_price']
        change = analysis['price_change']
        change_emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
        
        tech = analysis['technical_analysis']
        fund = analysis['fundamental_analysis']
        sent = analysis['news_sentiment']
        ai = analysis['ai_recommendation']
        
        # Build message - use simpler formatting to avoid markdown issues
        msg = f"📊 *AI STOCK ANALYSIS*\n\n"
        msg += f"*Symbol*: {symbol}\n"
        msg += f"*Price*: ₹{price:,.2f} ({change_emoji}{change:+.2f}%)\n"
        msg += f"*Date*: {analysis['timestamp'].strftime('%Y-%m-%d %H:%M')}\n\n"
        
        msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "📈 *TECHNICAL ANALYSIS*\n"
        msg += f"• Trend: {tech['trend']}\n"
        msg += f"• Support: ₹{tech['support']:,.2f}\n"
        msg += f"• Resistance: ₹{tech['resistance']:,.2f}\n"
        msg += f"• RSI: {tech['rsi']} ({tech['rsi_signal']})\n"
        msg += f"• MACD: {tech['macd_signal']}\n"
        msg += f"• Volume: {tech['volume_trend']}\n\n"
        
        msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "💼 *FUNDAMENTAL ANALYSIS*\n"
        pe = fund.get('pe_ratio', 0)
        msg += f"• P/E Ratio: {f'{pe:.2f}' if pe else 'N/A'}\n"
        msg += f"• Market Cap: ₹{fund.get('market_cap', 0)/1e12:.2f}T\n"
        de = fund.get('debt_equity', 0)
        msg += f"• Debt/Equity: {f'{de:.2f}' if de else 'N/A'}\n"
        roe = fund.get('roe', 0)
        msg += f"• ROE: {f'{roe:.2f}' if roe else 'N/A'}%\n"
        dy = fund.get('dividend_yield', 0)
        msg += f"• Dividend Yield: {f'{dy:.2f}' if dy else 'N/A'}%\n"
        msg += f"• Score: {fund.get('score', 50)}/100\n\n"
        
        msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "📰 *NEWS SENTIMENT* (Last 7 Days)\n"
        msg += f"• Sentiment: {sent.get('sentiment', 'neutral').title()} ({sent.get('confidence', 50)}%)\n"
        msg += f"• Articles: {sent.get('article_count', 0)}\n"
        msg += f"• Impact: {sent.get('impact', 0):+d}\n\n"
        
        msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "🤖 *AI RECOMMENDATION*\n\n"
        msg += f"*Action*: {ai.get('recommendation', 'HOLD')}\n"
        msg += f"*Confidence*: {ai.get('confidence', 50)}%\n\n"
        
        # Only show trade levels if entry is not None
        entry = ai.get('entry')
        stop_loss = ai.get('stop_loss')
        target1 = ai.get('target1')
        target2 = ai.get('target2')
        
        if entry is not None and stop_loss is not None and target1 is not None:
            msg += f"*Entry*: ₹{entry:,.2f}\n"
            msg += f"*Stop Loss*: ₹{stop_loss:,.2f}\n"
            msg += f"*Target 1*: ₹{target1:,.2f}\n"
            if target2 is not None:
                msg += f"*Target 2*: ₹{target2:,.2f}\n"
            msg += f"*Timeframe*: {ai.get('timeframe', 'N/A')}\n"
            msg += f"*Strength*: {ai.get('strength', 'moderate').title()}\n\n"
        
        # Show full AI reasoning without truncation
        reasoning = ai.get('reasoning', 'N/A')
        msg += f"*Reasoning*:\n{reasoning}\n\n"
        
        msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "⚠️ *RISK FACTORS*\n"
        for risk in analysis['risk_factors'][:3]:  # Limit to 3
            msg += f"• {risk}\n"
        msg += "\n"
        
        msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "💡 *KEY INSIGHTS*\n"
        for insight in analysis['key_insights'][:3]:  # Limit to 3
            msg += f"• {insight}\n"
        msg += "\n"
        
        msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "_Analysis powered by AI • Not financial advice_"
        
        return msg

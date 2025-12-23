"""
News sentiment analysis using Gemini AI

Fetches news and analyzes sentiment to enhance trading signals
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import yfinance as yf

logger = logging.getLogger(__name__)

# Try to import Gemini
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-genai not installed. Install with: pip install google-genai")


class NewsSentimentAnalyzer:
    """
    Analyze news sentiment using Gemini AI
    
    Fetches recent news and uses Gemini to determine bullish/bearish sentiment
    """
    
    def __init__(self, provider: str = 'auto'):
        """
        Initialize sentiment analyzer
        
        Args:
            provider: 'gemini', 'openrouter', or 'auto' (tries OpenRouter first, falls back to Gemini)
        """
        self.provider = None
        self.model = None
        
        if provider == 'auto':
            # Try OpenRouter first (higher limits), fall back to Gemini
            if self._init_openrouter():
                return
            elif self._init_gemini():
                return
            else:
                raise ValueError("No AI provider configured. Set OPENROUTER_API_KEY or GEMINI_API_KEY")
        elif provider == 'openrouter':
            if not self._init_openrouter():
                raise ValueError("OPENROUTER_API_KEY environment variable not set")
        elif provider == 'gemini':
            if not self._init_gemini():
                raise ValueError("GEMINI_API_KEY environment variable not set")
        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'gemini', 'openrouter', or 'auto'")
    
    def _init_openrouter(self) -> bool:
        """Initialize OpenRouter (free open-source models)"""
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            return False
        
        try:
            import openai
            self.client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )
            # Use Gemma-3-27B for best free financial analysis (free, unlimited, fast)
            # This is the largest free model - better than Gemma-2-9B
            self.model_name = "google/gemma-3-27b-it:free"
            self.provider = 'openrouter'
            logger.info(f"OpenRouter initialized with model: {self.model_name}")
            return True
        except ImportError:
            logger.warning("openai library not installed for OpenRouter")
            return False
        except Exception as e:
            logger.error(f"Error initializing OpenRouter: {e}")
            return False
    
    def _init_gemini(self) -> bool:
        """Initialize Gemini AI with new google.genai package"""
        if not GEMINI_AVAILABLE:
            return False
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return False
        
        try:
            # Initialize client with new API
            self.client = genai.Client(api_key=api_key)
            self.model_name = 'gemini-2.0-flash-exp'
            self.provider = 'gemini'
            logger.info("Gemini AI initialized with new google.genai package")
            return True
        except Exception as e:
            logger.error(f"Error initializing Gemini: {e}")
            return False
    
    def get_news_sentiment(self, symbol: str, timeframe: str = '1d') -> Dict:
        """
        Get news sentiment for a symbol using Google News RSS
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            timeframe: Trading timeframe ('1d' or '75m')
            
        Returns:
            Sentiment analysis with impact score
        """
        try:
            # Extract company name from symbol
            company_name = symbol.replace('.NS', '').replace('.BO', '')
            
            # Timeframe-aware news lookback
            # Daily: 3 days (swing trades hold 3-10 days)
            # Intraday: 1 day (positions close same day)
            days_back = 1 if timeframe == '75m' else 3
            
            # Fetch news from Google News RSS
            news_items = self._fetch_google_news(company_name, days_back=days_back)
            
            # Analyze sentiment of the fetched news
            sentiment_result = self.analyze_sentiment(symbol, news_items)
            return sentiment_result
            
        except Exception as e:
            logger.error(f"Error getting news sentiment for {symbol}: {e}")
            return {
                'sentiment': 'neutral',
                'confidence': 0,
                'summary': f'Error: {str(e)}',
                'impact': 0
            }

    def _fetch_google_news(self, company_name: str, days_back: int = 7) -> List[Dict]:
        """
        Fetch recent news for a company name using Google News RSS
        
        Args:
            company_name: Company name for search
            days_back: Number of days to look back
            
        Returns:
            List of news articles
        """
        try:
            import feedparser
            from urllib.parse import quote
            
            # Common Indian company name mappings
            name_mapping = {
                'RELIANCE': 'Reliance Industries',
                'TCS': 'Tata Consultancy Services',
                'INFY': 'Infosys',
                'HDFCBANK': 'HDFC Bank',
                'ICICIBANK': 'ICICI Bank',
                'SBIN': 'State Bank of India',
                'BHARTIARTL': 'Bharti Airtel',
                'ITC': 'ITC Limited',
                'WIPRO': 'Wipro',
                'AXISBANK': 'Axis Bank',
                'LT': 'Larsen Toubro',
                'MARUTI': 'Maruti Suzuki',
                'TATAMOTORS': 'Tata Motors',
                'TATASTEEL': 'Tata Steel',
                'HCLTECH': 'HCL Technologies',
                'TECHM': 'Tech Mahindra',
                'SUNPHARMA': 'Sun Pharma',
                'ASIANPAINT': 'Asian Paints',
                'ULTRACEMCO': 'UltraTech Cement',
                'NESTLEIND': 'Nestle India',
                'TITAN': 'Titan Company',
                'BAJFINANCE': 'Bajaj Finance',
                'KOTAKBANK': 'Kotak Mahindra Bank',
                'HINDUNILVR': 'Hindustan Unilever',
                'ONGC': 'ONGC',
                'NTPC': 'NTPC',
                'POWERGRID': 'Power Grid',
                'COALINDIA': 'Coal India',
                'BPCL': 'Bharat Petroleum',
                'IOC': 'Indian Oil',
                'VEDL': 'Vedanta',
                'HINDALCO': 'Hindalco',
                'JSWSTEEL': 'JSW Steel',
                'GRASIM': 'Grasim Industries',
            }
            
            search_term = name_mapping.get(company_name, company_name)
            
            # Google News RSS feed URL
            rss_url = f"https://news.google.com/rss/search?q={quote(search_term)}&hl=en-IN&gl=IN&ceid=IN:en"
            
            # Fetch and parse RSS feed
            feed = feedparser.parse(rss_url)
            
            if not feed.entries:
                logger.warning(f"{company_name}: No news found in Google News RSS")
                return []
            
            # Filter recent news
            cutoff_date = datetime.now() - timedelta(days=days_back)
            recent_news = []
            
            for entry in feed.entries[:10]:  # Limit to 10 most recent
                try:
                    # Parse published date
                    pub_date = datetime(*entry.published_parsed[:6])
                    
                    if pub_date >= cutoff_date:
                        recent_news.append({
                            'title': entry.title,
                            'publisher': entry.source.get('title', 'Unknown') if hasattr(entry, 'source') else 'Google News',
                            'link': entry.link,
                            'published': pub_date
                        })
                except Exception as e:
                    logger.debug(f"Error parsing entry: {e}")
                    continue
            
            logger.info(f"{company_name}: Found {len(recent_news)} recent news articles from Google News")
            return recent_news
            
        except ImportError:
            logger.error("feedparser not installed. Install with: pip install feedparser")
            return []
        except Exception as e:
            logger.error(f"Error fetching news for {company_name}: {e}")
            return []
    
    def analyze_sentiment(self, symbol: str, news: List[Dict]) -> Dict:
        """
        Analyze news sentiment using AI
        
        Args:
            symbol: Stock symbol
            news: List of news articles
            
        Returns:
            Sentiment analysis result
        """
        if not news:
            return {
                'sentiment': 'neutral',
                'confidence': 0,
                'summary': 'No recent news',
                'impact': 0
            }
        
        # Prepare news for analysis
        news_text = "\n".join([
            f"- {article['title']} ({article['publisher']})"
            for article in news[:5]  # Analyze top 5 headlines
        ])
        
        # Create prompt
        prompt = f"""
Analyze the following recent news headlines for {symbol} stock and determine the overall sentiment:

{news_text}

Provide your analysis in this exact format:
SENTIMENT: [bullish/bearish/neutral]
CONFIDENCE: [0-100]
IMPACT: [-20 to +20] (negative for bearish, positive for bullish)
SUMMARY: [2-3 sentence explanation]

Focus on:
1. Overall market sentiment (bullish/bearish/neutral)
2. Confidence level (0-100)
3. Expected price impact (-20 to +20 points to adjust signal confidence)
4. Brief summary of key factors
"""
        
        try:
            if self.provider == 'openrouter':
                # Use OpenRouter API
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.choices[0].message.content
            else:
                # Use Gemini API (new google.genai package)
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                response_text = response.text
            
            result = self._parse_response(response_text)
            
            logger.info(f"{symbol}: Sentiment={result['sentiment']}, Confidence={result['confidence']}%, Impact={result['impact']}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment for {symbol}: {e}")
            return {
                'sentiment': 'neutral',
                'confidence': 0,
                'summary': f'Error: {str(e)}',
                'impact': 0
            }
    
    def _parse_response(self, response_text: str) -> Dict:
        """Parse Gemini's response"""
        result = {
            'sentiment': 'neutral',
            'confidence': 0,
            'impact': 0,
            'summary': ''
        }
        
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('SENTIMENT:'):
                sentiment = line.split(':', 1)[1].strip().lower()
                result['sentiment'] = sentiment
            
            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence = int(line.split(':', 1)[1].strip())
                    result['confidence'] = max(0, min(100, confidence))
                except:
                    pass
            
            elif line.startswith('IMPACT:'):
                try:
                    impact = int(line.split(':', 1)[1].strip())
                    result['impact'] = max(-20, min(20, impact))
                except:
                    pass
            
            elif line.startswith('SUMMARY:'):
                result['summary'] = line.split(':', 1)[1].strip()
        
        return result
    
    
    def analyze_technical_indicators(self, symbol: str, signal: Dict) -> Dict:
        """
        Get AI analysis of technical indicators and generate alternative trade levels
        
        Args:
            symbol: Stock symbol
            signal: Signal with analysis data
            
        Returns:
            AI technical analysis with predictions and alternative trade levels
        """
        analysis = signal.get('analysis', {})
        
        # Extract indicator values
        trend = analysis.get('trend', {})
        momentum = analysis.get('momentum', {})
        volatility = analysis.get('volatility', {})
        
        # Get raw data for AI analysis
        ohlcv_data = signal.get('ohlcv_data', [])
        fundamentals = signal.get('fundamentals', {})
        current_price = signal.get('entry_price', 0)
        
        # Get news sentiment if available
        sentiment_data = signal.get('sentiment', {})
        sentiment_text = ""
        if sentiment_data:
            sent_type = sentiment_data.get('sentiment', 'neutral').upper()
            sent_conf = sentiment_data.get('confidence', 0)
            sent_summary = sentiment_data.get('summary', 'No recent news')
            
            sentiment_text = f"""
**NEWS SENTIMENT:**
- Sentiment: {sent_type} ({sent_conf}% confidence)
- Summary: {sent_summary}
"""
        
        # Format ALL candles in TOON format with dates
        # TOON format: Date|O|H|L|C|V (one line per candle, tab-separated)
        candles_toon = ""
        num_candles = 0
        date_range = ""
        if ohlcv_data:
            num_candles = len(ohlcv_data)
            candles_toon = "\n".join([
                f"{c.get('date', 'N/A')}\t{c['open']:.2f}\t{c['high']:.2f}\t{c['low']:.2f}\t{c['close']:.2f}\t{int(c['volume'])}"
                for c in ohlcv_data
            ])
            # Get date range for prompt
            if ohlcv_data[0].get('date') and ohlcv_data[-1].get('date'):
                date_range = f" from {ohlcv_data[0]['date']} to {ohlcv_data[-1]['date']}"
        
        # Format fundamentals for AI
        fundamentals_text = ""
        if fundamentals:
            pe = fundamentals.get('trailing_pe', 'N/A')
            pb = fundamentals.get('price_to_book', 'N/A')
            roe = fundamentals.get('return_on_equity', 'N/A')
            if isinstance(roe, (int, float)):
                roe = f"{roe*100:.1f}%" if roe < 1 else f"{roe:.1f}%"
            debt_equity = fundamentals.get('debt_to_equity', 'N/A')
            market_cap = fundamentals.get('market_cap', 'N/A')
            if isinstance(market_cap, (int, float)):
                market_cap = f"₹{market_cap:,.0f} Cr"
            
            fundamentals_text = f"""
**FUNDAMENTAL METRICS:**
- P/E Ratio: {pe}
- P/B Ratio: {pb}
- ROE: {roe}
- Debt/Equity: {debt_equity}
- Market Cap: {market_cap}
"""
        
        # Create prompt with raw data in TOON format
        prompt = f"""
You are a professional technical analyst. Analyze {symbol} and provide independent trade recommendations.

**⚠️ DATA SCOPE:**
You have EXACTLY {num_candles} daily candles{date_range}.
When referencing specific events, USE THE EXACT DATES from the data (format: YYYY-MM-DD).
Example: "breakout on 2025-12-15" instead of "late Nov '23" or "recent breakout".

**CURRENT PRICE:** ₹{current_price}

**HISTORICAL PRICE DATA ({num_candles} candles in TOON Format - Tab-separated: Date|Open|High|Low|Close|Volume):**
{candles_toon}

{fundamentals_text}

{sentiment_text}

**Analysis Guidelines:**
Analyze the {num_candles} candles above to identify:
1. Support/resistance from swing highs/lows (reference exact dates)
2. Optimal entry, stop-loss, and target prices
3. Independent technical assessment

**IMPORTANT:** 
- When mentioning price levels or patterns, cite the EXACT DATE from the data
- Set stop-loss below recent support (specify the date of that swing low)
- Set targets at resistance levels (specify dates of swing highs)
- Consider risk:reward ratio (minimum 1:1.5)
- **DETAILED REASONING is REQUIRED** - provide comprehensive technical analysis
- **KEEP REASONING CONCISE: Maximum 1200-1500 characters**
- **USE EXACT DATES (YYYY-MM-DD format) when referencing specific candles or events**

Provide analysis in this EXACT format:
STRENGTH: [weak/moderate/strong]
PREDICTION: [bullish/bearish/neutral]
TIMEFRAME: [1-3 days/1 week/2 weeks]
KEY_FACTORS: [2-3 key technical factors]
RECOMMENDATION: [buy/hold/avoid]
AI_ENTRY: [price OR 'N/A']
AI_STOP: [price OR 'N/A']
AI_TARGET1: [price OR 'N/A']
AI_TARGET2: [price OR 'None' OR 'N/A']
REASONING: [Detailed but concise (1200-1500 chars): 1) Trend analysis citing specific dates, 2) Support/resistance levels with dates, 3) Volume patterns with dates, 4) Why these entry/stop/target levels, 5) Risk factors, 6) Overall setup. ALWAYS use YYYY-MM-DD format for dates.]
"""
        
        try:
            if self.provider == 'openrouter':
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.choices[0].message.content
            else:
                # Use Gemini API (new google.genai package)
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                response_text = response.text
            
            # Debug: Log raw AI response
            logger.info(f"{symbol}: Raw AI Response:\n{response_text}\n")
            
            result = self._parse_technical_analysis(response_text)
            logger.info(f"{symbol}: AI Technical - {result['prediction'].upper()} ({result['confidence']}%), Recommendation: {result['recommendation'].upper()}")
            
            # Log AI levels if generated
            if result.get('ai_entry'):
                logger.info(f"{symbol}: AI Levels - Entry: ₹{result['ai_entry']}, Stop: ₹{result['ai_stop']}, Target: ₹{result['ai_target1']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in technical analysis for {symbol}: {e}")
            return {
                'strength': 'moderate',
                'prediction': 'neutral',
                'timeframe': '1 week',
                'confidence': 50,
                'key_factors': [],
                'recommendation': 'hold',
                'reasoning': f'Error: {str(e)}',
                'ai_entry': None,
                'ai_stop': None,
                'ai_target1': None,
                'ai_target2': None
            }
    
    def _parse_technical_analysis(self, response_text: str) -> Dict:
        """Parse AI technical analysis response including trade levels"""
        result = {
            'strength': 'moderate',
            'prediction': 'neutral',
            'timeframe': '1 week',
            'confidence': 50,
            'key_factors': [],
            'recommendation': 'hold',
            'reasoning': '',
            'ai_entry': None,
            'ai_stop': None,
            'ai_target1': None,
            'ai_target2': None
        }
        
        # Split response into lines for parsing
        lines = response_text.strip().split('\n')
        
        # Track if we're in the REASONING section
        in_reasoning = False
        reasoning_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if not line:
                if in_reasoning:
                    reasoning_lines.append('')  # Preserve blank lines in reasoning
                continue
            
            # Check if we are starting a new field, which would end the reasoning capture
            if in_reasoning and (
                line.startswith('STRENGTH:') or
                line.startswith('PREDICTION:') or
                line.startswith('TIMEFRAME:') or
                line.startswith('CONFIDENCE:') or
                line.startswith('KEY_FACTORS:') or
                line.startswith('RECOMMENDATION:') or
                line.upper().startswith('AI_ENTRY:') or
                line.upper().startswith('AI_STOP:') or
                line.upper().startswith('AI_TARGET1:') or
                line.upper().startswith('AI_TARGET2:')
            ):
                in_reasoning = False # End reasoning capture if a new field starts
            
            if line.startswith('STRENGTH:'):
                result['strength'] = line.split(':', 1)[1].strip().lower()
            
            elif line.startswith('PREDICTION:'):
                result['prediction'] = line.split(':', 1)[1].strip().lower()
            
            elif line.startswith('TIMEFRAME:'):
                result['timeframe'] = line.split(':', 1)[1].strip()
            
            elif line.startswith('CONFIDENCE:'):
                try:
                    conf = int(line.split(':', 1)[1].strip())
                    result['confidence'] = max(0, min(100, conf))
                except:
                    pass
            
            elif line.startswith('KEY_FACTORS:'):
                factors = line.split(':', 1)[1].strip()
                result['key_factors'] = [f.strip() for f in factors.split(',')]
            
            elif line.startswith('RECOMMENDATION:'):
                result['recommendation'] = line.split(':', 1)[1].strip().lower()
            
            elif line.startswith('REASONING:'):
                # Start capturing reasoning - everything after this line
                in_reasoning = True
                # Get any text on the same line after "REASONING:"
                first_line = line.split(':', 1)[1].strip()
                if first_line:
                    reasoning_lines.append(first_line)
            
            elif in_reasoning:
                # Continue capturing reasoning until we hit another field or end
                reasoning_lines.append(line)
            
            # Parse AI-generated trade levels
            # These checks are separate because they might appear after reasoning,
            # or reasoning might appear after them.
            if line.upper().startswith('AI_ENTRY:'):
                try:
                    price_str = line.split(':', 1)[1].strip().replace('₹', '').replace(',', '')
                    result['ai_entry'] = float(price_str)
                except:
                    pass
            
            elif line.upper().startswith('AI_STOP:'):
                try:
                    price_str = line.split(':', 1)[1].strip().replace('₹', '').replace(',', '')
                    result['ai_stop'] = float(price_str)
                except:
                    pass
            
            elif line.upper().startswith('AI_TARGET1:'):
                try:
                    price_str = line.split(':', 1)[1].strip().replace('₹', '').replace(',', '')
                    result['ai_target1'] = float(price_str)
                except:
                    pass
            
            elif line.upper().startswith('AI_TARGET2:'):
                try:
                    price_str = line.split(':', 1)[1].strip().replace('₹', '').replace(',', '')
                    if price_str.lower() != 'none':
                        result['ai_target2'] = float(price_str)
                except:
                    pass
        
        # Join all collected reasoning lines into a single string
        if reasoning_lines:
            result['reasoning'] = '\n'.join(reasoning_lines).strip()
        
        # Fallback: If AI didn't provide levels but agreed with strategy (BUY + consensus), 
        # use strategy levels as AI levels to ensure display
        if result['recommendation'] == 'buy' and not result.get('ai_entry'):
            # These will be populated from outside if still None, but for now we just parse what we have.
            # We can't access strategy signal here easily without modifying signature, 
            # so we rely on the prompt being strict.
            pass

        return result
    
    def enhance_signal(self, signal: Dict, include_technical: bool = True, timeframe: str = '1d') -> Dict:
        """
        Enhance signal with news sentiment and AI technical analysis
        
        Args:
            signal: Base signal from strategy
            include_technical: Whether to include AI technical analysis
            timeframe: Trading timeframe ('1d' or '75m')
            
        Returns:
            Enhanced signal with sentiment and AI analysis
        """
        symbol = signal['symbol']
        
        # Get news sentiment with timeframe-aware lookback
        sentiment = self.get_news_sentiment(symbol, timeframe=timeframe)
        
        # Calculate sentiment-adjusted confidence
        original_confidence = signal.get('confidence', 0)
        
        # Adjust confidence based on sentiment impact
        adjusted_confidence = original_confidence + sentiment['impact']
        adjusted_confidence = max(0, min(100, adjusted_confidence))
        
        # Add sentiment data to signal
        signal['sentiment'] = sentiment
        signal['original_confidence'] = original_confidence
        signal['confidence'] = adjusted_confidence
        signal['sentiment_adjusted'] = sentiment['impact']
        
        logger.info(f"{symbol}: Confidence adjusted from {original_confidence:.1f}% to {adjusted_confidence:.1f}% (impact: {sentiment['impact']:+d})")
        
        # Add AI technical analysis
        if include_technical:
            logger.info(f"Getting AI technical analysis for {symbol}...")
            technical = self.analyze_technical_indicators(symbol, signal)
            signal['technical_analysis'] = technical
        
        return signal
    
    def batch_enhance_signals(self, signals: List[Dict], include_technical: bool = True, timeframe: str = '1d') -> List[Dict]:
        """
        Enhance multiple signals with sentiment and technical analysis
        
        Args:
            signals: List of signal dictionaries
            include_technical: Whether to include AI technical analysis
            timeframe: Trading timeframe ('1d' or '75m')
            
        Returns:
            Enhanced signals
        """
        enhanced = []
        
        for i, signal in enumerate(signals, 1):
            logger.info(f"[{i}/{len(signals)}] Analyzing {signal['symbol']}...")
            
            try:
                # Enhance signal with sentiment and technical analysis
                enhanced_signal = self.enhance_signal(signal.copy(), include_technical=include_technical, timeframe=timeframe)
                enhanced.append(enhanced_signal)
                
                # Rate limiting (7 seconds between requests to avoid API rate limits)
                if i < len(signals) - 1:
                    import time
                    logger.info(f"Waiting 7s for rate limit... ({i+1}/{len(signals)} complete)")
                    time.sleep(7)
                    
            except Exception as e:
                logger.error(f"Error enhancing {signal['symbol']}: {e}")
                enhanced.append(signal)  # Keep original if error
        
        return enhanced

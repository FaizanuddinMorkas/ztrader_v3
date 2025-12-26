# ZTrader v2 - AI-Powered Algorithmic Trading Platform

A comprehensive Python-based algorithmic trading platform for Indian stock markets (NSE) featuring AI-powered analysis, multi-timeframe data management, and automated signal generation for Nifty 100 stocks.

## ✨ Features

### Core Trading Features
- 📊 **Multi-timeframe OHLCV data** storage using TimescaleDB (1m, 5m, 15m, 30m, 1h, 1d)
- 🎯 **Nifty 100 coverage** with automated symbol management
- 📈 **Advanced technical indicators** (RSI, MACD, Bollinger Bands, Support/Resistance, Fibonacci, ATR, etc.)
- 🧠 **AI-powered sentiment analysis** using Google News + Gemini/OpenRouter LLMs
- 🤖 **AI technical analysis** with Gemma-3-27B providing trade recommendations and levels
- 💎 **Scored fundamentals strategy** combining technical + fundamental analysis
- 📱 **Telegram notifications** with detailed signal formatting and workflow status
- 📰 **Automated Market Reports** (Morning, Mid-day, Afternoon, Market Close)
- ⏰ **Intraday & Daily signals** supporting both 1d and 75m timeframes
- 🎯 **Hybrid setups** combining strategy signals with AI-suggested levels

### AI Capabilities
- **News Sentiment Analysis**: Fetches and analyzes recent news using Gemini API
- **Technical Analysis AI**: Gemma-3-27B model provides detailed chart analysis
- **Smart Confidence Adjustment**: Adjusts signal confidence based on news sentiment
- **Trade Level Suggestions**: AI-generated entry, stop-loss, and target levels
- **Consensus Detection**: Identifies agreement/conflict between strategy and AI
- **Rate Limiting**: 7-second delays with exponential backoff and fallback support

### Infrastructure & Automation
- 🗄️ **PostgreSQL + TimescaleDB** for efficient time-series storage
- ☁️ **AWS RDS** for production database with encryption
- 🚀 **EC2 deployment** with automated scripts and cron setup
- 🔄 **Smart data sync** with skip logic, force flag, and weekend handling
- 🔕 **Silent mode** for testing without notifications
- 📅 **Weekend-aware sync**: Automatically uses Friday data on weekends/Monday pre-market
- ✅ **Data completeness checks**: Validates data freshness before signal generation
- 🔧 **Fundamentals auto-sync**: Keeps fundamental data up-to-date

## 🏗️ Architecture

```
ztrader_new/
├── src/                        # Core application source code
│   ├── analysis/               # AI sentiment & technical analysis
│   │   ├── sentiment.py        # News sentiment analyzer with Gemini/OpenRouter
│   │   └── on_demand_analyzer.py  # On-demand AI technical analysis
│   ├── data/                   # Data management layer
│   │   ├── storage.py          # Database models (InstrumentsDB, OHLCVDB, FundamentalsDB)
│   │   ├── sync.py             # Smart data synchronization with skip logic
│   │   ├── downloader.py       # yfinance data downloader
│   │   ├── fundamentals.py     # Fundamentals data management
│   │   └── resample.py         # Timeframe resampling utilities
│   ├── strategies/             # Trading strategies
│   │   ├── base.py             # Base strategy class
│   │   ├── multi_indicator.py  # Multi-indicator strategy
│   │   ├── multi_indicator_scored.py  # Scored fundamentals strategy
│   │   ├── signal_generator.py        # Basic signal generator
│   │   └── signal_generator_scored.py # Scored signal generator with AI
│   ├── indicators/             # Technical indicators library
│   │   ├── base.py             # Base indicator class
│   │   ├── momentum.py         # RSI, MACD, Stochastic
│   │   ├── trend.py            # Moving averages, ADX
│   │   ├── volatility.py       # Bollinger Bands, ATR
│   │   ├── volume.py           # Volume indicators
│   │   ├── support_resistance.py  # S/R level detection
│   │   ├── pivot_support_resistance.py  # Pivot points
│   │   ├── fibonacci.py        # Fibonacci retracements
│   │   └── patterns.py         # Chart pattern detection
│   ├── notifications/          # Notification services
│   │   ├── telegram.py         # Telegram notifier for signals
│   │   └── interactive_bot.py  # Interactive Telegram bot with user tracking
│   ├── backtesting/            # Backtesting framework (in development)
│   ├── chat/                   # Chat/conversational features
│   │   └── user_tracker.py     # User interaction tracking
│   ├── execution/              # Order execution (planned)
│   ├── monitoring/             # System monitoring (planned)
│   ├── risk/                   # Risk management (planned)
│   ├── utils/                  # Utility functions
│   │   └── logger.py           # Logging utilities
│   └── config/                 # Configuration management
│       └── settings.py         # Application settings
├── scripts/                    # Executable scripts
│   ├── daily_workflow.py       # Main workflow orchestration
│   ├── telegram_bot.py         # Telegram bot launcher
│   ├── signals/                # Signal generation scripts
│   │   ├── daily_signals_scored.py  # AI-powered daily/intraday signals
│   │   └── daily_signals.py         # Legacy signal generator
│   ├── sync/                   # Data synchronization scripts
│   │   ├── sync_data.py        # OHLCV data sync with smart skip
│   │   ├── sync_fundamentals.py    # Fundamentals data sync
│   │   └── sync_special_stocks.py  # Special stocks sync
│   ├── deployment/             # EC2 deployment automation
│   │   ├── deploy_to_ec2.sh    # Deployment script
│   │   └── ec2_cron_setup.sh   # Cron job setup
│   ├── connection/             # Database connection scripts
│   │   ├── connect-rds.sh      # RDS connection via SSH tunnel
│   │   └── connect-postgres.sh # Local PostgreSQL connection
│   ├── migration/              # Database migration scripts
│   ├── maintenance/            # System maintenance scripts
│   ├── database/               # Database setup scripts
│   ├── testing/                # Testing utilities
│   └── utils/                  # Utility scripts
│       ├── add_new_stocks.py   # Add new stocks to database
│       ├── extend_instruments.py   # Extend instrument list
│       ├── fetch_fundamentals.py   # Fetch fundamentals data
│       ├── compare_strategies.py   # Strategy comparison
│       ├── check_candles.py        # Candle data validation
│       └── get_telegram_chat_id.py # Get Telegram chat ID
├── tests/                      # Test suite
├── database/                   # SQL migrations and schema
├── docs/                       # Documentation
│   ├── EC2_DEPLOYMENT.md       # EC2 deployment guide
│   ├── RDS_QUICK_START.md      # RDS setup guide
│   ├── SILENT_MODE.md          # Silent mode documentation
│   ├── DATA_SYNC_GUIDE.md      # Data sync guide
│   └── SYNC_IMPROVEMENTS.md    # Sync improvements changelog
├── cache/                      # Data cache directory
├── logs/                       # Application logs
├── backups/                    # Database backups
└── requirements.txt            # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ with TimescaleDB extension
- AWS account (for RDS and EC2)
- API keys:
  - OpenRouter API key (for AI analysis)
  - Gemini API key (fallback AI provider)
  - Telegram Bot Token (for notifications)

### Local Setup

```bash
# Clone repository
git clone https://github.com/FaizanuddinMorkas/ztrader-v2.git
cd ztrader-v2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install TA-Lib (required for technical indicators)
# macOS: brew install ta-lib
# Ubuntu: sudo apt-get install ta-lib
# Then: pip install TA-Lib

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### Environment Configuration

Create a `.env` file with the following variables:

```bash
# Database Configuration
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_PORT=5432
DB_NAME=trading_db
DB_USER=trading_user
DB_PASSWORD=your_secure_password

# Data Configuration
DATA_CACHE_DIR=./cache
DATA_LOG_DIR=./logs
DEFAULT_TIMEFRAMES=1m,5m,15m,1h,1d
YFINANCE_MAX_WORKERS=10

# AI API Keys
GEMINI_API_KEY=your_gemini_api_key
OPENROUTER_API_KEY=your_openrouter_api_key

# Telegram (Optional - for notifications)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
WORKFLOW_TELEGRAM_BOT_TOKEN=your_workflow_bot_token
WORKFLOW_TELEGRAM_CHAT_ID=your_workflow_chat_id
```

### Database Setup

```bash
# Connect to RDS (if using AWS)
./scripts/connect-rds.sh

# Run migrations
python database/run_migrations.py

# Seed Nifty 100 instruments
python scripts/database/seed_nifty100.py
```

## 📊 Usage

### Daily Workflow

The main workflow orchestrates data sync, signal generation, and notifications:

```bash
# Full workflow (sync + signals + notifications)
python scripts/daily_workflow.py

# Skip data sync (use existing data)
python scripts/daily_workflow.py --skip-sync

# Silent mode (no Telegram notifications)
python scripts/daily_workflow.py --no-notify

# Skip fundamentals check
python scripts/daily_workflow.py --skip-fundamentals
```

### Generate Trading Signals

```bash
# Daily signals with AI sentiment analysis (recommended)
python scripts/signals/daily_signals_scored.py --sentiment

# Intraday signals (75-minute timeframe)
python scripts/signals/daily_signals_scored.py --timeframe 75m --sentiment

# Test mode with specific symbols
python scripts/signals/daily_signals_scored.py --test --symbols RELIANCE.NS TCS.NS

# Test single symbol
python scripts/signals/daily_signals_scored.py --test-symbol RELIANCE.NS --sentiment

# Silent mode (no notifications)
python scripts/signals/daily_signals_scored.py --no-notify

# Custom minimum confidence threshold
python scripts/signals/daily_signals_scored.py --min-confidence 75 --sentiment
```

### Data Synchronization

```bash
# Incremental sync (smart skip enabled)
python scripts/sync/sync_data.py --timeframe 1d --update

# Full historical sync
python scripts/sync/sync_data.py --timeframe 1d --full

# Force sync (bypass smart skip logic)
python scripts/sync/sync_data.py --timeframe 1d --update --force

# Sync multiple timeframes
python scripts/sync/sync_data.py --timeframe 5m --update
python scripts/sync/sync_data.py --timeframe 1h --update

# Sync fundamentals data
python scripts/sync/sync_fundamentals.py
```

## ☁️ EC2 Deployment

### Deploy to EC2

```bash
# Deploy code to EC2
./scripts/deployment/deploy_to_ec2.sh <EC2_IP> ~/.ssh/your-key.pem

# SSH into EC2
ssh -i ~/.ssh/your-key.pem ubuntu@<EC2_IP>

# Activate environment
cd ~/ztrader
source venv/bin/activate

# Run workflow
python scripts/daily_workflow.py
```

### Setup Cron Job (Optional)

Configure the automated schedule for market reports and daily workflow:

```bash
# On EC2, setup comprehensive cron schedule
./scripts/deployment/ec2_cron_setup.sh
```

**Automated Schedule (IST):**
| Time | Type | Action |
| :--- | :--- | :--- |
| **09:30 AM** | Report | Morning Pulse (Gainers/Losers/Active) |
| **11:45 AM** | Report | Mid-Day Market Scan |
| **02:00 PM** | Report | Afternoon Movers (52W Highs/Lows) |
| **05:00 PM** | Report | Market Close Summary |
| **06:00 PM** | Workflow | Daily Sync + Signal Generation |


## 🤖 AI Features

### Sentiment Analysis
The platform integrates AI-powered news sentiment analysis to enhance signal quality:

- **News Source**: Fetches recent articles from Google News RSS feeds
- **AI Models**: 
  - Primary: OpenRouter API (various models)
  - Fallback: Google Gemini API
- **Analysis Output**:
  - Sentiment classification (Bullish/Bearish/Neutral)
  - Confidence score (0-100%)
  - Reasoning for the sentiment
- **Signal Enhancement**: Adjusts strategy confidence based on news sentiment
- **Timeframe Support**: Both daily and intraday analysis
- **Compact Mode**: Optimized prompts for batch processing to reduce token usage

### AI Technical Analysis
Advanced chart analysis using state-of-the-art language models:

- **Model**: Gemma-3-27B via OpenRouter
- **Analysis Includes**:
  - Price prediction (Bullish/Bearish/Neutral)
  - Trade recommendation (BUY/HOLD/SELL/AVOID)
  - Signal strength assessment (Strong/Moderate/Weak)
  - Key factors driving the analysis
  - Chart pattern identification
- **Trade Levels**: AI-generated entry, stop-loss, and target prices
- **Reasoning**: Detailed explanation (1200-1500 chars) of the analysis
- **Consensus Detection**: Compares AI recommendation with strategy signal
- **Hybrid Setups**: Combines best levels from both strategy and AI

### Rate Limiting & Reliability
- **API Rate Limiting**: 7-second delay between calls to avoid rate limits
- **Retry Logic**: Exponential backoff on failures
- **Fallback Support**: Automatically switches to Gemini if OpenRouter fails
- **Error Handling**: Graceful degradation when AI services are unavailable
- **Date Accuracy**: AI references exact dates from candle data (YYYY-MM-DD format)
- **Null Safety**: Proper handling of missing or None values in AI responses

## 📱 Telegram Integration

### Signal Notifications

Signals are sent to Telegram with:
- Strategy signal (entry, stop-loss, targets)
- AI sentiment analysis
- AI technical analysis
- Hybrid setup (best of both)
- Risk/reward ratios

### Workflow Status

Workflow status reports include:
- Execution time
- Step-by-step success/failure status
- Error details (if any)

## 📚 Documentation

- **Deployment Guide**: `docs/EC2_DEPLOYMENT.md`
- **RDS Setup**: `docs/RDS_QUICK_START.md`
- **Silent Mode**: `docs/SILENT_MODE.md`
- **Data Sync**: `docs/DATA_SYNC_GUIDE.md`
- **Database**: `database/README.md`

## 🛠️ Development

### Running Tests

```bash
# Test database connection
python tests/test_db_connection.py

# Test Telegram notifications
python tests/test_telegram.py

# Test sentiment analysis
python tests/test_sentiment.py

# Test strategy
python tests/test_scored_strategy.py

# Test AI technical analysis
python tests/test_ai_analysis.py
```

### Code Quality

```bash
# Format code
black src/

# Lint code
flake8 src/
```

## 🆕 Recent Improvements

### December 2025 Updates

#### AI Enhancements
- **Fixed AI Date Hallucination**: AI now references exact dates from candle data in YYYY-MM-DD format
- **Improved Error Handling**: Fixed `TypeError` when formatting `None` AI-suggested levels
- **Enhanced Prompts**: Compact mode for batch processing with optimized token usage
- **Gemma-3-27B Integration**: Advanced AI model for technical analysis with detailed reasoning

#### Data Sync Improvements
- **Smart Sync Skip**: Automatically skips sync if data is already up-to-date
- **Force Flag**: `--force` option to bypass smart skip when needed
- **Weekend Handling**: Uses Friday as reference date on weekends and Monday pre-market
- **Data Completeness Checks**: Validates data freshness before signal generation
- **Auto Fundamentals Sync**: Automatically updates stale fundamental data

#### Workflow Automation
- **Daily Workflow Script**: Orchestrates complete workflow from sync to signals
- **Telegram Status Reports**: Workflow execution summaries sent via Telegram
- **Silent Mode**: `--no-notify` flag for testing without notifications
- **Flexible Options**: Skip sync, skip fundamentals, test mode support

#### Signal Generation
- **Intraday Support**: Added 75m timeframe for intraday trading
- **Hybrid Setups**: Combines strategy signals with AI-suggested levels
- **Consensus Detection**: Identifies agreement/conflict between strategy and AI
- **Enhanced Formatting**: Rich Telegram messages with emojis and structured data
- **Confidence Adjustment**: News sentiment adjusts signal confidence scores

#### Infrastructure
- **EC2 Migration**: Successfully migrated from local to EC2 with RDS
- **SSH Tunnel Support**: Secure database access via SSH tunneling
- **Cron Automation**: Automated daily workflow execution
- **Improved Logging**: Comprehensive logging for debugging and monitoring

## 🗺️ Roadmap

### ✅ Completed
- [x] Database schema with TimescaleDB
- [x] Multi-timeframe data sync (1m, 5m, 15m, 30m, 1h, 1d)
- [x] Technical indicators library (RSI, MACD, Bollinger Bands, ATR, etc.)
- [x] Scored fundamentals strategy
- [x] AI sentiment analysis (Google News + Gemini)
- [x] AI technical analysis (Gemma-3-27B)
- [x] Telegram notifications with rich formatting
- [x] EC2 deployment automation
- [x] RDS migration and setup
- [x] Silent mode for testing
- [x] Smart sync with weekend handling
- [x] Daily workflow orchestration
- [x] Intraday signal support (75m timeframe)
- [x] Hybrid setups (Strategy + AI levels)
- [x] Data completeness validation
- [x] Auto fundamentals sync
- [x] Automated Market Reports (4x Daily)
- [x] User Activity Tracking


### 🚧 In Progress
- [ ] Backtesting engine optimization
- [ ] Performance analytics dashboard
- [ ] Additional screener features

### 📋 Planned
- [ ] Risk management module with position sizing
- [ ] Paper trading simulation
- [ ] Live trading integration with broker APIs
- [ ] Portfolio management and tracking
- [ ] Multi-strategy support
- [ ] Options trading signals
- [ ] Advanced charting and visualization
- [ ] Mobile app for signal notifications
- [ ] Webhook support for third-party integrations
- [ ] Machine learning model training pipeline

## 🔒 Security Notes

- Never commit `.env` files to version control
- Use `.env.example` as a template
- Rotate API keys regularly
- Use AWS IAM roles for EC2 access
- Enable RDS encryption at rest
- Use security groups to restrict database access

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or support, please open an issue on GitHub.

# ZTrader v2 - AI-Powered Algorithmic Trading Platform

A Python-based algorithmic trading platform for Indian stock markets (NSE) with AI-powered sentiment analysis and technical indicators for Nifty 100 stocks.

## ✨ Features

### Core Trading Features
- 📊 **Multi-timeframe OHLCV data** storage using TimescaleDB (1m, 5m, 15m, 30m, 1h, 1d)
- 🎯 **Nifty 100 coverage** with automated symbol management
- 📈 **Advanced technical indicators** (RSI, MACD, Bollinger Bands, Support/Resistance, Fibonacci, etc.)
- 🧠 **AI-powered sentiment analysis** using news articles and LLMs
- 🤖 **AI technical analysis** with trade level suggestions (entry, stop-loss, targets)
- 💎 **Scored fundamentals strategy** combining technical + fundamental analysis
- 📱 **Telegram notifications** for signals and workflow status

### Infrastructure
- 🗄️ **PostgreSQL + TimescaleDB** for efficient time-series storage
- ☁️ **AWS RDS** for production database
- 🚀 **EC2 deployment** with automated scripts
- 🔄 **Smart data sync** with skip logic and weekend handling
- 🔕 **Silent mode** for testing without notifications

## 🏗️ Architecture

```
ztrader_new/
├── src/
│   ├── analysis/          # AI sentiment & technical analysis
│   ├── data/              # Data management, sync, fundamentals
│   ├── strategies/        # Trading strategies (scored, multi-indicator)
│   ├── indicators/        # Technical indicators library
│   ├── notifications/     # Telegram integration
│   └── config/            # Configuration management
├── scripts/
│   ├── daily_workflow.py  # Main workflow orchestration
│   ├── signals/           # Signal generation scripts
│   │   ├── daily_signals_scored.py  # AI-powered signals
│   │   └── daily_signals.py         # Legacy signals
│   ├── sync/              # Data synchronization
│   │   ├── sync_data.py
│   │   ├── sync_fundamentals.py
│   │   └── sync_special_stocks.py
│   ├── deployment/        # EC2 deployment
│   │   ├── deploy_to_ec2.sh
│   │   └── ec2_cron_setup.sh
│   ├── connection/        # Database connections
│   │   ├── connect-rds.sh
│   │   └── connect-postgres.sh
│   ├── migration/         # Database migrations
│   ├── maintenance/       # System maintenance
│   ├── utils/             # Utility scripts
│   ├── database/          # Database setup
│   └── testing/           # Testing scripts
├── tests/                 # All test files
├── database/              # SQL migrations
├── docs/                  # Documentation
└── requirements.txt       # Python dependencies
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
# Generate signals with AI sentiment analysis
python scripts/signals/daily_signals_scored.py --sentiment

# Test mode with specific symbols
python scripts/signals/daily_signals_scored.py --test --symbols RELIANCE.NS,TCS.NS

# Silent mode (no notifications)
python scripts/signals/daily_signals_scored.py --no-notify
```

### Data Synchronization

```bash
# Sync all timeframes
python scripts/sync/sync_data.py --timeframe 1d --update

# Full historical sync
python scripts/sync/sync_data.py --timeframe 1d --full

# Force sync (bypass smart skip)
python scripts/sync/sync_data.py --timeframe 1d --update --force
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

```bash
# On EC2, setup daily cron job
./scripts/deployment/ec2_cron_setup.sh
```

## 🤖 AI Features

### Sentiment Analysis

- Fetches recent news articles from Google News
- Analyzes sentiment using LLMs (OpenRouter/Gemini)
- Adjusts signal confidence based on news sentiment
- Supports both daily and intraday timeframes

### AI Technical Analysis

- Provides trade recommendations (BUY/SELL/HOLD/AVOID)
- Suggests entry, stop-loss, and target levels
- Analyzes chart patterns and key factors
- Includes detailed reasoning for each recommendation

### Rate Limiting

- 7-second delay between API calls
- Automatic retry with exponential backoff
- Fallback to Gemini if OpenRouter fails

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
```

### Code Quality

```bash
# Format code
black src/

# Lint code
flake8 src/
```

## 🗺️ Roadmap

- [x] Database schema with TimescaleDB
- [x] Multi-timeframe data sync
- [x] Technical indicators library
- [x] Scored fundamentals strategy
- [x] AI sentiment analysis
- [x] AI technical analysis
- [x] Telegram notifications
- [x] EC2 deployment automation
- [x] Silent mode for testing
- [ ] Backtesting engine
- [ ] Risk management module
- [ ] Paper trading
- [ ] Live trading integration
- [ ] Performance dashboard
- [ ] Portfolio management

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

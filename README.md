# ZTrader - Algorithmic Trading Platform

A Python-based algorithmic trading platform for Indian stock markets (NSE) with focus on Nifty 100 stocks.

## Features

- ✅ **Multi-timeframe OHLCV data** storage using TimescaleDB
- ✅ **Nifty 100 support** with symbol management
- ✅ **yfinance integration** for historical data download
- ✅ **Modular architecture** for strategies, backtesting, and risk management
- ✅ **PostgreSQL + TimescaleDB** for efficient time-series storage
- 🚧 **Strategy framework** for custom trading strategies
- 🚧 **Backtesting engine** for strategy validation
- 🚧 **Risk management** module

## Project Structure

```
ztrader_new/
├── src/                    # Source code
│   ├── config/             # Configuration management
│   ├── data/               # Data management (storage, downloader)
│   ├── strategies/         # Trading strategies
│   ├── indicators/         # Technical indicators
│   ├── backtesting/        # Backtesting engine
│   ├── risk/               # Risk management
│   ├── execution/          # Order execution
│   ├── monitoring/         # Logging and alerts
│   └── utils/              # Utilities
├── database/               # Database migrations
├── examples/               # Example scripts
├── tests/                  # Unit tests
├── scripts/                # Utility scripts
│   ├── database/           # Database setup scripts
│   └── testing/            # Testing scripts
├── docs/                   # Documentation
│   ├── deployment/         # Deployment guides
│   └── setup/              # Setup guides
├── logs/                   # Log files (auto-created)
├── cache/                  # Data cache (auto-created)
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Quick Start

### 1. Prerequisites

- Python 3.10+
- PostgreSQL 14+ with TimescaleDB extension
- SSH access to EC2 database (or local PostgreSQL)

### 2. Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Start SSH tunnel to EC2 database (in separate terminal)
./scripts/connect-postgres.sh

# Run migrations
python3 database/run_migrations.py
```

### 4. Configuration

Edit `.env` file with your settings:

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_db
DB_USER=trading_user
DB_PASSWORD=your_password
```

## Usage

### Download Historical Data

```python
from src.data.downloader import download_nifty100_data

# Download data for all Nifty 100 stocks
results = download_nifty100_data(
    timeframes=['1d', '1h'],
    period='1y'
)
```

### Query OHLCV Data

```python
from src.data.storage import OHLCVDB

db = OHLCVDB()
df = db.get_ohlcv('RELIANCE.NS', '1d', limit=100)
```

### Manage Instruments

```python
from src.data.storage import InstrumentsDB

db = InstrumentsDB()
symbols = db.get_nifty_100()
it_stocks = db.get_by_sector('Information Technology')
```

## Documentation

- **Setup Guides**: `docs/setup/`
- **Deployment Guides**: `docs/deployment/`
- **Database Documentation**: `database/README.md`
- **Research & Architecture**: `docs/algo_trading_platform_research.md`

## Scripts

- **Database**: `scripts/database/` - Setup and migration scripts
- **Testing**: `scripts/testing/` - Connection and integration tests
- **Connection**: `scripts/connect-postgres.sh` - SSH tunnel to EC2 database

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
flake8 src/
```

## Roadmap

- [x] Database schema with TimescaleDB
- [x] Data download and storage
- [x] Project structure and configuration
- [ ] Technical indicators library
- [ ] Strategy framework
- [ ] Backtesting engine
- [ ] Risk management module
- [ ] Paper trading
- [ ] Live trading integration
- [ ] Telegram notifications
- [ ] Performance dashboard

## License

MIT

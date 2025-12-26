# Telegram Market Analysis Bot

Get real-time NSE market data directly in Telegram!

## 🚀 Quick Start

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Copy the bot token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Install Dependencies

```bash
pip install python-telegram-bot
```

### 3. Set Bot Token

```bash
export TELEGRAM_BOT_TOKEN='your-bot-token-here'
```

Or add to your `.env` file:
```
TELEGRAM_BOT_TOKEN=your-bot-token-here
```

### 4. Run the Bot

```bash
python scripts/telegram/market_bot.py
```

### 5. Start Using

1. Open Telegram
2. Search for your bot (by username you created)
3. Send `/start` to begin!

---

## 📱 Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Welcome message and help | `/start` |
| `/help` | Show all commands | `/help` |
| `/gainers [limit]` | Top gainers from Nifty 500 | `/gainers 10` |
| `/losers [limit]` | Top losers from Nifty 500 | `/losers 5` |
| `/active [limit]` | Most active stocks by volume | `/active 10` |
| `/52high [limit]` | Stocks at 52-week high | `/52high 10` |
| `/52low [limit]` | Stocks at 52-week low | `/52low 5` |
| `/sectors` | All sector performance | `/sectors` |
| `/overview` | Complete market snapshot | `/overview` |

**Default limit:** 10 stocks  
**Maximum limit:** 20 stocks

---

## 💡 Usage Examples

### Get Top 5 Gainers
```
/gainers 5
```

**Response:**
```
📈 TOP 5 GAINERS (NIFTY 500)

🟢 MMTC - MMTC Limited
   ₹65.20 (+13.33%)

🟢 RVNL - Rail Vikas Nigam Limited
   ₹387.25 (+12.02%)

🟢 IRFC - Indian Railway Finance...
   ₹133.60 (+9.97%)
...
```

### Check Sector Performance
```
/sectors
```

**Response:**
```
📊 SECTOR PERFORMANCE

🟢 METAL: +0.59%
🟢 CONSUMER DURABLES: +0.34%
⚪ FMCG: +0.03%
🔴 IT: -1.03%
...
```

### Market Overview
```
/overview
```

**Response:**
```
📊 MARKET OVERVIEW

📈 Top 3 Gainers:
🟢 MMTC: +13.33%
🟢 RVNL: +12.02%
🟢 IRFC: +9.97%

📉 Top 3 Losers:
🔴 RPOWER: -3.96%
🔴 JBMA: -3.74%
🔴 COFORGE: -3.67%

🏆 Best Sector:
METAL: +0.59%

⚠️ Worst Sector:
IT: -1.03%
```

---

## 🔧 Advanced Configuration

### Run as Background Service

Using `screen`:
```bash
screen -S market-bot
python scripts/telegram/market_bot.py
# Press Ctrl+A then D to detach
```

Using `nohup`:
```bash
nohup python scripts/telegram/market_bot.py > bot.log 2>&1 &
```

### Auto-start on System Boot

Create systemd service `/etc/systemd/system/market-bot.service`:

```ini
[Unit]
Description=Telegram Market Analysis Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/ztrader_new
Environment="TELEGRAM_BOT_TOKEN=your-token-here"
ExecStart=/path/to/venv/bin/python scripts/telegram/market_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable market-bot
sudo systemctl start market-bot
sudo systemctl status market-bot
```

---

## 🎯 Features

- ✅ Real-time NSE market data
- ✅ Nifty 500 top movers
- ✅ 52-week high/low detection
- ✅ Sector performance tracking
- ✅ Volume analysis
- ✅ Clean formatted messages
- ✅ Emoji indicators
- ✅ Error handling
- ✅ Rate limiting (NSE API)
- ✅ Caching (5-minute TTL)

---

## 📊 Data Sources

All data is fetched from:
- **NSE India** public APIs
- **Real-time** market data
- **Nifty 500** constituents
- **16 sectoral indices**

---

## 🛡️ Security Notes

1. **Never share your bot token** publicly
2. Store token in environment variables
3. Use `.env` file (add to `.gitignore`)
4. Restrict bot access if needed (via BotFather)

---

## 🐛 Troubleshooting

### Bot not responding
- Check if bot is running: `ps aux | grep market_bot`
- Check logs for errors
- Verify bot token is correct

### "No data available"
- NSE API might be down
- Market might be closed
- Check internet connection

### Rate limiting errors
- Bot has built-in rate limiting (1.5s between requests)
- NSE API has caching (5-minute TTL)
- Avoid rapid consecutive commands

---

## 🔄 Updates

To update the bot:
```bash
# Pull latest changes
git pull

# Restart bot
pkill -f market_bot.py
python scripts/telegram/market_bot.py
```

---

## 📝 Customization

### Change Default Limit
Edit `market_bot.py`:
```python
limit = int(context.args[0]) if context.args else 15  # Change from 10 to 15
```

### Add Custom Commands
```python
async def my_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Your custom logic
    await update.message.reply_text("Custom response")

# Register handler
application.add_handler(CommandHandler("mycommand", my_command))
```

---

## 🎉 Enjoy!

Your personal market analysis assistant is ready! 📈📊

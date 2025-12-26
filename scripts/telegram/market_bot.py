#!/usr/bin/env python3
"""
Telegram Bot for Market Analysis
Provides real-time market data via Telegram commands

Commands:
  /gainers [limit] - Top gainers from Nifty 500
  /losers [limit] - Top losers from Nifty 500
  /active [limit] - Most active stocks by volume
  /52high [limit] - Stocks at 52-week high
  /52low [limit] - Stocks at 52-week low
  /sectors - Sector performance
  /overview - Complete market overview
  /help - Show all commands
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data.nse_api import NSEClient

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize NSE client
nse_client = NSEClient()


def format_stock_message(df, title, limit=10):
    """Format stock data for Telegram message"""
    if df.empty:
        return f"*{title}*\n\nNo data available."
    
    message = f"*{title}*\n\n"
    
    for idx, row in df.head(limit).iterrows():
        symbol = row.get('symbol', 'N/A').replace('.NS', '')
        company = row.get('companyName', '')
        
        # Get price - try different column names
        ltp = row.get('lastPrice') or row.get('ltp') or row.get('last', 0)
        
        # Get change - try different column names
        pchange = row.get('pChange') or row.get('perChange', 0)
        
        # Format company name
        if 'meta' in row and isinstance(row['meta'], dict):
            company = row['meta'].get('companyName', company)
        
        # Truncate company name
        if len(company) > 25:
            company = company[:22] + '...'
        
        # Format emoji based on change
        emoji = "🟢" if pchange > 0 else "🔴" if pchange < 0 else "⚪"
        
        message += f"{emoji} *{symbol}*"
        if company:
            message += f" - {company}"
        message += f"\n   ₹{ltp:,.2f} ({pchange:+.2f}%)\n\n"
    
    return message


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    welcome_msg = """
🎯 *Market Analysis Bot*

Get real-time NSE market data instantly!

*📊 SCREENER COMMANDS:*

📈 */gainers* `[limit]`
Get top gainers from Nifty 500
Example: `/gainers 10`

📉 */losers* `[limit]`
Get top losers from Nifty 500
Example: `/losers 5`

🔥 */active* `[limit]`
Most active stocks by volume
Example: `/active 10`

🚀 */52high* `[limit]`
Stocks hitting 52-week high today
Example: `/52high 10`

⚠️ */52low* `[limit]`
Stocks hitting 52-week low today
Example: `/52low 5`

🏭 */sectors*
View all 16 sector performances
Example: `/sectors`

📊 */overview*
Complete market snapshot
Shows top gainers, losers, and best/worst sectors
Example: `/overview`

ℹ️ */help*
Show this help message

*📝 NOTES:*
• Default limit: 10 stocks
• Maximum limit: 20 stocks
• All data from NSE India (real-time)
• Data updates every 5 minutes (cached)

*🎯 QUICK START:*
Try: `/gainers 5` to see top 5 gainers!
    """
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed help message"""
    help_msg = """
📚 *DETAILED COMMAND GUIDE*

*1️⃣ TOP GAINERS*
Command: `/gainers [limit]`
Shows stocks with highest % gain today
• From Nifty 500 index
• Sorted by % change (highest first)
• Shows: Symbol, Company, Price, % Change

Examples:
`/gainers` → Top 10 gainers
`/gainers 5` → Top 5 gainers
`/gainers 20` → Top 20 gainers

---

*2️⃣ TOP LOSERS*
Command: `/losers [limit]`
Shows stocks with highest % loss today
• From Nifty 500 index
• Sorted by % change (lowest first)
• Shows: Symbol, Company, Price, % Change

Examples:
`/losers` → Top 10 losers
`/losers 5` → Top 5 losers

---

*3️⃣ MOST ACTIVE*
Command: `/active [limit]`
Shows stocks with highest trading volume
• Based on shares traded
• Indicates high investor interest
• Shows: Symbol, Company, Price, Volume

Examples:
`/active` → Top 10 by volume
`/active 15` → Top 15 by volume

---

*4️⃣ 52-WEEK HIGH*
Command: `/52high [limit]`
Shows stocks touching/breaking their year-high TODAY
• Stocks at or above 52-week high
• Strong momentum indicator
• Sorted by % gain

Examples:
`/52high` → Top 10 at 52W high
`/52high 5` → Top 5 at 52W high

---

*5️⃣ 52-WEEK LOW*
Command: `/52low [limit]`
Shows stocks touching/breaking their year-low TODAY
• Stocks at or below 52-week low
• Potential value plays or avoid
• Sorted by % loss

Examples:
`/52low` → Top 10 at 52W low
`/52low 5` → Top 5 at 52W low

---

*6️⃣ SECTOR PERFORMANCE*
Command: `/sectors`
Shows all 16 NSE sector indices
• Identifies sector rotation
• Best and worst performing sectors
• No limit parameter needed

Example:
`/sectors` → View all sectors

---

*7️⃣ MARKET OVERVIEW*
Command: `/overview`
Complete market snapshot in one view
• Top 3 gainers
• Top 3 losers
• Best sector
• Worst sector

Example:
`/overview` → Quick market pulse

---

*💡 PRO TIPS:*
• Use `/gainers 5` for quick checks
• Use `/overview` for market pulse
• Check `/sectors` for rotation
• Combine `/52high` with `/gainers` for momentum plays

*⚙️ TECHNICAL INFO:*
• Data source: NSE India
• Update frequency: Real-time (5min cache)
• Coverage: Nifty 500 stocks
• Sectors: All 16 NSE indices

Need help? Just send `/help` anytime!
    """
    await update.message.reply_text(help_msg, parse_mode='Markdown')


async def gainers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get top gainers"""
    try:
        limit = int(context.args[0]) if context.args else 10
        limit = min(limit, 20)  # Max 20
        
        await update.message.reply_text("🔍 Fetching top gainers...")
        
        df = nse_client.get_top_movers_from_index('NIFTY 500', limit=limit, sort_by='gainers')
        message = format_stock_message(df, f"📈 TOP {limit} GAINERS (NIFTY 500)", limit)
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in gainers command: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def losers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get top losers"""
    try:
        limit = int(context.args[0]) if context.args else 10
        limit = min(limit, 20)
        
        await update.message.reply_text("🔍 Fetching top losers...")
        
        df = nse_client.get_top_movers_from_index('NIFTY 500', limit=limit, sort_by='losers')
        message = format_stock_message(df, f"📉 TOP {limit} LOSERS (NIFTY 500)", limit)
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in losers command: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def active(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get most active stocks"""
    try:
        limit = int(context.args[0]) if context.args else 10
        limit = min(limit, 20)
        
        await update.message.reply_text("🔍 Fetching most active stocks...")
        
        df = nse_client.get_most_active_by_volume(limit=limit)
        message = format_stock_message(df, f"🔥 MOST ACTIVE BY VOLUME - TOP {limit}", limit)
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in active command: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def week_52_high(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get stocks at 52-week high"""
    try:
        limit = int(context.args[0]) if context.args else 10
        limit = min(limit, 20)
        
        await update.message.reply_text("🔍 Fetching 52-week highs...")
        
        df = nse_client.get_52week_high(limit=limit)
        message = format_stock_message(df, f"🚀 STOCKS AT 52-WEEK HIGH - TOP {limit}", limit)
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in 52high command: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def week_52_low(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get stocks at 52-week low"""
    try:
        limit = int(context.args[0]) if context.args else 10
        limit = min(limit, 20)
        
        await update.message.reply_text("🔍 Fetching 52-week lows...")
        
        df = nse_client.get_52week_low(limit=limit)
        message = format_stock_message(df, f"⚠️ STOCKS AT 52-WEEK LOW - TOP {limit}", limit)
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in 52low command: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def sectors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get sector performance"""
    try:
        await update.message.reply_text("🔍 Fetching sector performance...")
        
        df = nse_client.get_sector_performance()
        
        if df.empty:
            await update.message.reply_text("*SECTOR PERFORMANCE*\n\nNo data available.", parse_mode='Markdown')
            return
        
        message = "*📊 SECTOR PERFORMANCE*\n\n"
        
        for idx, row in df.iterrows():
            sector = row.get('sector', 'N/A')
            pchange = row.get('pChange', 0)
            
            emoji = "🟢" if pchange > 0 else "🔴" if pchange < 0 else "⚪"
            
            # Shorten sector name
            sector_short = sector.replace('NIFTY ', '')
            
            message += f"{emoji} *{sector_short}*: {pchange:+.2f}%\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in sectors command: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def overview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get market overview"""
    try:
        await update.message.reply_text("🔍 Fetching market overview...")
        
        # Get top 5 gainers
        gainers_df = nse_client.get_top_movers_from_index('NIFTY 500', limit=5, sort_by='gainers')
        
        # Get top 5 losers
        losers_df = nse_client.get_top_movers_from_index('NIFTY 500', limit=5, sort_by='losers')
        
        # Get sector performance
        sectors_df = nse_client.get_sector_performance()
        
        # Format message
        message = "*📊 MARKET OVERVIEW*\n\n"
        
        # Top 3 gainers
        message += "*📈 Top 3 Gainers:*\n"
        for idx, row in gainers_df.head(3).iterrows():
            symbol = row.get('symbol', 'N/A').replace('.NS', '')
            pchange = row.get('pChange', 0)
            message += f"🟢 {symbol}: {pchange:+.2f}%\n"
        
        message += "\n*📉 Top 3 Losers:*\n"
        for idx, row in losers_df.head(3).iterrows():
            symbol = row.get('symbol', 'N/A').replace('.NS', '')
            pchange = row.get('pChange', 0)
            message += f"🔴 {symbol}: {pchange:+.2f}%\n"
        
        # Best and worst sectors
        if not sectors_df.empty:
            best_sector = sectors_df.iloc[0]
            worst_sector = sectors_df.iloc[-1]
            
            message += f"\n*🏆 Best Sector:*\n"
            message += f"{best_sector['sector'].replace('NIFTY ', '')}: {best_sector['pChange']:+.2f}%\n"
            
            message += f"\n*⚠️ Worst Sector:*\n"
            message += f"{worst_sector['sector'].replace('NIFTY ', '')}: {worst_sector['pChange']:+.2f}%\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in overview command: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


def main():
    """Start the bot"""
    # Get bot token from environment variable (loaded from .env)
    token = os.getenv('ANALYSIS_TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("ANALYSIS_TELEGRAM_BOT_TOKEN environment variable not set!")
        print("\n❌ Error: ANALYSIS_TELEGRAM_BOT_TOKEN not set!")
        print("\nPlease add to .env file:")
        print("  ANALYSIS_TELEGRAM_BOT_TOKEN='your-bot-token-here'")
        print("\nGet your token from @BotFather on Telegram")
        sys.exit(1)
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("gainers", gainers))
    application.add_handler(CommandHandler("losers", losers))
    application.add_handler(CommandHandler("active", active))
    application.add_handler(CommandHandler("52high", week_52_high))
    application.add_handler(CommandHandler("52low", week_52_low))
    application.add_handler(CommandHandler("sectors", sectors))
    application.add_handler(CommandHandler("overview", overview))
    
    # Start the bot
    logger.info("Starting Market Analysis Bot...")
    print("\n🤖 Market Analysis Bot Started!")
    print("📱 Send /start to your bot on Telegram to begin")
    print("⏹️  Press Ctrl+C to stop\n")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

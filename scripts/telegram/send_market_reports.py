#!/usr/bin/env python3
"""
Market Report Sender
Sends comprehensive market analysis reports to Telegram.
Designed to be run via cron at specific times (e.g., 9:30 AM, 11:45 AM, 2:00 PM).
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.nse_api import NSEClient
from src.chat.user_tracker import UserTracker
from src.utils.telegram_helpers import format_stock_list

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def send_report():
    """Fetch market data and broadcast report to all active users"""
    load_dotenv()
    
    # Configuration
    bot_token = os.getenv('ANALYSIS_TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        logger.error("❌ ANALYSIS_TELEGRAM_BOT_TOKEN not found")
        sys.exit(1)
        
    logger.info("Starting market report broadcast...")
    
    # Get active users
    tracker = UserTracker()
    users = tracker.get_all_users()
    active_users = [u for u in users if u['is_active']]
    
    if not active_users:
        logger.warning("No active users found to send report to.")
        return

    logger.info(f"Broadcasting to {len(active_users)} active users...")
    
    bot = Bot(token=bot_token)
    client = NSEClient()
    limit = 20
    
    try:
        # --- PREPARE CONTENT ONCE ---
        
        # Header (Convert UTC to IST)
        from datetime import timedelta
        ist_time = datetime.now() + timedelta(hours=5, minutes=30)
        current_time = ist_time.strftime("%I:%M %p")
        header = f"🔔 *MARKET UPDATE - {current_time} (IST)*\n━━━━━━━━━━━━━━━━━━━━━━"
        
        # 1. Market Overview
        logger.info("Fetching market data...")
        sectors_df = client.get_sector_performance()
        gainers_df = client.get_top_movers_from_index('NIFTY 500', limit=5, sort_by='gainers')
        losers_df = client.get_top_movers_from_index('NIFTY 500', limit=5, sort_by='losers')
        
        market_msg = "*📊 MARKET SNAPSHOT*\n\n"
        if not sectors_df.empty:
            best = sectors_df.iloc[0]
            worst = sectors_df.iloc[-1]
            market_msg += f"🏆 *Best Sector:* {best['sector'].replace('NIFTY ', '')} ({best['pChange']:+.2f}%)\n"
            market_msg += f"⚠️ *Worst Sector:* {worst['sector'].replace('NIFTY ', '')} ({worst['pChange']:+.2f}%)\n\n"
            
        market_msg += "*Top Gainers:*\n"
        for _, row in gainers_df.head(3).iterrows():
             market_msg += f"🟢 {row['symbol'].replace('.NS','')}: {row['pChange']:+.2f}%\n"
             
        market_msg += "\n*Top Losers:*\n"
        for _, row in losers_df.head(3).iterrows():
             market_msg += f"🔴 {row['symbol'].replace('.NS','')}: {row['pChange']:+.2f}%\n"

        # 2. Top Gainers
        df_gainers = client.get_top_movers_from_index('NIFTY 500', limit=limit, sort_by='gainers')
        msg_gainers = format_stock_list(df_gainers, f"📈 TOP {limit} GAINERS (NIFTY 500)", limit)

        # 3. Top Losers
        df_losers = client.get_top_movers_from_index('NIFTY 500', limit=limit, sort_by='losers')
        msg_losers = format_stock_list(df_losers, f"📉 TOP {limit} LOSERS (NIFTY 500)", limit)

        # 4. Most Active
        df_active = client.get_most_active_by_volume(limit=limit)
        msg_active = format_stock_list(df_active, f"🔥 MOST ACTIVE BY VOLUME (TOP {limit})", limit)

        # 5. 52-Week High
        df_52h = client.get_52week_high(limit=limit)
        msg_52h = format_stock_list(df_52h, f"🚀 52-WEEK HIGHS (TOP {limit})", limit)

        # 6. 52-Week Low
        df_52l = client.get_52week_low(limit=limit)
        msg_52l = format_stock_list(df_52l, f"⚠️ 52-WEEK LOWS (TOP {limit})", limit)

        # 7. Sector Performance
        sector_msg = "*📊 SECTOR PERFORMANCE*\n\n"
        for _, row in sectors_df.iterrows():
            pchange = row['pChange']
            emoji = "🟢" if pchange > 0 else "🔴" if pchange < 0 else "⚪"
            sector_msg += f"{emoji} *{row['sector'].replace('NIFTY ', '')}*: {pchange:+.2f}%\n"

        # List of all messages to send
        messages = [
            header,
            market_msg,
            msg_gainers,
            msg_losers,
            msg_active,
            msg_52h,
            msg_52l,
            sector_msg
        ]

        # --- BROADCAST LOOP ---
        for user in active_users:
            user_id = user['user_id']
            username = user.get('username', 'N/A')
            logger.info(f"Sending report to {username} ({user_id})...")
            
            try:
                for msg in messages:
                    await bot.send_message(chat_id=user_id, text=msg, parse_mode=ParseMode.MARKDOWN)
                    await asyncio.sleep(0.5) # Rate limit protection per message
                
                logger.info(f"✅ Sent to {username}")
                # Sleep between users to be safe
                await asyncio.sleep(1) 
                
            except TelegramError as e:
                logger.error(f"❌ Failed to send to {username} ({user_id}): {e}")
                # Don't stop the loop if one user fails (e.g., blocked bot)
            except Exception as e:
                logger.error(f"❌ Unexpected error for {username}: {e}")

        logger.info("✅ Broadcast complete!")
        
    except Exception as e:
        logger.error(f"Global error: {e}", exc_info=True)

if __name__ == '__main__':
    asyncio.run(send_report())

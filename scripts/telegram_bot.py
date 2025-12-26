#!/usr/bin/env python3
"""
Interactive Telegram Bot Startup Script

Starts the Telegram bot for on-demand stock analysis.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram.ext import (
    Application, 
    CommandHandler, 
    ConversationHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    filters
)
from src.notifications.interactive_bot import InteractiveTradingBot, WAITING_FOR_SYMBOL

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Start the Telegram bot"""
    # Use dedicated analysis bot token
    bot_token = os.getenv('ANALYSIS_TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        logger.error("❌ ANALYSIS_TELEGRAM_BOT_TOKEN not found in environment")
        print("❌ ANALYSIS_TELEGRAM_BOT_TOKEN not found in environment")
        print("Please set ANALYSIS_TELEGRAM_BOT_TOKEN in .env file")
        sys.exit(1)
    
    # Check if bot is enabled
    bot_enabled = os.getenv('INTERACTIVE_BOT_ENABLED', 'true').lower() == 'true'
    if not bot_enabled:
        logger.warning("Interactive bot is disabled (INTERACTIVE_BOT_ENABLED=false)")
        print("⚠️  Interactive bot is disabled")
        print("Set INTERACTIVE_BOT_ENABLED=true in .env to enable")
        sys.exit(0)
    
    logger.info("Starting Analysis Telegram bot...")
    print("🤖 Starting Analysis Telegram bot...")
    print(f"Using ANALYSIS_TELEGRAM_BOT_TOKEN")
    
    # Create application
    app = Application.builder().token(bot_token).build()
    
    # Create bot instance with application reference
    bot = InteractiveTradingBot(application=app)
    
    # Add conversation handler for analysis
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('analyze', bot.analyze_command),
            CallbackQueryHandler(bot.button_callback, pattern='^analyze$')
        ],
        states={
            WAITING_FOR_SYMBOL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_symbol)
            ],
        },
        fallbacks=[CommandHandler('cancel', bot.cancel_command)],
    )
    
    # Add handlers
    app.add_handler(CommandHandler('start', bot.start_command))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('help', bot.help_command))
    app.add_handler(CommandHandler('list', bot.list_command))
    app.add_handler(CommandHandler('workflow', bot.workflow_command))
    
    # Add user management commands
    app.add_handler(CommandHandler('approve', bot.approve_command))
    app.add_handler(CommandHandler('reject', bot.reject_command))
    app.add_handler(CommandHandler('users', bot.users_command))
    app.add_handler(CommandHandler('allusers', bot.allusers_command))
    
    # Add market analysis commands
    app.add_handler(CommandHandler('gainers', bot.gainers_command))
    app.add_handler(CommandHandler('losers', bot.losers_command))
    app.add_handler(CommandHandler('active', bot.active_command))
    app.add_handler(CommandHandler('52high', bot.high52_command))
    app.add_handler(CommandHandler('52low', bot.low52_command))
    app.add_handler(CommandHandler('sectors', bot.sectors_command))
    app.add_handler(CommandHandler('market', bot.market_command))
    
    app.add_handler(CallbackQueryHandler(bot.button_callback))
    
    # Add unknown command handler (must be last)
    app.add_handler(MessageHandler(filters.COMMAND, bot.unknown_command))
    
    # Start bot
    logger.info("Bot is running. Press Ctrl+C to stop.")
    print("✅ Bot is running. Press Ctrl+C to stop.")
    print("Send /start to the bot to begin!")
    
    try:
        app.run_polling(allowed_updates=['message', 'callback_query'])
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        print("\n👋 Bot stopped")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
        print(f"\n❌ Bot error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

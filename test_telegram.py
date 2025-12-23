#!/usr/bin/env python3
"""Test Telegram notification on EC2"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Testing Telegram Notification on EC2")
print("=" * 60)
print()

# Check credentials
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

print("Telegram Configuration:")
print(f"  Bot Token: {'✅ Set' if bot_token else '❌ Not set'}")
print(f"  Chat ID: {'✅ Set' if chat_id else '❌ Not set'}")
print()

if not bot_token or not chat_id:
    print("❌ Telegram credentials not configured")
    print()
    print("To configure:")
    print("1. Edit .env file: nano ~/ztrader/.env")
    print("2. Add:")
    print("   TELEGRAM_BOT_TOKEN=your_bot_token")
    print("   TELEGRAM_CHAT_ID=your_chat_id")
    sys.exit(1)

# Test sending message
try:
    from telegram import Bot
    
    async def send_test_message():
        bot = Bot(token=bot_token)
        
        message = f"""🧪 **Test Message from EC2**

This is a test notification from the trading platform.

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: ✅ Telegram integration working!"""
        
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
        print("✅ Test message sent successfully!")
    
    print("Sending test message...")
    asyncio.run(send_test_message())
    
    print()
    print("=" * 60)
    print("✅ Telegram notification test PASSED")
    print("=" * 60)
    
except ImportError:
    print("❌ python-telegram-bot not installed")
    print()
    print("To install:")
    print("  pip install python-telegram-bot")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Telegram notification FAILED")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

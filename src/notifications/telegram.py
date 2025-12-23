"""
Telegram notification module

Sends trading signals via Telegram bot
"""

import os
import logging
import asyncio
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import telegram, handle if not installed
try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("python-telegram-bot not installed. Install with: pip install python-telegram-bot")


class TelegramNotifier:
    """
    Send trading signals via Telegram
    
    Requires:
    - TELEGRAM_BOT_TOKEN environment variable
    - TELEGRAM_CHAT_ID environment variable
    """
    
    def __init__(self):
        """Initialize Telegram bot"""
        if not TELEGRAM_AVAILABLE:
            raise ImportError("python-telegram-bot not installed")
        
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
        
        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID environment variable not set")
        
        self.bot = Bot(token=self.bot_token)
        logger.info("Telegram bot initialized")
    
    async def send_message(self, message: str, priority: bool = False) -> bool:
        """
        Send a message via Telegram
        
        Args:
            message: Pre-formatted message text
            priority: If True, add priority marker
            
        Returns:
            True if sent successfully
        """
        try:
            # Add priority marker
            if priority:
                message = "⚡ *HIGH CONFIDENCE SIGNAL* ⚡\n\n" + message
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"✅ Sent Telegram message")
            return True
            
        except TelegramError as e:
            logger.error(f"❌ Telegram error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error sending message: {e}")
            return False
    
    async def send_messages(self, messages: List[str], priorities: List[bool] = None) -> Dict:
        """
        Send multiple messages
        
        Args:
            messages: List of pre-formatted message strings
            priorities: Optional list of priority flags for each message
            
        Returns:
            Dictionary with send statistics
        """
        if priorities is None:
            priorities = [False] * len(messages)
        
        sent = 0
        priority_sent = 0
        failed = 0
        
        for i, (message, priority) in enumerate(zip(messages, priorities)):
            if await self.send_message(message, priority=priority):
                sent += 1
                if priority:
                    priority_sent += 1
            else:
                failed += 1
        
        stats = {
            'total_messages': len(messages),
            'sent': sent,
            'priority_sent': priority_sent,
            'failed': failed
        }
        
        logger.info(f"Telegram notifications: {sent} sent ({priority_sent} priority), {failed} failed")
        
        return stats
    
    async def send_summary(self, summary_text: str) -> bool:
        """
        Send a summary message
        
        Args:
            summary_text: Pre-formatted summary text
            
        Returns:
            True if sent successfully
        """
        try:
            await self.send_message(summary_text, priority=False)
            logger.info("✅ Sent daily summary")
            return True
        except Exception as e:
            logger.error(f"❌ Error sending summary: {e}")
            return False

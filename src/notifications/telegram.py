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
    
    def __init__(self, broadcast_to_users: bool = False):
        """
        Initialize Telegram bot
        
        Args:
            broadcast_to_users: If True, send to all active users from DB using ANALYSIS bot.
                               If False, send to single TELEGRAM_CHAT_ID using TELEGRAM bot.
        """
        if not TELEGRAM_AVAILABLE:
            raise ImportError("python-telegram-bot not installed")
        
        self.broadcast_to_users = broadcast_to_users
        
        if broadcast_to_users:
            # Use ANALYSIS bot and fetch users from database
            self.bot_token = os.getenv('ANALYSIS_TELEGRAM_BOT_TOKEN')
            if not self.bot_token:
                raise ValueError("ANALYSIS_TELEGRAM_BOT_TOKEN environment variable not set")
            
            # Import UserTracker to get active users
            try:
                from src.chat.user_tracker import UserTracker
                self.user_tracker = UserTracker()
                self.chat_id = None  # Will use multiple user IDs
                logger.info("Telegram bot initialized in BROADCAST mode (all active users)")
            except ImportError:
                raise ImportError("UserTracker not available for broadcast mode")
        else:
            # Use regular bot and single chat ID
            self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            if not self.bot_token:
                raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
            
            if not self.chat_id:
                raise ValueError("TELEGRAM_CHAT_ID environment variable not set")
            
            self.user_tracker = None
            logger.info("Telegram bot initialized in SINGLE CHAT mode")
        
        self.bot = Bot(token=self.bot_token)
    
    async def send_message(self, message: str, priority: bool = False) -> bool:
        """
        Send a message via Telegram
        
        Args:
            message: Pre-formatted message text
            priority: If True, add priority marker
            
        Returns:
            True if sent successfully (or if all broadcasts succeeded)
        """
        try:
            # Add priority marker
            if priority:
                message = "⚡ *HIGH CONFIDENCE SIGNAL* ⚡\n\n" + message
            
            if self.broadcast_to_users:
                # Broadcast to all active users
                users = self.user_tracker.get_all_users()
                active_users = [u for u in users if u['is_active']]
                
                if not active_users:
                    logger.warning("No active users to broadcast to")
                    return False
                
                success_count = 0
                for user in active_users:
                    try:
                        await self.bot.send_message(
                            chat_id=user['telegram_user_id'],
                            text=message,
                            parse_mode='Markdown'
                        )
                        success_count += 1
                    except TelegramError as e:
                        logger.error(f"Failed to send to user {user['telegram_user_id']}: {e}")
                
                logger.info(f"✅ Broadcast to {success_count}/{len(active_users)} users")
                return success_count > 0
            else:
                # Send to single chat
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

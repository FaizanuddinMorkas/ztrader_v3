"""
Interactive Telegram Bot for On-Demand Stock Analysis

Provides interactive conversation-based interface for users to request
AI-powered stock analysis via Telegram.
"""

import os
import logging
import subprocess
import yfinance as yf
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Optional
from datetime import datetime

from src.analysis.on_demand_analyzer import OnDemandAnalyzer
from src.data.storage import InstrumentsDB
from src.chat.user_tracker import UserTracker

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_SYMBOL = 1


class InteractiveTradingBot:
    """
    Interactive Telegram bot for on-demand analysis
    """
    
    def __init__(self, application=None):
        """Initialize the bot with analyzer, database, user tracker, and SQL agent"""
        self.analyzer = OnDemandAnalyzer()
        self.db = InstrumentsDB()
        self.user_tracker = UserTracker()
        self.application = application  # Store application for sending messages
        
        # Initialize SQL Agent for natural language screening
        try:
            from src.chat.sql_agent import StockScreenerSQLAgent
            self.sql_agent = StockScreenerSQLAgent()
            logger.info("SQL Agent initialized successfully")
        except Exception as e:
            logger.warning(f"SQL Agent initialization failed: {e}")
            self.sql_agent = None
        
        logger.info("InteractiveTradingBot initialized with user tracking")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - Register user and check approval status"""
        user = update.effective_user
        
        # Register user (inactive by default)
        self.user_tracker.register_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=False
        )
        
        # Check if user is already active
        if self.user_tracker.is_user_active(user.id):
            # Active user - show main menu
            keyboard = [
                [InlineKeyboardButton("📊 Analyze Stock", callback_data='analyze')],
                [InlineKeyboardButton("📋 List Stocks", callback_data='list')],
                [InlineKeyboardButton("ℹ️ Help", callback_data='help')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            welcome_msg = (
                "🤖 *Welcome back to AI Trading Bot!*\n\n"
                "Get comprehensive AI-powered stock analysis on-demand.\n\n"
                "What would you like to do?"
            )
            
            await update.message.reply_text(
                welcome_msg,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            # Inactive user - pending approval
            await update.message.reply_text(
                "👋 *Welcome to AI Stock Screener Bot!*\n\n"
                "Your access request has been submitted.\n"
                "You'll be notified once approved by admin.\n\n"
                "Thank you for your patience!",
                parse_mode='Markdown'
            )
            
            # Notify admin about new user
            await self._notify_admin_new_user(user)
    
    async def _check_user_access(self, update: Update) -> bool:
        """
        Check if user has access to bot features
        Returns True if user is active, False otherwise
        """
        user_id = update.effective_user.id
        
        if not self.user_tracker.is_user_active(user_id):
            # Get the message object (works for both regular messages and callback queries)
            message = update.message or update.callback_query.message
            
            await message.reply_text(
                "⚠️ *Access Pending*\n\n"
                "Your account is awaiting admin approval.\n"
                "You'll be notified once activated.\n\n"
                "Please contact the admin if you've been waiting for a while.",
                parse_mode='Markdown'
            )
            return False
        return True
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command - Active users only"""
        # Check user access
        if not await self._check_user_access(update):
            return
        
        # Check if symbol was provided as argument
        if context.args:
            # Direct mode: /analyze SYMBOL
            symbol_input = context.args[0].strip().upper()
            
            # Auto-add .NS if not present
            if not symbol_input.endswith('.NS') and not symbol_input.endswith('.BO'):
                symbol = f"{symbol_input}.NS"
            else:
                symbol = symbol_input.replace('.BO', '.NS')
            
            # Process the analysis directly
            await self._process_analysis(update, symbol, is_button=False)
            return
        
        # Conversational mode: Ask for symbol
        msg = (
            "📊 *Stock Analysis*\n\n"
            "Please send the stock symbol you want to analyze.\n\n"
            "*Examples:*\n"
            "• RELIANCE or RELIANCE.NS\n"
            "• TCS or TCS.NS\n"
            "• INFY or INFY.NS\n\n"
            "Or send /cancel to cancel."
        )
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        return WAITING_FOR_SYMBOL
    
    async def _process_analysis(self, update: Update, symbol: str, is_button: bool = False):
        """Process stock analysis (shared by command and button)"""
        import time
        start_time = time.time()
        
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        # Check if symbol exists
        if not self._symbol_exists(symbol):
            message = update.callback_query.message if is_button else update.message
            await message.reply_text(
                f"❌ *Symbol not found: {symbol}*\n\n"
                "Could not find this symbol on NSE.\n\n"
                "Please check the symbol and try again.",
                parse_mode='Markdown'
            )
            return
        
        # Send processing message
        message = update.callback_query.message if is_button else update.message
        processing_msg = await message.reply_text(
            f"⏳ *Analyzing {symbol}...*\n\n"
            "Downloading data and running AI analysis.\n"
            "This may take 30-60 seconds.\n\n"
            "Please wait...",
            parse_mode='Markdown'
        )
        
        try:
            # Perform analysis
            logger.info(f"User {username} ({user_id}) requested analysis for {symbol}")
            analysis = self.analyzer.analyze_symbol(symbol)
            
            # Delete processing message
            await processing_msg.delete()
            
            # Send summary first
            summary = self.analyzer.format_summary(analysis)
            await message.reply_text(summary, parse_mode='Markdown')
            
            # Send detailed sections
            sections = self.analyzer.format_detailed_sections(analysis)
            for section in sections:
                await message.reply_text(section, parse_mode='Markdown')
            
            logger.info(f"Analysis sent successfully for {symbol} ({len(sections)} sections)")
            
            # Log successful analysis
            response_time = int((time.time() - start_time) * 1000)
            query_text = f'/analyze {symbol}' + (' (button)' if is_button else '')
            self.user_tracker.log_query(
                user_id=user_id,
                query_type='analyze',
                query_text=query_text,
                response_time_ms=response_time,
                success=True,
                username=username
            )
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}", exc_info=True)
            await processing_msg.edit_text(
                f"❌ *Error analyzing {symbol}*\n\n"
                f"Error: {str(e)}\n\n"
                "Please try again or contact support.",
                parse_mode='Markdown'
            )
            
            # Log failed analysis
            response_time = int((time.time() - start_time) * 1000)
            query_text = f'/analyze {symbol}' + (' (button)' if is_button else '')
            self.user_tracker.log_query(
                user_id=user_id,
                query_type='analyze',
                query_text=query_text,
                response_time_ms=response_time,
                success=False,
                error_message=str(e),
                username=username
            )
    
    async def handle_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle symbol input from user"""
        import time
        start_time = time.time()
        
        user_id = update.effective_user.id
        username = update.effective_user.username
        user_input = update.message.text.strip().upper()
        
        # Auto-add .NS if not present (always use NSE)
        if not user_input.endswith('.NS') and not user_input.endswith('.BO'):
            symbol = f"{user_input}.NS"
        else:
            # Convert .BO to .NS
            symbol = user_input.replace('.BO', '.NS')
        
        # Check if symbol exists in our database or yfinance
        if not self._symbol_exists(symbol):
            await update.message.reply_text(
                f"❌ *Symbol not found: {symbol}*\n\n"
                "Could not find this symbol on NSE.\n\n"
                "Please check the symbol and try again, or use /list to see Nifty 100 stocks.",
                parse_mode='Markdown'
            )
            return WAITING_FOR_SYMBOL
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            f"⏳ *Analyzing {symbol}...*\n\n"
            "Downloading data and running AI analysis.\n"
            "This may take 30-60 seconds.\n\n"
            "Please wait...",
            parse_mode='Markdown'
        )
        
        try:
            # Perform analysis
            logger.info(f"User {username} ({user_id}) requested analysis for {symbol}")
            analysis = self.analyzer.analyze_symbol(symbol)
            
            # Delete processing message
            await processing_msg.delete()
            
            # Send summary first (quick overview)
            summary = self.analyzer.format_summary(analysis)
            await update.message.reply_text(summary, parse_mode='Markdown')
            
            # Send detailed sections one by one for interactive feel
            sections = self.analyzer.format_detailed_sections(analysis)
            for section in sections:
                await update.message.reply_text(section, parse_mode='Markdown')
            
            logger.info(f"Analysis sent successfully for {symbol} ({len(sections)} sections)")
            
            # Log successful analysis
            response_time = int((time.time() - start_time) * 1000)
            self.user_tracker.log_query(
                user_id=user_id,
                query_type='analyze',
                query_text=f'/analyze {symbol}',
                response_time_ms=response_time,
                success=True,
                username=username
            )
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}", exc_info=True)
            await processing_msg.edit_text(
                f"❌ *Error analyzing {symbol}*\n\n"
                f"Error: {str(e)}\n\n"
                "Please try again or contact support.",
                parse_mode='Markdown'
            )
            
            # Log failed analysis
            response_time = int((time.time() - start_time) * 1000)
            self.user_tracker.log_query(
                user_id=user_id,
                query_type='analyze',
                query_text=f'/analyze {symbol}',
                response_time_ms=response_time,
                success=False,
                error_message=str(e),
                username=username
            )
        
        # End conversation
        from telegram.ext import ConversationHandler
        return ConversationHandler.END
    
    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list command to show all stocks with clickable buttons - Active users only"""
        # Check user access
        if not await self._check_user_access(update):
            return
        
        # Get message object (works for both regular messages and callback queries)
        message = update.message or update.callback_query.message
        
        try:
            instruments = self.db.get_nifty_100()  # Returns list of strings
            
            # Create a concise list (remove .NS suffix for display)
            symbols = [symbol.replace('.NS', '') for symbol in instruments]
            symbols.sort()
            
            # Telegram allows max ~100 buttons per message, so we'll send in batches
            # Show 30 stocks per message, 3 per row
            batch_size = 30
            total_batches = (len(symbols) + batch_size - 1) // batch_size
            
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, len(symbols))
                batch_symbols = symbols[start_idx:end_idx]
                
                # Create inline keyboard for this batch
                keyboard = []
                for i in range(0, len(batch_symbols), 3):  # 3 per row
                    row = []
                    for symbol in batch_symbols[i:i+3]:
                        row.append(InlineKeyboardButton(
                            symbol, 
                            callback_data=f'analyze_{symbol}'
                        ))
                    keyboard.append(row)
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Create message for this batch
                if batch_num == 0:
                    msg_text = f"📋 *Nifty 100 Stocks* (Part {batch_num + 1}/{total_batches})\n\n"
                    msg_text += f"Total: {len(symbols)} stocks\n\n"
                    msg_text += "👆 *Click any stock to analyze*"
                else:
                    msg_text = f"📋 *Nifty 100 Stocks* (Part {batch_num + 1}/{total_batches})"
                
                await message.reply_text(
                    msg_text, 
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            
            # Send final message with instructions
            final_msg = "\n💡 *Tip:* Use /analyze to search for any NSE stock (not just Nifty 100)"
            await message.reply_text(final_msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in list_command: {e}")
            await message.reply_text(
                "❌ Error fetching stock list. Please try again."
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_msg = (
            "ℹ️ *AI Trading Bot Help*\n\n"
            "*📊 Stock Analysis Commands:*\n"
            "• /start - Start the bot\n"
            "• /analyze - Analyze a stock (AI-powered)\n"
            "• /list - Show supported stocks\n"
            "• /cancel - Cancel current operation\n\n"
            "*📈 Market Screener Commands:*\n"
            "• /gainers [limit] - Top gainers (Nifty 500)\n"
            "• /losers [limit] - Top losers (Nifty 500)\n"
            "• /active [limit] - Most active by volume\n"
            "• /52high [limit] - Stocks at 52-week high\n"
            "• /52low [limit] - Stocks at 52-week low\n"
            "• /sectors - All sector performance\n"
            "• /market - Complete market overview\n\n"
            "*💡 Examples:*\n"
            "`/gainers 5` - Top 5 gainers\n"
            "`/losers 10` - Top 10 losers\n"
            "`/active` - Top 20 most active (default)\n"
            "`/52high 5` - Top 5 at 52W high\n"
            "`/sectors` - All sectors\n"
            "`/market` - Quick market pulse\n\n"
            "*🔍 AI Stock Analysis:*\n"
            "1. Send /analyze command\n"
            "2. Enter stock symbol (e.g., RELIANCE)\n"
            "3. Wait for AI analysis (30-60 seconds)\n"
            "4. Review comprehensive report\n\n"
            "*📋 Analysis Includes:*\n"
            "📈 Technical Analysis (RSI, MACD, Support/Resistance)\n"
            "💼 Fundamental Analysis (P/E, ROE, Debt/Equity)\n"
            "📰 News Sentiment (Last 7 days)\n"
            "🤖 AI Recommendation (Entry, Stop Loss, Targets)\n\n"
            "*📊 Market Screener Features:*\n"
            "• Real-time NSE data\n"
            "• Nifty 500 coverage\n"
            "• 16 sectoral indices\n"
            "• Default limit: 20 stocks\n"
            "• Maximum limit: 20 stocks\n\n"
            "*🎯 Supported Stocks:*\n"
            "All NSE stocks (use /list to see Nifty 100)\n\n"
            "⚠️ *Disclaimer:* This is not financial advice. "
            "Always do your own research before investing."
        )
        
        await update.message.reply_text(help_msg, parse_mode='Markdown')
    
    async def workflow_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /workflow command - run daily workflow (admin only)"""
        
        # Get admin user ID from environment
        admin_user_id = os.getenv('ADMIN_TELEGRAM_USER_ID')
        
        if not admin_user_id:
            await update.message.reply_text(
                "❌ Workflow command is not configured.\n"
                "Please set ADMIN_TELEGRAM_USER_ID in .env file."
            )
            return
        
        # Check if user is admin
        user_id = str(update.effective_user.id)
        if user_id != admin_user_id:
            logger.warning(f"Unauthorized workflow attempt by user {user_id}")
            await update.message.reply_text(
                "❌ You are not authorized to run this command."
            )
            return
        
        # Send confirmation message
        status_msg = await update.message.reply_text(
            "🚀 *Starting Daily Workflow*\n\n"
            "This will run:\n"
            "1. Data synchronization\n"
            "2. Signal generation\n"
            "3. AI analysis\n"
            "4. Telegram notifications\n\n"
            "⏳ Starting...",
            parse_mode='Markdown'
        )
        
        try:
            # Run the daily workflow script with real-time output
            logger.info(f"Admin user {user_id} triggered daily workflow")
            
            # Get the project root directory dynamically
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            process = subprocess.Popen(
                ['python', 'scripts/daily_workflow.py'],
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Stream output and send updates
            output_lines = []
            last_update_time = 0
            
            for line in process.stdout:
                output_lines.append(line.strip())
                
                # Print to terminal for visibility
                print(f"[WORKFLOW] {line.strip()}")
                
                # Send update every 5 seconds or on important lines
                import time
                current_time = time.time()
                is_important = any(keyword in line.lower() for keyword in 
                    ['starting', 'completed', 'error', 'success', 'failed', 'analyzing'])
                
                if (current_time - last_update_time > 5) or is_important:
                    # Get last 10 lines for context
                    recent_output = '\n'.join(output_lines[-10:])
                    
                    # Escape Markdown special characters to prevent parsing errors
                    escaped_output = recent_output.replace('`', '\\`').replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]')
                    
                    await status_msg.edit_text(
                        f"🚀 *Daily Workflow Running*\n\n"
                        f"```\n{escaped_output[-500:]}\n```",  # Limit to 500 chars
                        parse_mode='Markdown'
                    )
                    last_update_time = current_time
            
            # Wait for process to complete
            return_code = process.wait(timeout=600)
            
            # Send final result
            if return_code == 0:
                await update.message.reply_text(
                    "✅ *Daily Workflow Completed Successfully!*\n\n"
                    "Check your signals channel for updates.",
                    parse_mode='Markdown'
                )
                logger.info("Daily workflow completed successfully")
            else:
                final_output = '\n'.join(output_lines[-20:])
                # Escape special characters
                escaped_final = final_output.replace('`', '\\`').replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]')
                await update.message.reply_text(
                    f"❌ *Workflow Failed*\n\n"
                    f"Exit code: {return_code}\n\n"
                    f"```\n{escaped_final[-500:]}\n```",
                    parse_mode='Markdown'
                )
                logger.error(f"Daily workflow failed with code {return_code}")
                
        except subprocess.TimeoutExpired:
            process.kill()
            await update.message.reply_text(
                "⏱️ *Workflow Timeout*\n\n"
                "The workflow took longer than 10 minutes.\n"
                "Please check the logs manually.",
                parse_mode='Markdown'
            )
            logger.warning("Daily workflow timed out")
            
        except Exception as e:
            # Escape error message
            error_msg = str(e).replace('`', '\\`').replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]')
            await update.message.reply_text(
                f"❌ *Error Running Workflow*\n\n"
                f"Error: {error_msg}",
                parse_mode='Markdown'
            )
            logger.error(f"Error running workflow: {e}", exc_info=True)
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command"""
        await update.message.reply_text(
            "❌ Operation cancelled.\n\n"
            "Use /start to begin again."
        )
        
        from telegram.ext import ConversationHandler
        return ConversationHandler.END
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        # Check user access for analyze and list buttons
        if query.data in ['analyze', 'list'] or query.data.startswith('analyze_'):
            user_id = update.effective_user.id
            if not self.user_tracker.is_user_active(user_id):
                await query.message.reply_text(
                    "⚠️ *Access Pending*\n\n"
                    "Your account is awaiting admin approval.\n"
                    "You'll be notified once activated.",
                    parse_mode='Markdown'
                )
                return
        
        # Handle stock analysis buttons
        if query.data.startswith('analyze_'):
            symbol = query.data.replace('analyze_', '')
            symbol_ns = f"{symbol}.NS"
            
            # Use shared analysis method
            await self._process_analysis(update, symbol_ns, is_button=True)
        
        # Handle "show all stocks" button
        elif query.data == 'list_all':
            try:
                instruments = self.db.get_nifty_100()
                symbols = [symbol.replace('.NS', '') for symbol in instruments]
                symbols.sort()
                
                # Split into chunks
                chunk_size = 15
                chunks = [symbols[i:i+chunk_size] for i in range(0, len(symbols), chunk_size)]
                
                message = "📋 *All Nifty 100 Stocks*\n\n"
                message += f"Total: {len(symbols)} stocks\n\n"
                
                for chunk in chunks:
                    message += ", ".join(chunk) + "\n"
                
                message += "\n💡 Use /list to see clickable buttons\n"
                message += "💡 Use /analyze to search for any NSE stock"
                
                await query.message.reply_text(message, parse_mode='Markdown')
                
            except Exception as e:
                logger.error(f"Error showing all stocks: {e}")
                await query.message.reply_text("❌ Error fetching stock list.")
        
        # Handle original buttons
        elif query.data == 'analyze':
            await query.message.reply_text(
                "📊 *Stock Analysis*\n\n"
                "Please send the stock symbol you want to analyze.\n\n"
                "*Examples:* RELIANCE, TCS, INFY",
                parse_mode='Markdown'
            )
            return WAITING_FOR_SYMBOL
        
        elif query.data == 'list':
            await self.list_command(update, context)
        
        elif query.data == 'help':
            await self.help_command(update, context)
    
    def _symbol_exists(self, symbol: str) -> bool:
        """
        Check if symbol exists in instruments database or validate via yfinance
        If validated via yfinance, automatically add to database
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            
        Returns:
            True if symbol exists in database or is valid on yfinance, False otherwise
        """
        try:
            logger.info(f"Checking symbol existence for: {symbol}")
            
            # First check all active instruments in database
            instruments_df = self.db.get_all_active()  # Returns DataFrame
            
            if instruments_df is not None and not instruments_df.empty:
                db_symbols = instruments_df['symbol'].tolist()
                logger.info(f"Database has {len(db_symbols)} active instruments")
                
                if symbol in db_symbols:
                    logger.info(f"✓ {symbol} found in instruments database")
                    return True
            else:
                logger.warning("Database returned empty or None")
                db_symbols = []
            
            logger.info(f"✗ {symbol} not in database")
            
            # If not in database, try yfinance validation (NSE only)
            logger.info(f"Attempting yfinance validation for {symbol}...")
            
            # Ensure it's an NSE symbol
            if not symbol.endswith('.NS'):
                logger.warning(f"✗ {symbol} is not an NSE symbol (doesn't end with .NS)")
                return False
            
            logger.info(f"Fetching data from yfinance for {symbol}...")
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            logger.info(f"yfinance returned {len(info) if info else 0} fields for {symbol}")
            if info:
                logger.info(f"Symbol: {info.get('symbol')}, Exchange: {info.get('exchange')}, Currency: {info.get('currency')}")
            
            # Check if we got valid data and it's actually an NSE stock
            # Valid NSE stocks should have basic info like symbol, exchange, currency
            if (info and 
                len(info) > 5 and 
                info.get('symbol') and
                (info.get('exchange') == 'NSI' or info.get('currency') == 'INR')):
                logger.info(f"✓ {symbol} validated via yfinance as NSE stock")
                
                # Add to database for future quick access
                try:
                    name = info.get('longName') or info.get('shortName') or symbol.replace('.NS', '')
                    sector = info.get('sector', 'Unknown')
                    industry = info.get('industry', 'Unknown')
                    
                    self.db.insert_instrument(
                        symbol=symbol,
                        name=name,
                        sector=sector,
                        industry=industry,
                        is_nifty_50=False,
                        is_nifty_100=False
                    )
                    logger.info(f"✓ Added {symbol} to database: {name} ({sector})")
                except Exception as db_error:
                    logger.warning(f"Could not add {symbol} to database: {db_error}")
                    # Don't fail validation if DB insert fails
                
                return True
            
            logger.warning(f"✗ {symbol} not found or not a valid NSE stock on yfinance")
            return False
            
        except Exception as e:
            logger.error(f"✗ Error checking symbol existence for {symbol}: {e}", exc_info=True)
            return False
    
    def _split_message(self, text: str, max_length: int = 4000) -> list:
        """
        Split long message into chunks
        
        Args:
            text: Message text
            max_length: Maximum length per chunk
            
        Returns:
            List of message chunks
        """
        if len(text) <= max_length:
            return [text]
        
        # Split by sections (---) first
        sections = text.split('\n---\n')
        chunks = []
        current_chunk = ""
        
        for section in sections:
            if len(current_chunk) + len(section) + 6 <= max_length:
                if current_chunk:
                    current_chunk += "\n---\n"
                current_chunk += section
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = section
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    # ========================================================================
    # User Management Commands
    # ========================================================================
    
    async def _notify_admin_new_user(self, user):
        """Notify admin about new user registration via workflow bot"""
        admin_id = os.getenv('ADMIN_TELEGRAM_USER_ID')
        workflow_bot_token = os.getenv('WORKFLOW_TELEGRAM_BOT_TOKEN')
        
        if not admin_id or not workflow_bot_token:
            logger.warning("Admin notification skipped - ADMIN_TELEGRAM_USER_ID or WORKFLOW_TELEGRAM_BOT_TOKEN not set")
            return
        
        try:
            from telegram import Bot
            
            admin_id = int(admin_id)
            # Escape special characters for Markdown
            username = (user.username or 'N/A').replace('_', '\\_')
            first_name = (user.first_name or '').replace('_', '\\_')
            last_name = (user.last_name or '').replace('_', '\\_')
            
            msg = (
                f"🆕 *New User Registration*\n\n"
                f"User ID: {user.id}\n"
                f"Username: @{username}\n"
                f"Name: {first_name} {last_name}\n\n"
                f"Approve: /approve {user.id}\n"
                f"Reject: /reject {user.id}"
            )
            
            # Send via workflow bot
            workflow_bot = Bot(token=workflow_bot_token)
            await workflow_bot.send_message(
                chat_id=admin_id,
                text=msg,
                parse_mode='Markdown'
            )
            logger.info(f"Notified admin about new user via workflow bot: {user.id}")
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}", exc_info=True)
    
    async def approve_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin only: Approve user"""
        admin_id = os.getenv('ADMIN_TELEGRAM_USER_ID')
        
        if not admin_id or str(update.effective_user.id) != admin_id:
            logger.warning(f"Unauthorized approve attempt by user {update.effective_user.id}")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /approve <user_id>")
            return
        
        try:
            user_id = int(context.args[0])
            
            # Activate user
            success = self.user_tracker.activate_user(user_id)
            
            if success:
                await update.message.reply_text(f"✅ User {user_id} approved!")
                
                # Notify user
                try:
                    await self.application.bot.send_message(
                        chat_id=user_id,
                        text=(
                            "🎉 *Access Approved!*\n\n"
                            "You can now use the stock screener.\n"
                            "Send /start to get started!"
                        ),
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Failed to notify user {user_id}: {e}")
            else:
                await update.message.reply_text(f"❌ Failed to approve user {user_id}")
                
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID")
        except Exception as e:
            logger.error(f"Error approving user: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def reject_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin only: Reject user"""
        admin_id = os.getenv('ADMIN_TELEGRAM_USER_ID')
        
        if not admin_id or str(update.effective_user.id) != admin_id:
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /reject <user_id>")
            return
        
        try:
            user_id = int(context.args[0])
            
            # Deactivate user
            success = self.user_tracker.deactivate_user(user_id)
            
            if success:
                await update.message.reply_text(f"❌ User {user_id} rejected/deactivated!")
            else:
                await update.message.reply_text(f"❌ Failed to reject user {user_id}")
                
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID")
        except Exception as e:
            logger.error(f"Error rejecting user: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin only: List pending users"""
        admin_id = os.getenv('ADMIN_TELEGRAM_USER_ID')
        
        if not admin_id or str(update.effective_user.id) != admin_id:
            return
        
        try:
            pending = self.user_tracker.get_pending_users()
            
            if not pending:
                await update.message.reply_text("No pending users.")
                return
            
            msg = "👥 *Pending Users*\n\n"
            for user in pending:
                # Escape special characters
                name = user['name'].replace('_', '\\_')
                username = user['username'].replace('_', '\\_')
                msg += f"• {name} (@{username}) - ID: {user['user_id']}\n"
                msg += f"  Registered: {user['first_seen'].strftime('%Y-%m-%d %H:%M')}\n\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error getting pending users: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def allusers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin only: List all users"""
        admin_id = os.getenv('ADMIN_TELEGRAM_USER_ID')
        
        if not admin_id or str(update.effective_user.id) != admin_id:
            return
        
        try:
            all_users = self.user_tracker.get_all_users()
            
            if not all_users:
                await update.message.reply_text("No users registered yet.")
                return
            
            # Separate active and inactive
            active_users = [u for u in all_users if u['is_active']]
            inactive_users = [u for u in all_users if not u['is_active']]
            
            msg = f"👥 *All Registered Users* ({len(all_users)} total)\n\n"
            
            if active_users:
                msg += f"✅ *Active Users* ({len(active_users)}):\n"
                for user in active_users[:10]:  # Limit to 10
                    name = user['name'].replace('_', '\\_')
                    username = user['username'].replace('_', '\\_')
                    msg += f"• {name} (@{username}) - ID: {user['user_id']}\n"
                    msg += f"  Last seen: {user['last_seen'].strftime('%Y-%m-%d %H:%M')}\n"
                if len(active_users) > 10:
                    msg += f"  ... and {len(active_users) - 10} more\n"
                msg += "\n"
            
            if inactive_users:
                msg += f"⏳ *Pending Approval* ({len(inactive_users)}):\n"
                for user in inactive_users[:10]:  # Limit to 10
                    name = user['name'].replace('_', '\\_')
                    username = user['username'].replace('_', '\\_')
                    msg += f"• {name} (@{username}) - ID: {user['user_id']}\n"
                if len(inactive_users) > 10:
                    msg += f"  ... and {len(inactive_users) - 10} more\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error getting all users: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")

    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user statistics"""
        user_id = update.effective_user.id
        
        try:
            stats = self.user_tracker.get_user_stats(user_id)
            
            if stats:
                msg = (
                    f"📊 *Your Usage Statistics*\n\n"
                    f"Total Queries: {stats['total_queries']}\n"
                    f"Screen Queries: {stats['screen_queries']}\n"
                    f"Analysis Queries: {stats['analyze_queries']}\n"
                    f"Avg Response Time: {stats['avg_response_time']:.0f}ms\n"
                    f"Failed Queries: {stats['failed_queries']}\n"
                    f"Last Query: {stats['last_query_time'].strftime('%Y-%m-%d %H:%M')}"
                )
            else:
                msg = "No usage data yet. Start using /analyze!"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}", exc_info=True)
            await update.message.reply_text("❌ Error retrieving statistics")
    
    # ========================================================================
    # Market Analysis Commands
    # ========================================================================
    
    async def gainers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get top gainers from Nifty 500"""
        if not await self._check_user_access(update):
            return
        
        import time
        start_time = time.time()
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        try:
            from src.data.nse_api import NSEClient
            
            limit = int(context.args[0]) if context.args else 20
            limit = min(limit, 20)
            
            await update.message.reply_text("🔍 Fetching top gainers...")
            
            client = NSEClient()
            df = client.get_top_movers_from_index('NIFTY 500', limit=limit, sort_by='gainers')
            
            message = self._format_stock_list(df, f"📈 TOP {limit} GAINERS (NIFTY 500)", limit)
            await update.message.reply_text(message, parse_mode='Markdown')
            
            # Log successful query
            response_time = int((time.time() - start_time) * 1000)
            self.user_tracker.log_query(
                user_id=user_id,
                query_type='market',
                query_text=f'/gainers {limit}',
                response_time_ms=response_time,
                success=True,
                username=username
            )
            
        except Exception as e:
            logger.error(f"Error in gainers command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
            
            # Log failed query
            response_time = int((time.time() - start_time) * 1000)
            self.user_tracker.log_query(
                user_id=user_id,
                query_type='market',
                query_text=f'/gainers',
                response_time_ms=response_time,
                success=False,
                error_message=str(e),
                username=username
            )
    
    async def losers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get top losers from Nifty 500"""
        if not await self._check_user_access(update):
            return
        
        import time
        start_time = time.time()
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        try:
            from src.data.nse_api import NSEClient
            
            limit = int(context.args[0]) if context.args else 20
            limit = min(limit, 20)
            
            await update.message.reply_text("🔍 Fetching top losers...")
            
            client = NSEClient()
            df = client.get_top_movers_from_index('NIFTY 500', limit=limit, sort_by='losers')
            
            message = self._format_stock_list(df, f"📉 TOP {limit} LOSERS (NIFTY 500)", limit)
            await update.message.reply_text(message, parse_mode='Markdown')
            
            # Log successful query
            response_time = int((time.time() - start_time) * 1000)
            self.user_tracker.log_query(user_id=user_id, query_type='market', query_text=f'/losers {limit}', response_time_ms=response_time, success=True,
                username=username
            )
            
        except Exception as e:
            logger.error(f"Error in losers command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
            response_time = int((time.time() - start_time) * 1000)
            self.user_tracker.log_query(user_id=user_id, query_type='market', query_text=f'/losers', response_time_ms=response_time, success=False, error_message=str(e),
                username=username
            )
    
    async def active_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get most active stocks by volume"""
        if not await self._check_user_access(update):
            return
        
        import time
        start_time = time.time()
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        try:
            from src.data.nse_api import NSEClient
            
            limit = int(context.args[0]) if context.args else 20
            limit = min(limit, 20)
            
            await update.message.reply_text("🔍 Fetching most active stocks...")
            
            client = NSEClient()
            df = client.get_most_active_by_volume(limit=limit)
            
            message = self._format_stock_list(df, f"🔥 MOST ACTIVE BY VOLUME - TOP {limit}", limit)
            await update.message.reply_text(message, parse_mode='Markdown')
            
            response_time = int((time.time() - start_time) * 1000)
            self.user_tracker.log_query(user_id=user_id, query_type='market', query_text=f'/active {limit}', response_time_ms=response_time, success=True,
                username=username
            )
            
        except Exception as e:
            logger.error(f"Error in active command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
            response_time = int((time.time() - start_time) * 1000)
            self.user_tracker.log_query(user_id=user_id, query_type='market', query_text=f'/active', response_time_ms=response_time, success=False, error_message=str(e),
                username=username
            )
    
    async def high52_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get stocks at 52-week high"""
        if not await self._check_user_access(update):
            return
        
        import time
        start_time = time.time()
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        try:
            from src.data.nse_api import NSEClient
            
            limit = int(context.args[0]) if context.args else 20
            limit = min(limit, 20)
            
            await update.message.reply_text("🔍 Fetching 52-week highs...")
            
            client = NSEClient()
            df = client.get_52week_high(limit=limit)
            
            message = self._format_stock_list(df, f"🚀 STOCKS AT 52-WEEK HIGH - TOP {limit}", limit)
            await update.message.reply_text(message, parse_mode='Markdown')
            
            response_time = int((time.time() - start_time) * 1000)
            self.user_tracker.log_query(user_id=user_id, query_type='market', query_text=f'/52high {limit}', response_time_ms=response_time, success=True,
                username=username
            )
            
        except Exception as e:
            logger.error(f"Error in 52high command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
            response_time = int((time.time() - start_time) * 1000)
            self.user_tracker.log_query(user_id=user_id, query_type='market', query_text=f'/52high', response_time_ms=response_time, success=False, error_message=str(e),
                username=username
            )
    
    async def low52_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get stocks at 52-week low"""
        if not await self._check_user_access(update):
            return
        
        import time
        start_time = time.time()
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        try:
            from src.data.nse_api import NSEClient
            
            limit = int(context.args[0]) if context.args else 20
            limit = min(limit, 20)
            
            await update.message.reply_text("🔍 Fetching 52-week lows...")
            
            client = NSEClient()
            df = client.get_52week_low(limit=limit)
            
            message = self._format_stock_list(df, f"⚠️ STOCKS AT 52-WEEK LOW - TOP {limit}", limit)
            await update.message.reply_text(message, parse_mode='Markdown')
            
            response_time = int((time.time() - start_time) * 1000)
            self.user_tracker.log_query(user_id=user_id, query_type='market', query_text=f'/52low {limit}', response_time_ms=response_time, success=True,
                username=username
            )
            
        except Exception as e:
            logger.error(f"Error in 52low command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
            response_time = int((time.time() - start_time) * 1000)
            self.user_tracker.log_query(user_id=user_id, query_type='market', query_text=f'/52low', response_time_ms=response_time, success=False, error_message=str(e),
                username=username
            )
    
    async def sectors_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get sector performance"""
        if not await self._check_user_access(update):
            return
        
        import time
        start_time = time.time()
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        try:
            from src.data.nse_api import NSEClient
            
            await update.message.reply_text("🔍 Fetching sector performance...")
            
            client = NSEClient()
            df = client.get_sector_performance()
            
            if df.empty:
                await update.message.reply_text("*SECTOR PERFORMANCE*\n\nNo data available.", parse_mode='Markdown')
                return
            
            message = "*📊 SECTOR PERFORMANCE*\n\n"
            
            for idx, row in df.iterrows():
                sector = row.get('sector', 'N/A')
                pchange = row.get('pChange', 0)
                
                emoji = "🟢" if pchange > 0 else "🔴" if pchange < 0 else "⚪"
                sector_short = sector.replace('NIFTY ', '')
                
                message += f"{emoji} *{sector_short}*: {pchange:+.2f}%\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
            response_time = int((time.time() - start_time) * 1000)
            self.user_tracker.log_query(user_id=user_id, query_type='market', query_text='/sectors', response_time_ms=response_time, success=True,
                username=username
            )
            
        except Exception as e:
            logger.error(f"Error in sectors command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
            response_time = int((time.time() - start_time) * 1000)
            self.user_tracker.log_query(user_id=user_id, query_type='market', query_text='/sectors', response_time_ms=response_time, success=False, error_message=str(e),
                username=username
            )
    
    async def market_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get market overview"""
        if not await self._check_user_access(update):
            return
        
        import time
        start_time = time.time()
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        try:
            from src.data.nse_api import NSEClient
            
            await update.message.reply_text("🔍 Fetching market overview...")
            
            client = NSEClient()
            
            # Get top 5 gainers and losers
            gainers_df = client.get_top_movers_from_index('NIFTY 500', limit=5, sort_by='gainers')
            losers_df = client.get_top_movers_from_index('NIFTY 500', limit=5, sort_by='losers')
            sectors_df = client.get_sector_performance()
            
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
            
            response_time = int((time.time() - start_time) * 1000)
            self.user_tracker.log_query(user_id=user_id, query_type='market', query_text='/market', response_time_ms=response_time, success=True,
                username=username
            )
            
        except Exception as e:
            logger.error(f"Error in market command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
            response_time = int((time.time() - start_time) * 1000)
            self.user_tracker.log_query(user_id=user_id, query_type='market', query_text='/market', response_time_ms=response_time, success=False, error_message=str(e),
                username=username
            )
    
    # Remove specific import in favor of top-level or method-level
    # Imports should be at the top of file 
    
    def _format_stock_list(self, df, title, limit=10):
        """Deprecated: Use src.utils.telegram_helpers.format_stock_list instead"""
        from src.utils.telegram_helpers import format_stock_list
        return format_stock_list(df, title, limit)

    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown commands - show help"""
        unknown_cmd = update.message.text.split()[0] if update.message.text else "Unknown"
        
        await update.message.reply_text(
            f"❓ *Unknown command: {unknown_cmd}*\n\n"
            "I didn't recognize that command.\n"
            "Here is the list of available commands:",
            parse_mode='Markdown'
        )
        
        # Show help
        await self.help_command(update, context)

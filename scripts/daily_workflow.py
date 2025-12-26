#!/usr/bin/env python3
"""
Daily Trading Workflow Script

This script orchestrates the complete daily workflow:
1. Check data completeness for all instruments
2. Verify fundamentals data exists
3. Sync latest market data
4. Generate trading signals
5. Send signals via Telegram

Usage:
    python scripts/daily_workflow.py [--skip-sync] [--skip-fundamentals]
"""

import sys
import argparse
import subprocess
import os
from pathlib import Path
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

from src.data.storage import InstrumentsDB, OHLCVDB, FundamentalsDB
from src.data.sync import DataSync
from src.data.fundamentals import FundamentalsDownloader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('daily_workflow')

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def check_data_completeness():
    """Check if OHLCV data exists and is recent for all instruments"""
    print_header("STEP 1: Checking Data Completeness")
    
    instruments_db = InstrumentsDB()
    ohlcv_db = OHLCVDB()
    
    # Get all active instruments
    instruments = instruments_db.get_all_active()
    total_instruments = len(instruments)
    
    logger.info(f"Checking data for {total_instruments} instruments...")
    
    # Determine reference date (handle weekends and Monday pre-market)
    now = datetime.now()
    reference_date = now
    
    # If Saturday (5), use Friday
    if now.weekday() == 5:
        reference_date = now - timedelta(days=1)
        logger.info("Running on Saturday, using Friday as reference")
    # If Sunday (6), use Friday
    elif now.weekday() == 6:
        reference_date = now - timedelta(days=2)
        logger.info("Running on Sunday, using Friday as reference")
    # If Monday (0) before market open (9:15 AM), use Friday
    elif now.weekday() == 0 and now.hour < 9:
        reference_date = now - timedelta(days=3)
        logger.info("Running on Monday before market open, using Friday as reference")
    
    missing_data = []
    stale_data = []
    
    for idx, row in instruments.iterrows():
        symbol = row['symbol']
        
        # Check 1d timeframe (most important)
        latest_time = ohlcv_db.get_latest_timestamp(symbol, '1d')
        
        if latest_time is None:
            missing_data.append(symbol)
            logger.warning(f"  ❌ {symbol}: No data found")
        else:
            days_old = (reference_date - latest_time.replace(tzinfo=None)).days
            if days_old > 3:  # Data older than 3 days from reference
                stale_data.append((symbol, days_old))
                logger.warning(f"  ⚠️  {symbol}: Data is {days_old} days old")
    
    # Summary
    print(f"\n📊 Data Status:")
    print(f"  Total instruments: {total_instruments}")
    print(f"  Missing data: {len(missing_data)}")
    print(f"  Stale data (>3 days): {len(stale_data)}")
    
    if missing_data:
        print(f"\n  Missing: {', '.join(missing_data[:10])}")
        if len(missing_data) > 10:
            print(f"  ... and {len(missing_data) - 10} more")
    
    return len(missing_data) == 0 and len(stale_data) == 0

def check_fundamentals():
    """Check if fundamentals data exists and is up-to-date for all instruments"""
    print_header("STEP 2: Checking Fundamentals Data")
    
    instruments_db = InstrumentsDB()
    fundamentals_db = FundamentalsDB()
    
    instruments = instruments_db.get_all_active()
    fundamentals = fundamentals_db.get_all_fundamentals()
    
    instruments_symbols = set(instruments['symbol'].tolist())
    fundamentals_symbols = set(fundamentals['symbol'].tolist()) if not fundamentals.empty else set()
    
    missing_fundamentals = instruments_symbols - fundamentals_symbols
    
    # Check for stale fundamentals (>3 days old)
    stale_fundamentals = []
    if not fundamentals.empty:
        for _, row in fundamentals.iterrows():
            if 'updated_at' in row and row['updated_at']:
                days_old = (datetime.now() - row['updated_at'].replace(tzinfo=None)).days
                if days_old > 3:
                    stale_fundamentals.append((row['symbol'], days_old))
    
    print(f"\n📈 Fundamentals Status:")
    print(f"  Total instruments: {len(instruments_symbols)}")
    print(f"  With fundamentals: {len(fundamentals_symbols)}")
    print(f"  Missing fundamentals: {len(missing_fundamentals)}")
    print(f"  Stale fundamentals (>3 days): {len(stale_fundamentals)}")
    
    if missing_fundamentals:
        print(f"\n  Missing: {', '.join(list(missing_fundamentals)[:10])}")
        if len(missing_fundamentals) > 10:
            print(f"  ... and {len(missing_fundamentals) - 10} more")
    
    if stale_fundamentals:
        print(f"\n  Stale: {', '.join([f'{s} ({d}d)' for s, d in stale_fundamentals[:5]])}")
        if len(stale_fundamentals) > 5:
            print(f"  ... and {len(stale_fundamentals) - 5} more")
    
    return len(missing_fundamentals) == 0 and len(stale_fundamentals) == 0, missing_fundamentals, stale_fundamentals

def sync_fundamentals(missing_symbols, stale_symbols):
    """Sync fundamentals for missing and stale instruments"""
    print_header("STEP 2b: Syncing Fundamentals")
    
    fundamentals_db = FundamentalsDB()
    fund_downloader = FundamentalsDownloader()
    
    # Combine missing and stale (stale is list of tuples)
    to_sync = list(missing_symbols) + [s for s, _ in stale_symbols]
    
    if not to_sync:
        logger.info("✅ All fundamentals are up-to-date")
        return True
    
    logger.info(f"Syncing fundamentals for {len(to_sync)} instruments...")
    
    success_count = 0
    for i, symbol in enumerate(to_sync, 1):
        try:
            logger.info(f"  [{i}/{len(to_sync)}] {symbol}")
            fundamentals = fund_downloader.download_fundamentals(symbol)
            if fundamentals:
                fundamentals_db.upsert_fundamentals(fundamentals)
                success_count += 1
        except Exception as e:
            logger.error(f"    Failed: {e}")
    
    logger.info(f"✅ Synced {success_count}/{len(to_sync)} fundamentals")
    return True

def sync_market_data():
    """Sync latest market data for all timeframes"""
    print_header("STEP 3: Syncing Market Data")
    
    logger.info("Running incremental sync for 1d timeframe...")
    
    # Run sync_data.py for 1d timeframe with live output (no timeout)
    sync_process = subprocess.Popen(
        ['python', 'scripts/sync/sync_data.py', '--update', '--timeframe', '1d', '--workers', '1'],
    )
    sync_process.wait() # Wait for the process to complete
    
    if sync_process.returncode != 0:
        logger.error("Sync failed")
        return False
    
    logger.info("✅ Market data sync completed")
    return True

def generate_signals(no_notify=False, test_symbol=None):
    """Generate trading signals"""
    print_header("STEP 4: Generating Trading Signals")
    
    if test_symbol:
        logger.info(f"Running signal generation for test symbol: {test_symbol}")
    else:
        logger.info("Running signal generation...")
    
    # Build command with optional --no-notify flag and sentiment analysis
    cmd = ['python', 'scripts/signals/daily_signals_scored.py', '--sentiment']
    if no_notify:
        cmd.append('--no-notify')
    if test_symbol:
        cmd.extend(['--test-symbol', test_symbol])
    
    # Run daily_signals_scored.py with live output and sentiment analysis (no timeout)
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        logger.error("Signal generation failed")
        return False, "Failed"
    
    logger.info("✅ Signal generation completed")
    return True, "Success"

def send_workflow_status(status_dict, start_time):
    """Send workflow status report via Telegram"""
    print_header("STEP 5: Sending Workflow Status Report")
    
    # Get workflow Telegram credentials
    bot_token = os.getenv('WORKFLOW_TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('WORKFLOW_TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        logger.warning("⚠️  Workflow Telegram credentials not configured, skipping status report")
        return
    
    try:
        from telegram import Bot
        import asyncio
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Build status message
        message = "📊 **Daily Workflow Status Report**\n\n"
        message += f"🕐 Execution Time: {execution_time:.1f}s\n\n"
        
        # Add status for each step
        for step, status in status_dict.items():
            emoji = "✅" if status['success'] else "❌"
            message += f"{emoji} {step}: {status['message']}\n"
        
        # Add any errors
        errors = [s['error'] for s in status_dict.values() if s.get('error')]
        if errors:
            message += f"\n⚠️ **Errors:**\n"
            for error in errors[:3]:  # Show first 3 errors
                message += f"  • {error[:100]}\n"
        
        # Send message
        async def send_message():
            bot = Bot(token=bot_token)
            await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
        
        asyncio.run(send_message())
        logger.info("✅ Workflow status sent to Telegram")
        
    except Exception as e:
        logger.error(f"Failed to send workflow status: {e}")

def main():
    parser = argparse.ArgumentParser(description='Daily trading workflow')
    parser.add_argument('--skip-sync', action='store_true', help='Skip market data sync')
    parser.add_argument('--skip-fundamentals', action='store_true', help='Skip fundamentals check/sync')
    parser.add_argument('--no-notify', action='store_true', help='Disable all Telegram notifications')
    parser.add_argument('--test-symbol', type=str, help='Test with specific symbol (e.g., RELIANCE.NS)')
    args = parser.parse_args()
    
    start_time = datetime.now()
    status_dict = {}
    
    print_header("DAILY TRADING WORKFLOW")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Step 1: Check data completeness
    try:
        data_complete = check_data_completeness()
        status_dict['Data Completeness'] = {
            'success': data_complete,
            'message': 'All data up-to-date' if data_complete else 'Some data missing/stale'
        }
    except Exception as e:
        status_dict['Data Completeness'] = {'success': False, 'message': 'Check failed', 'error': str(e)}
        data_complete = False
    
    # Step 2: Check and sync fundamentals
    if not args.skip_fundamentals:
        try:
            fundamentals_complete, missing, stale = check_fundamentals()
            if not fundamentals_complete:
                sync_fundamentals(missing, stale)
            status_dict['Fundamentals'] = {
                'success': True,
                'message': f'Synced {len(missing) + len(stale)} instruments' if not fundamentals_complete else 'All up-to-date'
            }
        except Exception as e:
            status_dict['Fundamentals'] = {'success': False, 'message': 'Sync failed', 'error': str(e)}
    else:
        status_dict['Fundamentals'] = {'success': True, 'message': 'Skipped'}
    
    # Step 3: Sync market data
    if not args.skip_sync:
        if not data_complete:
            logger.warning("⚠️  Data issues detected, but proceeding with sync...")
        
        try:
            sync_success = sync_market_data()
            if not sync_success:
                logger.error("❌ Sync failed, aborting workflow")
                status_dict['Market Data Sync'] = {'success': False, 'message': 'Sync failed'}
                if not args.no_notify:
                    send_workflow_status(status_dict, start_time)
                return 1
            status_dict['Market Data Sync'] = {'success': True, 'message': 'Completed successfully'}
        except Exception as e:
            logger.error(f"❌ Sync error: {e}")
            status_dict['Market Data Sync'] = {'success': False, 'message': 'Sync error', 'error': str(e)}
            if not args.no_notify:
                send_workflow_status(status_dict, start_time)
            return 1
    else:
        logger.info("⏭️  Skipping market data sync (--skip-sync)")
        status_dict['Market Data Sync'] = {'success': True, 'message': 'Skipped'}
    
    # Step 4: Generate signals
    try:
        signal_success, signal_output = generate_signals(no_notify=args.no_notify, test_symbol=args.test_symbol)
        if not signal_success:
            logger.error("❌ Signal generation failed")
            status_dict['Signal Generation'] = {'success': False, 'message': 'Failed', 'error': signal_output}
            if not args.no_notify:
                send_workflow_status(status_dict, start_time)
            return 1
        status_dict['Signal Generation'] = {'success': True, 'message': 'Completed successfully'}
    except Exception as e:
        logger.error(f"❌ Signal generation error: {e}")
        status_dict['Signal Generation'] = {'success': False, 'message': 'Error', 'error': str(e)}
        if not args.no_notify:
            send_workflow_status(status_dict, start_time)
        return 1
    
    # Step 5: Send workflow status
    if not args.no_notify:
        send_workflow_status(status_dict, start_time)
    else:
        logger.info("Workflow status notifications disabled via --no-notify flag")
    
    print_header("WORKFLOW COMPLETED SUCCESSFULLY")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

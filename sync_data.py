#!/usr/bin/env python3
"""
Data Synchronization CLI

Usage:
    python sync_data.py --help
    python sync_data.py --full              # Full download for all symbols
    python sync_data.py --update            # Incremental update
    python sync_data.py --timeframe 1d      # Sync specific timeframe
    python sync_data.py --status            # Show sync status
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.sync import DataSync
from src.utils.logger import setup_logger

logger = setup_logger('sync_cli')


def main():
    parser = argparse.ArgumentParser(
        description='Synchronize OHLCV data for Nifty 100 stocks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full download for all timeframes
  python sync_data.py --full

  # Incremental update (only new data)
  python sync_data.py --update

  # Sync specific timeframe
  python sync_data.py --timeframe 1d --full

  # Show current sync status
  python sync_data.py --status

  # Sync with custom number of workers
  python sync_data.py --update --workers 10
        """
    )
    
    parser.add_argument(
        '--full',
        action='store_true',
        help='Full download (download all historical data)'
    )
    
    parser.add_argument(
        '--update',
        action='store_true',
        help='Incremental update (download only new data)'
    )
    
    parser.add_argument('--timeframe', 
                        choices=['1m', '5m', '15m', '30m', '1h', '1d', '1w'],
                        default='1d',
                        help='Timeframe to sync (default: 1d)')
    
    parser.add_argument('--period',
                        default='5y',
                        help='Period to download (e.g., 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max). Default: 5y')
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current sync status'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=5,
        help='Number of parallel download workers (default: 5)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force sync even if data is up-to-date'
    )
    
    args = parser.parse_args()
    
    # Initialize DataSync
    sync = DataSync(max_workers=args.workers)
    
    # Show status
    if args.status:
        logger.info("Fetching sync status...")
        status_df = sync.get_sync_status()
        
        print("\n" + "=" * 80)
        print("SYNC STATUS")
        print("=" * 80)
        
        # Summary by timeframe
        print("\nBy Timeframe:")
        summary = status_df.groupby('timeframe').agg({
            'symbol': 'count',
            'needs_update': 'sum',
            'days_old': 'mean'
        }).round(2)
        summary.columns = ['Total Symbols', 'Needs Update', 'Avg Days Old']
        print(summary)
        
        # Symbols needing update
        needs_update = status_df[status_df['needs_update'] == True]
        if not needs_update.empty:
            print(f"\n{len(needs_update)} symbol-timeframe pairs need update")
            print("\nOldest data (top 10):")
            oldest = status_df.nlargest(10, 'days_old')[['symbol', 'timeframe', 'days_old', 'latest_data']]
            print(oldest.to_string(index=False))
        else:
            print("\n✓ All data is up to date!")
        
        print("\n" + "=" * 80)
        return
    
    # Perform sync
    if not (args.full or args.update):
        parser.print_help()
        print("\nError: Please specify --full or --update")
        sys.exit(1)
    
    # Determine mode
    full_download = args.full or (not args.update)
    
    logger.info("=" * 80)
    logger.info("DATA SYNCHRONIZATION")
    logger.info("=" * 80)
    logger.info(f"Mode: {'Full download' if full_download else 'Incremental update'}")
    logger.info(f"Workers: {args.workers}")
    
    if args.timeframe:
        logger.info(f"Timeframe: {args.timeframe}")
        logger.info(f"Period: {args.period}")
        logger.info("=" * 80)
        results = sync.sync_timeframe(args.timeframe, full_download=full_download, period=args.period)
    else:
        logger.info("Timeframes: All configured timeframes")
        logger.info("=" * 80)
        results = sync.sync_all_symbols(full_download=full_download, force=args.force)
    
    # Print summary
    print("\n" + "=" * 80)
    print("SYNC SUMMARY")
    print("=" * 80)
    print(f"Total tasks: {results['total_tasks']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Total rows inserted: {results['total_rows']}")
    print(f"Duration: {results['duration']:.2f} seconds")
    print("=" * 80)
    
    # Show failures if any
    if results['failed'] > 0:
        print("\nFailed tasks:")
        failures = [d for d in results['details'] if d['status'] == 'error']
        
        # Group by error type
        error_types = {}
        for failure in failures:
            error_type = failure.get('error_type', 'OTHER')
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(failure)
        
        # Show summary by error type
        for error_type, errors in error_types.items():
            print(f"\n  {error_type}: {len(errors)} failures")
            for error in errors[:3]:  # Show first 3 of each type
                print(f"    - {error['symbol']} {error['timeframe']}: {error.get('error', 'Unknown')[:80]}")
            if len(errors) > 3:
                print(f"    ... and {len(errors) - 3} more")
        
        # Specific advice for rate limiting
        if 'RATE_LIMIT' in error_types:
            print(f"\n⚠️  RATE LIMIT DETECTED ({len(error_types['RATE_LIMIT'])} symbols)")
            print("   Solutions:")
            print("   1. Wait 2-3 minutes and retry")
            print("   2. Use fewer workers: --workers 1")
            print("   3. Add delays between requests")
    
    logger.info("Sync completed!")


if __name__ == '__main__':
    main()

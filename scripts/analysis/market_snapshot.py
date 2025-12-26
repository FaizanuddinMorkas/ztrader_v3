"""
Market Snapshot - NSE Market Data Tool

Shows real-time market data including top gainers/losers, sector performance,
and most active stocks using NSE APIs.

Usage:
    python scripts/analysis/market_snapshot.py --type gainers
    python scripts/analysis/market_snapshot.py --type sectors
    python scripts/analysis/market_snapshot.py --type overview
"""

import sys
import os
import argparse
import pandas as pd
from tabulate import tabulate

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.data.nse_api import NSEClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def display_gainers_losers(df, title):
    """Display gainers/losers in formatted table"""
    if df.empty:
        print(f"\n{title}: No data available")
        return
    
    print(f"\n{'='*100}")
    print(f"{title}")
    print('='*100)
    
    # Extract company name from meta field if available
    if 'meta' in df.columns:
        df['companyName'] = df['meta'].apply(lambda x: x.get('companyName', '') if isinstance(x, dict) else '')
    
    # Select relevant columns (API uses different names)
    cols_to_show = []
    col_mapping = {}
    
    if 'symbol' in df.columns:
        cols_to_show.append('symbol')
        col_mapping['symbol'] = 'Symbol'
    
    if 'companyName' in df.columns and not df['companyName'].isna().all():
        cols_to_show.append('companyName')
        col_mapping['companyName'] = 'Company'
    
    # Handle both ltp and lastPrice
    if 'ltp' in df.columns:
        cols_to_show.append('ltp')
        col_mapping['ltp'] = 'LTP'
    elif 'lastPrice' in df.columns:
        cols_to_show.append('lastPrice')
        col_mapping['lastPrice'] = 'LTP'
    elif 'last' in df.columns:
        cols_to_show.append('last')
        col_mapping['last'] = 'LTP'
    
    # Handle both perChange and pChange
    if 'perChange' in df.columns:
        cols_to_show.append('perChange')
        col_mapping['perChange'] = 'Change %'
    elif 'pChange' in df.columns:
        cols_to_show.append('pChange')
        col_mapping['pChange'] = 'Change %'
    
    # Add open, high, low if available
    if 'open' in df.columns:
        cols_to_show.append('open')
        col_mapping['open'] = 'Open'
    if 'dayHigh' in df.columns:
        cols_to_show.append('dayHigh')
        col_mapping['dayHigh'] = 'High'
    if 'dayLow' in df.columns:
        cols_to_show.append('dayLow')
        col_mapping['dayLow'] = 'Low'
    
    # Handle volume
    if 'trade_quantity' in df.columns:
        cols_to_show.append('trade_quantity')
        col_mapping['trade_quantity'] = 'Volume'
    elif 'totalTradedVolume' in df.columns:
        cols_to_show.append('totalTradedVolume')
        col_mapping['totalTradedVolume'] = 'Volume'
    elif 'volume' in df.columns:
        cols_to_show.append('volume')
        col_mapping['volume'] = 'Volume'
    
    if not cols_to_show:
        print("No displayable columns found")
        return
    
    display_df = df[cols_to_show].copy()
    display_df.columns = [col_mapping[col] for col in cols_to_show]
    
    # Format numbers
    for col in ['LTP', 'Open', 'High', 'Low']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"₹{x:,.2f}" if pd.notna(x) else '-')
    
    if 'Change %' in display_df.columns:
        display_df['Change %'] = display_df['Change %'].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else '-')
    
    if 'Volume' in display_df.columns:
        display_df['Volume'] = display_df['Volume'].apply(
            lambda x: f"{x/1000000:.2f}M" if pd.notna(x) and x > 1000000 else (f"{x/1000:.2f}K" if pd.notna(x) else '-')
        )
    
    # Truncate company name if too long
    if 'Company' in display_df.columns:
        display_df['Company'] = display_df['Company'].apply(lambda x: x[:30] + '...' if len(str(x)) > 30 else x)
    
    print(tabulate(display_df, headers='keys', tablefmt='grid', showindex=False))


def display_sector_performance(df):
    """Display sector performance"""
    if df.empty:
        print("\nSector Performance: No data available")
        return
    
    print(f"\n{'='*80}")
    print("SECTOR PERFORMANCE")
    print('='*80)
    
    # Select relevant columns
    display_df = df[['sector', 'last', 'pChange']].copy()
    display_df.columns = ['Sector', 'Index Value', 'Change %']
    
    # Format numbers
    display_df['Index Value'] = display_df['Index Value'].apply(lambda x: f"{x:,.2f}")
    display_df['Change %'] = display_df['Change %'].apply(lambda x: f"{x:+.2f}%")
    
    print(tabulate(display_df, headers='keys', tablefmt='grid', showindex=True))


def display_market_overview(client):
    """Display comprehensive market overview"""
    print("\n" + "="*80)
    print("MARKET OVERVIEW")
    print("="*80)
    
    # Market status
    try:
        status = client.get_market_status()
        print(f"\nMarket Status: {status.get('marketState', 'Unknown')}")
    except:
        pass
    
    # Top gainers
    gainers = client.get_top_gainers(limit=5)
    display_gainers_losers(gainers, "📈 TOP 5 GAINERS")
    
    # Top losers
    losers = client.get_top_losers(limit=5)
    display_gainers_losers(losers, "📉 TOP 5 LOSERS")
    
    # Most active
    active = client.get_most_active_by_volume(limit=5)
    display_gainers_losers(active, "📊 MOST ACTIVE (Volume)")
    
    # Sector performance
    sectors = client.get_sector_performance()
    display_sector_performance(sectors)


def main():
    parser = argparse.ArgumentParser(description="NSE Market Data Snapshot")
    parser.add_argument('--type', choices=['gainers', 'losers', 'active', 'volume-shockers', 
                                           '52high', '52low', 'sectors', 'overview', 'sector-stocks'],
                       default='overview', help='Type of data to fetch')
    parser.add_argument('--limit', type=int, default=20, help='Number of results')
    parser.add_argument('--sector', type=str, help='Sector name for sector-stocks type')
    parser.add_argument('--index', type=str, help='Index filter (NIFTY 500, NIFTY 50, NIFTY BANK, etc.)')
    
    args = parser.parse_args()
    
    # Initialize client
    logger.info("Initializing NSE API client...")
    client = NSEClient()
    
    try:
        if args.type == 'gainers':
            # If index is Nifty 500 or similar, use index-based method
            if args.index and args.index.upper() in ['NIFTY500', 'NIFTY 500', 'NIFTY50', 'NIFTY 50']:
                index_map = {
                    'NIFTY500': 'NIFTY 500',
                    'NIFTY 500': 'NIFTY 500',
                    'NIFTY50': 'NIFTY 50',
                    'NIFTY 50': 'NIFTY 50'
                }
                index_name = index_map.get(args.index.upper(), args.index)
                df = client.get_top_movers_from_index(index_name, limit=args.limit, sort_by='gainers')
                display_gainers_losers(df, f"TOP {args.limit} GAINERS ({index_name})")
            else:
                # Use live-analysis-variations API
                df = client.get_top_gainers(limit=args.limit, index=args.index)
                index_label = f" ({args.index})" if args.index else ""
                display_gainers_losers(df, f"TOP {args.limit} GAINERS{index_label}")
        
        elif args.type == 'losers':
            # Support index filtering for losers too
            if args.index and args.index.upper() in ['NIFTY500', 'NIFTY 500', 'NIFTY50', 'NIFTY 50']:
                index_map = {
                    'NIFTY500': 'NIFTY 500',
                    'NIFTY 500': 'NIFTY 500',
                    'NIFTY50': 'NIFTY 50',
                    'NIFTY 50': 'NIFTY 50'
                }
                index_name = index_map.get(args.index.upper(), args.index)
                df = client.get_top_movers_from_index(index_name, limit=args.limit, sort_by='losers')
                display_gainers_losers(df, f"TOP {args.limit} LOSERS ({index_name})")
            else:
                df = client.get_top_losers(limit=args.limit)
                display_gainers_losers(df, f"TOP {args.limit} LOSERS")
        
        elif args.type == 'active':
            df = client.get_most_active_by_volume(limit=args.limit)
            display_gainers_losers(df, f"MOST ACTIVE BY VOLUME - TOP {args.limit}")
        
        elif args.type == 'volume-shockers':
            df = client.get_most_active_by_value(limit=args.limit)
            display_gainers_losers(df, f"VOLUME SHOCKERS (By Value) - TOP {args.limit}")
        
        elif args.type == '52high':
            df = client.get_52week_high(limit=args.limit)
            display_gainers_losers(df, f"STOCKS AT 52-WEEK HIGH - TOP {args.limit}")
        
        elif args.type == '52low':
            df = client.get_52week_low(limit=args.limit)
            display_gainers_losers(df, f"STOCKS AT 52-WEEK LOW - TOP {args.limit}")
        
        elif args.type == 'sectors':
            df = client.get_sector_performance()
            display_sector_performance(df)
        
        elif args.type == 'sector-stocks':
            if not args.sector:
                print("Error: --sector required for sector-stocks type")
                print("\nAvailable sectors:")
                for sector in client.SECTORAL_INDICES:
                    print(f"  - {sector}")
                return
            
            df = client.get_sector_stocks(args.sector)
            display_gainers_losers(df, f"STOCKS IN {args.sector}")
        
        elif args.type == 'overview':
            display_market_overview(client)
    
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        print(f"\n❌ Error: {e}")
        print("\nTip: NSE APIs may be slow or unavailable. Try again in a few seconds.")
    
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        print(f"\n❌ Error: {e}")
        print("\nTip: NSE APIs may be slow or unavailable. Try again in a few seconds.")


if __name__ == "__main__":
    main()

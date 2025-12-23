#!/usr/bin/env python3
"""
Fetch fundamentals for special stocks
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.fundamentals import FundamentalsDownloader

# Stocks to fetch fundamentals for
SYMBOLS = [
    'RECLTD.NS',      # REC
    'PFC.NS',         # PFC
    'BDL.NS',         # BDL
    'BSE.NS',         # BSE
    'BIOCON.NS',      # BIOCON
    'GODREJCP.NS',    # GODREJ CONSUMER
    'BANKINDIA.NS',   # BOI
    'SRF.NS'          # SRF
]

def main():
    print("Fetching fundamentals for special stocks...")
    print(f"Stocks: {', '.join(SYMBOLS)}\n")
    
    fund_db = FundamentalsDownloader()
    
    for symbol in SYMBOLS:
        try:
            print(f"Fetching {symbol}...")
            
            # Fetch and store fundamentals
            fundamentals = fund_db.fetch_and_store_fundamentals(symbol)
            
            if fundamentals:
                print(f"✅ {symbol}: P/E={fundamentals.get('pe_ratio', 'N/A')}, "
                      f"ROE={fundamentals.get('roe', 'N/A')}%, "
                      f"Debt/Equity={fundamentals.get('debt_to_equity', 'N/A')}\n")
            else:
                print(f"❌ {symbol}: No fundamentals available\n")
                
        except Exception as e:
            print(f"❌ {symbol}: Error - {str(e)}\n")
    
    print("✅ Fundamentals fetch complete!")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Seed Nifty 100 instruments into database

This script populates the instruments table with Nifty 100 stock symbols
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.storage import InstrumentsDB
from src.utils.logger import setup_logger

logger = setup_logger('seed_nifty100')


# Nifty 100 constituents with sector information
NIFTY_100_STOCKS = [
    # Banking & Financial Services
    ('HDFCBANK.NS', 'HDFC Bank Ltd', 'Financial Services', 'Private Bank', True),
    ('ICICIBANK.NS', 'ICICI Bank Ltd', 'Financial Services', 'Private Bank', True),
    ('KOTAKBANK.NS', 'Kotak Mahindra Bank', 'Financial Services', 'Private Bank', True),
    ('AXISBANK.NS', 'Axis Bank Ltd', 'Financial Services', 'Private Bank', True),
    ('SBIN.NS', 'State Bank of India', 'Financial Services', 'Public Bank', True),
    ('BAJFINANCE.NS', 'Bajaj Finance Ltd', 'Financial Services', 'NBFC', True),
    ('BAJAJFINSV.NS', 'Bajaj Finserv Ltd', 'Financial Services', 'NBFC', True),
    ('HDFCLIFE.NS', 'HDFC Life Insurance', 'Financial Services', 'Life Insurance', True),
    ('SBILIFE.NS', 'SBI Life Insurance', 'Financial Services', 'Life Insurance', True),
    ('INDUSINDBK.NS', 'IndusInd Bank Ltd', 'Financial Services', 'Private Bank', False),
    ('BANDHANBNK.NS', 'Bandhan Bank Ltd', 'Financial Services', 'Private Bank', False),
    
    # Information Technology
    ('TCS.NS', 'Tata Consultancy Services', 'Information Technology', 'IT Services', True),
    ('INFY.NS', 'Infosys Ltd', 'Information Technology', 'IT Services', True),
    ('HCLTECH.NS', 'HCL Technologies', 'Information Technology', 'IT Services', True),
    ('WIPRO.NS', 'Wipro Ltd', 'Information Technology', 'IT Services', True),
    ('TECHM.NS', 'Tech Mahindra', 'Information Technology', 'IT Services', True),
    ('LTI.NS', 'LTI Mindtree', 'Information Technology', 'IT Services', False),
    ('PERSISTENT.NS', 'Persistent Systems', 'Information Technology', 'IT Services', False),
    ('MPHASIS.NS', 'Mphasis Ltd', 'Information Technology', 'IT Services', False),
    
    # Energy & Oil & Gas
    ('RELIANCE.NS', 'Reliance Industries', 'Energy', 'Oil & Gas', True),
    ('ONGC.NS', 'Oil & Natural Gas Corp', 'Energy', 'Oil & Gas', True),
    ('BPCL.NS', 'Bharat Petroleum', 'Energy', 'Oil & Gas', True),
    ('IOC.NS', 'Indian Oil Corporation', 'Energy', 'Oil & Gas', True),
    ('NTPC.NS', 'NTPC Ltd', 'Energy', 'Power Generation', True),
    ('POWERGRID.NS', 'Power Grid Corp', 'Energy', 'Power Transmission', True),
    ('ADANIGREEN.NS', 'Adani Green Energy', 'Energy', 'Renewable Energy', False),
    ('ADANIPORTS.NS', 'Adani Ports & SEZ', 'Infrastructure', 'Ports', True),
    
    # Automobile
    ('MARUTI.NS', 'Maruti Suzuki India', 'Automobile', 'Auto Manufacturer', True),
    # Tata Motors (post-demerger)
    ('TATAMOTORS.NS', 'Tata Motors Passenger Vehicles Ltd', 'Automobile', 'Passenger Vehicles', True),
    ('TMPV.NS', 'Tata Motors Passenger Vehicles Ltd', 'Automobile', 'Passenger Vehicles', False),  # Same as TATAMOTORS.NS
    ('TMCV.NS', 'TML Commercial Vehicles Ltd', 'Automobile', 'Commercial Vehicles', False),
    ('M&M.NS', 'Mahindra & Mahindra', 'Automobile', 'Auto Manufacturer', True),
    ('BAJAJ-AUTO.NS', 'Bajaj Auto Ltd', 'Automobile', 'Two Wheeler', True),
    ('EICHERMOT.NS', 'Eicher Motors', 'Automobile', 'Two Wheeler', True),
    ('HEROMOTOCO.NS', 'Hero MotoCorp', 'Automobile', 'Two Wheeler', True),
    ('TVSMOTOR.NS', 'TVS Motor Company', 'Automobile', 'Two Wheeler', False),
    
    # FMCG (Fast Moving Consumer Goods)
    ('HINDUNILVR.NS', 'Hindustan Unilever', 'FMCG', 'Consumer Goods', True),
    ('ITC.NS', 'ITC Ltd', 'FMCG', 'Diversified', True),
    ('NESTLEIND.NS', 'Nestle India', 'FMCG', 'Food Products', True),
    ('BRITANNIA.NS', 'Britannia Industries', 'FMCG', 'Food Products', True),
    ('DABUR.NS', 'Dabur India Ltd', 'FMCG', 'Personal Care', False),
    ('MARICO.NS', 'Marico Ltd', 'FMCG', 'Personal Care', False),
    ('GODREJCP.NS', 'Godrej Consumer Products', 'FMCG', 'Personal Care', False),
    
    # Pharmaceuticals
    ('SUNPHARMA.NS', 'Sun Pharmaceutical', 'Pharmaceuticals', 'Drug Manufacturer', True),
    ('DRREDDY.NS', 'Dr. Reddy\'s Laboratories', 'Pharmaceuticals', 'Drug Manufacturer', True),
    ('CIPLA.NS', 'Cipla Ltd', 'Pharmaceuticals', 'Drug Manufacturer', True),
    ('DIVISLAB.NS', 'Divi\'s Laboratories', 'Pharmaceuticals', 'Drug Manufacturer', True),
    ('APOLLOHOSP.NS', 'Apollo Hospitals', 'Healthcare', 'Hospitals', True),
    ('BIOCON.NS', 'Biocon Ltd', 'Pharmaceuticals', 'Biotechnology', False),
    ('LUPIN.NS', 'Lupin Ltd', 'Pharmaceuticals', 'Drug Manufacturer', False),
    
    # Metals & Mining
    ('TATASTEEL.NS', 'Tata Steel Ltd', 'Metals & Mining', 'Steel', True),
    ('HINDALCO.NS', 'Hindalco Industries', 'Metals & Mining', 'Aluminum', True),
    ('JSWSTEEL.NS', 'JSW Steel Ltd', 'Metals & Mining', 'Steel', True),
    ('COALINDIA.NS', 'Coal India Ltd', 'Metals & Mining', 'Coal', True),
    ('VEDL.NS', 'Vedanta Ltd', 'Metals & Mining', 'Diversified', False),
    
    # Cement
    ('ULTRACEMCO.NS', 'UltraTech Cement', 'Cement', 'Cement', True),
    ('GRASIM.NS', 'Grasim Industries', 'Cement', 'Diversified', True),
    ('SHREECEM.NS', 'Shree Cement Ltd', 'Cement', 'Cement', False),
    
    # Telecom
    ('BHARTIARTL.NS', 'Bharti Airtel Ltd', 'Telecom', 'Telecom Services', True),
    
    # Retail
    ('DMART.NS', 'Avenue Supermarts (DMart)', 'Retail', 'Retail', False),
    ('TRENT.NS', 'Trent Ltd', 'Retail', 'Retail', False),
    
    # Conglomerate
    ('LT.NS', 'Larsen & Toubro', 'Construction', 'Engineering & Construction', True),
    ('ADANIENT.NS', 'Adani Enterprises', 'Conglomerate', 'Diversified', False),
    
    # Others
    ('TITAN.NS', 'Titan Company Ltd', 'Consumer Durables', 'Jewelry', True),
    ('ASIANPAINT.NS', 'Asian Paints Ltd', 'Consumer Durables', 'Paints', True),
    ('PIDILITIND.NS', 'Pidilite Industries', 'Chemicals', 'Specialty Chemicals', False),
]


def seed_nifty100():
    """Seed Nifty 100 instruments into database"""
    
    logger.info("=" * 80)
    logger.info("SEEDING NIFTY 100 INSTRUMENTS")
    logger.info("=" * 80)
    
    db = InstrumentsDB()
    
    inserted = 0
    updated = 0
    
    for symbol, name, sector, industry, is_nifty_50 in NIFTY_100_STOCKS:
        try:
            rows = db.insert_instrument(
                symbol=symbol,
                name=name,
                sector=sector,
                industry=industry,
                is_nifty_50=is_nifty_50,
                is_nifty_100=True
            )
            
            if rows > 0:
                inserted += 1
                logger.debug(f"Inserted: {symbol} - {name}")
            else:
                updated += 1
                logger.debug(f"Updated: {symbol} - {name}")
                
        except Exception as e:
            logger.error(f"Error inserting {symbol}: {e}")
    
    logger.info("=" * 80)
    logger.info(f"Seeding completed!")
    logger.info(f"Total stocks: {len(NIFTY_100_STOCKS)}")
    logger.info(f"Inserted: {inserted}")
    logger.info(f"Updated: {updated}")
    logger.info("=" * 80)
    
    # Show summary
    df = db.get_all_active()
    print("\nInstruments Summary:")
    print(f"Total active instruments: {len(df)}")
    print(f"Nifty 50 stocks: {df['is_nifty_50'].sum()}")
    print(f"Nifty 100 stocks: {df['is_nifty_100'].sum()}")
    
    print("\nBy Sector:")
    print(df['sector'].value_counts())


if __name__ == '__main__':
    seed_nifty100()

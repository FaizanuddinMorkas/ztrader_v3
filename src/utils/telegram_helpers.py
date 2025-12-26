"""
Telegram Bot Helper Utilities
Shared functions for formatting messages and handling Telegram data
"""
import pandas as pd

def format_stock_list(df: pd.DataFrame, title: str, limit: int = 20) -> str:
    """
    Format stock data DataFrame into a readable Telegram message
    
    Args:
        df: DataFrame containing stock data
        title: Title of the message
        limit: Max number of items to show
        
    Returns:
        Formatted markdown string
    """
    if df.empty:
        return f"*{title}*\n\nNo data available."
    
    message = f"*{title}*\n\n"
    
    # Ensure limit doesn't exceed dataframe size
    display_limit = min(limit, len(df))
    
    for idx, row in df.head(display_limit).iterrows():
        # Handle different column names from different APIs
        symbol = row.get('symbol', 'N/A').replace('.NS', '')
        
        # Get company name
        company = ''
        if 'meta' in row and isinstance(row['meta'], dict):
            company = row['meta'].get('companyName', '')
        elif 'companyName' in row:
            company = row['companyName']
        
        # Get price
        ltp = row.get('lastPrice') or row.get('ltp') or row.get('last', 0)
        
        # Get change
        pchange = row.get('pChange') or row.get('perChange', 0)
        
        # Truncate company name if too long
        if len(company) > 25:
            company = company[:22] + '...'
        
        # Format emoji based on price change
        emoji = "🟢" if pchange > 0 else "🔴" if pchange < 0 else "⚪"
        
        # Construct line: Emoji Symbol - Company
        message += f"{emoji} *{symbol}*"
        if company:
            message += f" - {company}"
        message += f"\n   ₹{ltp:,.2f} ({pchange:+.2f}%)\n\n"
    
    return message

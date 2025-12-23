#!/usr/bin/env python3
"""
Get Telegram Chat ID - Simple Version

Uses direct HTTP requests to get chat IDs.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_chat_ids():
    """Get chat IDs from Telegram bot updates"""
    
    # Get bot token
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env file")
        print("\nPlease add your bot token to .env:")
        print("TELEGRAM_BOT_TOKEN=your_bot_token_here")
        return
    
    print("🤖 Fetching updates from Telegram...")
    print(f"Token: {bot_token[:10]}...{bot_token[-5:]}")
    print()
    
    try:
        # Get bot info
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Error getting bot info: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        bot_info = response.json()
        if not bot_info.get('ok'):
            print(f"❌ Bot API error: {bot_info.get('description')}")
            return
        
        bot_data = bot_info['result']
        print(f"✅ Connected to bot: @{bot_data['username']}")
        print(f"   Bot Name: {bot_data['first_name']}")
        print()
        
        # Get updates
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Error getting updates: {response.status_code}")
            return
        
        data = response.json()
        if not data.get('ok'):
            print(f"❌ API error: {data.get('description')}")
            return
        
        updates = data.get('result', [])
        
        if not updates:
            print("\n⚠️  No messages found!")
            print("\nTo get your chat ID:")
            print(f"1. Open Telegram and search for @{bot_data['username']}")
            print("2. Send any message to the bot (e.g., 'Hello')")
            print("3. Run this script again: python3 get_telegram_chat_id.py")
            return
        
        print(f"✅ Found {len(updates)} recent message(s)\n")
        
        # Extract chat IDs
        chat_ids = {}
        for update in updates:
            if 'message' in update:
                chat = update['message']['chat']
                chat_id = chat['id']
                chat_ids[chat_id] = {
                    'type': chat['type'],
                    'first_name': chat.get('first_name', ''),
                    'last_name': chat.get('last_name', ''),
                    'username': chat.get('username', ''),
                    'title': chat.get('title', '')
                }
        
        print("=" * 60)
        print("AVAILABLE CHAT IDs")
        print("=" * 60)
        
        for chat_id, info in chat_ids.items():
            print(f"\nChat ID: {chat_id}")
            print(f"  Type: {info['type']}")
            
            if info['type'] == 'private':
                name = f"{info['first_name']} {info['last_name']}".strip()
                print(f"  Name: {name}")
                if info['username']:
                    print(f"  Username: @{info['username']}")
            else:
                print(f"  Title: {info['title']}")
        
        print("\n" + "=" * 60)
        print("ADD TO YOUR .env FILE:")
        print("=" * 60)
        
        if chat_ids:
            # Use the most recent chat ID
            latest_chat_id = list(chat_ids.keys())[-1]
            print(f"\nTELEGRAM_CHAT_ID={latest_chat_id}")
            print()
            print("📋 Copy the line above and add it to your .env file")
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        print("Check your internet connection and try again")
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    get_chat_ids()

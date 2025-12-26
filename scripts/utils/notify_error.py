
import os
import sys
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
from dotenv import load_dotenv

async def send_error_alert(command, error_msg, log_preview):
    load_dotenv()
    
    bot_token = os.getenv('WORKFLOW_TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('WORKFLOW_TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("❌ Telegram credentials missing. Cannot send alert.")
        return

    # Escape basic markdown characters if needed or just use simple format
    msg = (
        f"🚨 **CRITICAL CRON FAILURE** 🚨\n\n"
        f"**Command:** `{command}`\n"
        f"**Time:** `{os.popen('date').read().strip()}`\n\n"
        f"**Error:**\n```\n{error_msg}\n```\n\n"
        f"**Log Tail:**\n```\n{log_preview}\n```"
    )

    # Truncate if too long (Telegram limit ~4096)
    if len(msg) > 4000:
        msg = msg[:4000] + "\n... (truncated) ...```"

    try:
        bot = Bot(token=bot_token)
        await bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)
        print("✅ Alert sent to Telegram.")
    except Exception as e:
        print(f"❌ Failed to send Telegram alert: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python notify_error.py <job_name> <log_path>")
        sys.exit(1)
        
    job_name = sys.argv[1]
    log_path = sys.argv[2]
    
    log_preview = "No log content available."
    try:
        # Read the last 2048 bytes (approx 10-20 lines) safely
        file_size = os.path.getsize(log_path)
        with open(log_path, 'r', errors='replace') as f:
            if file_size > 2048:
                f.seek(file_size - 2048)
            log_preview = f.read()
    except Exception as e:
        log_preview = f"Failed to read log file: {e}"
    
    asyncio.run(send_error_alert(job_name, "Execution Failed", log_preview))

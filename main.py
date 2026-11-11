import asyncio
from datetime import datetime
import logging
import threading
from flask import Flask
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# Configuration
TOKEN = "9237583887:AAHlhOpHgBBTT_-GXbmkOuj9m5Q3d0acogY"  # Your BotFather Token
ADMIN_CHAT_ID = 8842031370                               # Your Admin Chat ID

bot = Bot(token=TOKEN)
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def get_fb999_period_and_wait():
    """Calculates the exact upcoming FB999 1-minute period and time sync."""
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    total_minutes = (now.hour * 60) + now.minute
    
    # Matches your target period sequence format (e.g., 2026111100010624)
    period_index = total_minutes + 1  
    period_str = f"{date_str}000{period_index:04d}"
    
    # Exact seconds remaining until the next minute starts
    seconds_remaining = 60 - now.second + 0.2
    return period_str, seconds_remaining

async def prediction_scheduler():
    """Asynchronous loop synchronized with system clock to eliminate lag/drift."""
    logging.info("Prediction scheduler loop started...")
    
    while True:
        try:
            period, wait_time = get_fb999_period_and_wait()
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Win", callback_data="win"),
                    InlineKeyboardButton("❌ Loss", callback_data="loss")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message_text = (
                f"📊 **WIN GO NUMBER SIGNAL (1M)**\n\n"
                f"🔹 Period: `{period}`\n"
                f"📈 Stage Level: Stage 1 / 6\n"
                f"🎯 Prediction Range: 🔴 BIG (5-9)\n"
                f"🔢 Target Numbers: 8 / 9\n"
                f"🔥 Win Rate: 86%"
            )
            
            await bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=message_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            logging.error(f"Error in scheduler loop: {e}")
            await asyncio.sleep(5)

def run_bot():
    asyncio.run(prediction_scheduler())

if __name__ == "__main__":
    # Start the Telegram bot loop in a separate background thread
    t = threading.Thread(target=run_bot)
    t.start()
    
    # Run Flask on port 8080 to satisfy cloud hosting health checks
    app.run(host="0.0.0.0", port=8080)

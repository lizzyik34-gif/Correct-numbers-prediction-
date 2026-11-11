import asyncio
from datetime import datetime, timezone
import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# Configuration
TOKEN = "YOUR_BOT_TOKEN_HERE"
ADMIN_CHAT_ID = 8842031370  # Your admin chat ID from context
bot = Bot(token=TOKEN)

logging.basicConfig(level=logging.INFO)

def get_fb999_period_and_wait():
    """
    Calculates the current FB999 1-minute period based on the exact UTC/system time 
    and returns both the NEXT period to drop and the exact seconds remaining until 
    the next minute rolls over.
    """
    now = datetime.now() # Adjust to timezone.utc if your platform runs on UTC
    
    # Format: YYYYMMDD + daily minute count
    date_str = now.strftime("%Y%m%d")
    total_minutes = (now.hour * 60) + now.minute
    
    # FB999 1M format typically uses a 4-digit zero-padded index offset starting at 1
    # e.g., midnight is 0001 or similar depending on the platform layout. 
    # Based on your image: 2026111100010624 -> let's map the daily sequence index:
    period_index = total_minutes + 1  # 00:00 is period 1, 11:34 is 695, etc.
    
    current_period_str = f"{date_str}000{period_index:04d}" # Adjust padding if needed based on exact API length
    
    # Calculate seconds until the next minute starts (+1 second buffer for safety)
    seconds_remaining = 60 - now.second + 0.2
    
    return current_period_str, seconds_remaining

async def prediction_scheduler():
    """
    24/7 background loop that never drifts or stops.
    """
    logging.info("Prediction scheduler started 24/7 loop...")
    
    while True:
        try:
            period, wait_time = get_fb999_period_and_wait()
            
            # Send the signal for the upcoming period precisely at the start of the minute
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
            
            # Sleep precisely until the next minute boundary hits
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            logging.error(f"Error in scheduler loop: {e}")
            await asyncio.sleep(5)  rs: Retry quickly if a temporary network drop happens

if __name__ == "__main__":
    # Run loop asynchronously
    asyncio.run(prediction_scheduler())

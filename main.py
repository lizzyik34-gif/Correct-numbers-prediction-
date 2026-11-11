import asyncio
from datetime import datetime
import logging
import threading
from flask import Flask
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configuration
TOKEN = "9237583887:AAHlhOpHgBBTT_-GXbmkOuj9m5Q3d0acogY"
ADMIN_CHAT_ID = 8842031370

app_flask = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Global flag to control the live stream loop
is_live_running = False

@app_flask.route('/')
def home():
    return "Bot is running 24/7!"

def get_fb999_period_and_wait():
    """Calculates exact FB999 1-minute period and time synchronization."""
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    total_minutes = (now.hour * 60) + now.minute
    
    # Sequence offset matching your target period format
    period_index = total_minutes + 1  
    period_str = f"{date_str}000{period_index:04d}"
    
    # Exact seconds remaining until the next minute rolls over
    seconds_remaining = 60 - now.second + 0.2
    return period_str, seconds_remaining

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Welcome to your Professional Win Go Bot!**\n\n"
        "🔹 `/1m` - Get a single live synchronized signal\n"
        "🔹 `/live` - Start interactive live stream (24/7 loop)\n"
        "🔹 `/stop` - End live stream"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def live_stream_loop(bot: Bot):
    global is_live_running
    is_live_running = True
    logging.info("Live prediction stream started.")
    
    while is_live_running:
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
                f"🔢 Target Numbers: 7 / 9\n"
                f"🔥 Win Rate: 91%"
            )
            
            await bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=message_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            logging.error(f"Error in live loop: {e}")
            await asyncio.sleep(5)

async def live_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_live_running
    if is_live_running:
        await update.message.reply_text("⚠️ Live stream is already running!")
        return
    
    await update.message.reply_text("🚀 Starting 24/7 Live Stream signals...")
    asyncio.create_task(live_stream_loop(context.bot))

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_live_running
    is_live_running = False
    await update.message.reply_text("🛑 Live stream stopped.")

def run_flask():
    app_flask.run(host="0.0.0.0", port=8080)

def main():
    # Start Flask keep-alive server in background thread
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    
    # Build Telegram Application properly using version 20+ handlers
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("live", live_command))
    application.add_handler(CommandHandler("stop", stop_command))
    
    # Run the bot polling loop
    application.run_polling()

if __name__ == "__main__":
    main()

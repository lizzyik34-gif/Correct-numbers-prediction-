from datetime import datetime
import os
import threading
from flask import Flask
import telebot

# Your exact API token
TOKEN = "9055476591:AAHpG8hvCdU4_1DEnbFrvfJ3mXR0xSX7J7U"
ADMIN_CHAT_ID = 8842031370

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

is_live_running = False

@app.route('/')
def home():
    return "Bot is alive and running 24/7!"

def get_fb999_period():
    """Calculates the exact current FB999 1-minute period."""
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    total_minutes = (now.hour * 60) + now.minute
    period_index = total_minutes + 1  
    return f"{date_str}000{period_index:04d}"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🚀 **Starting Smart Sharp-Mode Live Session...**\n\n"
        "🔹 `/live` - Start 24/7 continuous signals\n"
        "🔹 `/stop` - Stop live session"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['live'])
def start_live(message):
    global is_live_running
    if is_live_running:
        bot.send_message(message.chat.id, "⚠️ Live session is already running!")
        return
    
    is_live_running = True
    bot.send_message(message.chat.id, "🚀 **Starting Smart Sharp-Mode Live Session...**", parse_mode="Markdown")
    
    # Run continuous loop in background thread
    threading.Thread(target=run_signal_loop, args=(message.chat.id,), daemon=True).start()

@bot.message_handler(commands=['stop'])
def stop_live(message):
    global is_live_running
    is_live_running = False
    bot.send_message(message.chat.id, "🛑 **Live stream successfully stopped.**", parse_mode="Markdown")

def run_signal_loop(chat_id):
    global is_live_running
    while is_live_running:
        try:
            period = get_fb999_period()
            
            markup = telebot.types.InlineKeyboardMarkup()
            markup.row(
                telebot.types.InlineKeyboardButton("✅ WIN", callback_data="win"),
                telebot.types.InlineKeyboardButton("❌ LOSS", callback_data="loss")
            )
            
            msg_text = (
                f"🔥 **WINGO_SMART_AI_PRO**\n"
                f"(((( WINGO 1 MINUTE ))))\n\n"
                f"📊 **ACTIVE PREDICTION** 📊\n"
                f"Period: `{period}` : [ SMAL ]\n"
                f"NUMBER - [ 2 ]\n\n"
                f"👇 Tap below once result appears on fb999:"
            )
            
            bot.send_message(chat_id, msg_text, parse_Mode="Markdown", reply_markup=markup)
            
            # Sync timing to the exact second the next minute rolls over
            now = datetime.now()
            sleep_time = 60 - now.second + 0.5
            
            elapsed = 0
            while elapsed < sleep_time and is_live_running:
                threading.Event().wait(1)
                elapsed += 1
                
        except Exception as e:
            print(f"Error: {e}")
            threading.Event().wait(5)

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Start Flask web server for 24/7 cloud health checks
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start Telegram bot polling
    print("Bot polling started...")
    bot.infinity_polling()

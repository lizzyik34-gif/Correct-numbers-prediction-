from datetime import datetime
import os
import threading
from flask import Flask
import telebot

TOKEN = "9237583887:AAHlhOpHgBBTT_-GXbmkOuj9m5Q3d0acogY"
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
    
    # Run the continuous loop in background thread so it doesn't block commands
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
                f"Period: `{period}` : [ BIG ]\n"
                f"NUMBER - [ 8 ]\n\n"
                f"👇 Tap below once result appears on fb999:"
            )
            
            bot.send_message(chat_id, msg_text, parse_mode="Markdown", reply_markup=markup)
            
            # Wait precisely until the next minute rolls over based on system clock
            now = datetime.now()
            sleep_time = 60 - now.second + 0.5
            
            # Sleep in small slices to instantly catch stop signals
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
    # Start Flask web server in a background thread for cloud health checks
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start Telegram bot polling
    print("Bot polling started...")
    bot.infinity_polling()

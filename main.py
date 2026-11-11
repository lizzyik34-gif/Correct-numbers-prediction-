from datetime import datetime
import os
import threading
from flask import Flask
import telebot

TOKEN = "9055476591:AAHpG8hvCdU4_1DEnbFrvfJ3mXR0xSX7J7U"
ADMIN_CHAT_ID = 8842031370

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Thread-safe lock and status flag to prevent multiple overlapping loops
is_live_running = False
loop_lock = threading.Lock()

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
        "🚀 **Smart Sharp-Mode Bot Initialized**\n\n"
        "🔹 `/live` - Start 24/7 continuous automatic signals\n"
        "🔹 `/stop` - Stop live session"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['live'])
def start_live(message):
    global is_live_running
    with loop_lock:
        if is_live_running:
            bot.send_message(message.chat.id, "⚠️ Live session is already running!")
            return
        is_live_running = True

    bot.send_message(message.chat.id, "🚀 **Starting Smart Sharp-Mode Live Session...**", parse_mode="Markdown")
    
    # Start the 24/7 background worker targeted at your Admin Chat ID
    threading.Thread(target=run_signal_loop, args=(ADMIN_CHAT_ID,), daemon=True).start()

@bot.message_handler(commands=['stop'])
def stop_live(message):
    global is_live_running
    with loop_lock:
        if not is_live_running:
            bot.send_message(message.chat.id, "⚠️ No live session is currently running.")
            return
        is_live_running = False
        
    bot.send_message(message.chat.id, "🛑 **Live stream successfully stopped.**", parse_mode="Markdown")

def run_signal_loop(target_chat_id):
    global is_live_running
    print("Background signal loop started.")
    
    while True:
        with loop_lock:
            if not is_live_running:
                break
                
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
            
            bot.send_message(target_chat_id, msg_text, parse_mode="Markdown", reply_markup=markup)
            
            # Precise time sync to the exact next minute boundary
            now = datetime.now()
            sleep_time = 60 - now.second + 0.3
            
            # Sleep in short increments so it responds to `/stop` immediately
            elapsed = 0
            while elapsed < sleep_time:
                with loop_lock:
                    if not is_live_running:
                        break
                threading.Event().wait(1)
                elapsed += 1
                
        except Exception as e:
            print(f"Loop Error: {e}")
            threading.Event().wait(5)
            
    print("Background signal loop terminated.")

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Start Flask web server in background thread for cloud hosting
    threading.Thread(target=run_flask, daemon=True).start()
    
    print("Bot polling started...")
    bot.infinity_polling()

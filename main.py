from datetime import datetime
import os
import random
import threading
from flask import Flask
import telebot

TOKEN = "9055476591:AAHpG8hvCdU4_1DEnbFrvfJ3mXR0xSX7J7U"
ADMIN_CHAT_ID = 8842031370

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

is_live_running = False
loop_lock = threading.Lock()

@app.route('/')
def home():
    return "Bot is alive and running 24/7!"

def get_fb999_period():
    """Calculates the exact current FB999 1-minute period matching fb999.com game history format."""
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    
    # Calculate exact total minutes elapsed since midnight today
    total_minutes = (now.hour * 60) + now.minute
    
    # FB999 1M sequence starts at 1 for the first minute of the day
    period_index = total_minutes + 1  
    
    # Matches format: YYYYMMDD000XXXX (e.g., 2026111100010674)
    return f"{date_str}000{period_index:04d}"

def create_prediction_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("✅ WIN", callback_data="btn_win"),
        telebot.types.InlineKeyboardButton("❌ LOSS", callback_data="btn_loss")
    )
    return markup

def send_signal(chat_id):
    period = get_fb999_period()
    
    # Generate realistic dynamic prediction values matching your screenshots
    is_big = random.choice([True, False])
    prediction_type = "BIGG" if is_big else "SMAL"
    target_number = random.randint(5, 9) if is_big else random.randint(0, 4)
    
    msg_text = (
        f"🔥 **WINGO_SMART_AI_PRO**\n"
        f"(((( WINGO 1 MINUTE ))))\n\n"
        f"Waiting for first result...\n\n"
        f"🕹️ **ACTIVE PREDICTION** 🕹️\n"
        f"Period: `{period}` : [ {prediction_type} ]\n"
        f"NUMBER - [ {target_number} ]\n\n"
        f"👇 Tap below once result appears on fb999:"
    )
    bot.send_message(chat_id, msg_text, parse_mode="Markdown", reply_markup=create_prediction_markup())

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🚀 **Smart Sharp-Mode Bot Ready**\n\n"
        "🔹 `/live` - Start 24/7 continuous signals\n"
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
    
    # Drop first signal immediately
    send_signal(message.chat.id)
    
    # Start automated background loop
    threading.Thread(target=run_signal_loop, args=(message.chat.id,), daemon=True).start()

@bot.message_handler(commands=['stop'])
def stop_live(message):
    global is_live_running
    with loop_lock:
        if not is_live_running:
            bot.send_message(message.chat.id, "⚠️ No live session is currently running.")
            return
        is_live_running = False
        
    bot.send_message(message.chat.id, "🛑 **Live stream successfully stopped.**", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data in ["btn_win", "btn_loss"])
def handle_button(call):
    result_text = "WIN 🎉" if call.data == "btn_win" else "LOSS ❌"
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=call.message.text + f"\n\n✨ **Graded as: __{result_text}__**",
            parse_mode="Markdown"
        )
    except Exception:
        pass
    
    # Drop the next period card automatically
    send_signal(call.message.chat.id)
    bot.answer_callback_query(call.id, f"Recorded as {result_text}! Next period dropped.")

def run_signal_loop(chat_id):
    global is_live_running
    while True:
        with loop_lock:
            if not is_live_running:
                break
                
        # Precise synchronization to the exact start of the next minute
        now = datetime.now()
        sleep_time = 60 - now.second + 0.3
        
        elapsed = 0
        while elapsed < sleep_time:
            with loop_lock:
                if not is_live_running:
                    break
            threading.Event().wait(1)
            elapsed += 1
            
        with loop_lock:
            if not is_live_running:
                break
                
        try:
            send_signal(chat_id)
        except Exception as e:
            print(f"Auto-loop error: {e}")

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("Bot polling started...")
    bot.infinity_polling()

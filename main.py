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

# Keep track of recent history lines for the active session
signal_history = []

@app.route('/')
def home():
    return "Bot is alive and running 24/7!"

def get_fb999_period():
    """Calculates the exact period matching fb999.com (e.g., 2026111100010684)."""
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    
    # Total minutes elapsed since midnight
    total_minutes = (now.hour * 60) + now.minute
    
    # Matches the exact game sequence prefix + running minute index
    period_index = total_minutes + 1  
    return f"{date_str}0001{period_index:04d}"

def create_prediction_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("✅ WIN", callback_data="btn_win"),
        telebot.types.InlineKeyboardButton("❌ LOSS", callback_data="btn_loss")
    )
    return markup

def build_message_text(active_period, pred_type, target_num):
    history_block = "\n".join(signal_history[-5:]) if signal_history else "Initializing history..."
    
    text = (
        f"🔥 WINGO SMART AI PRO\n"
        f"(((( WINGO 1 MINUTE ))))\n\n"
        f"{history_block}\n\n"
        f"🕹️ ACTIVE PREDICTION 🕹️\n"
        f"Period: {active_period} : [ {pred_type} ]\n"
        f"NUMBER - [ {target_num} ]\n\n"
        f"👇 Tap below once result appears on fb999:"
    )
    return text

def send_signal(chat_id):
    period = get_fb999_period()
    is_big = random.choice([True, False])
    pred_type = "BIGG" if is_big else "SMAL"
    target_num = random.randint(5, 9) if is_big else random.randint(0, 4)
    
    msg_text = build_message_text(period, pred_type, target_num)
    
    try:
        sent_msg = bot.send_message(chat_id, msg_text, reply_markup=create_prediction_markup())
        return sent_msg
    except Exception as e:
        print(f"Error sending signal: {e}")
        return None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, "🚀 Smart Sharp-Mode Bot Ready\n\n🔹 /live - Start signals\n🔹 /stop - Stop session")

@bot.message_handler(commands=['live'])
def start_live(message):
    global is_live_running, signal_history
    with loop_lock:
        if is_live_running:
            bot.send_message(message.chat.id, "⚠️ Live session is already running!")
            return
        is_live_running = True
        signal_history.clear()

    bot.send_message(message.chat.id, "🚀 Starting Smart Sharp-Mode Live Session...")
    send_signal(message.chat.id)
    
    threading.Thread(target=run_signal_loop, args=(message.chat.id,), daemon=True).start()

@bot.message_handler(commands=['stop'])
def stop_live(message):
    global is_live_running
    with loop_lock:
        if not is_live_running:
            bot.send_message(message.chat.id, "⚠️ No live session is currently running.")
            return
        is_live_running = False
        
    bot.send_message(message.chat.id, "🛑 Live stream successfully stopped.")

@bot.callback_query_handler(func=lambda call: call.data in ["btn_win", "btn_loss"])
def handle_button(call):
    global signal_history
    is_win = (call.data == "btn_win")
    
    # Updated symbols: ✅ for win, ❌ for loss
    result_label = "WIN ✅" if is_win else "LOSS ❌"
    
    lines = call.message.text.split('\n')
    try:
        for line in lines:
            if "Period:" in line:
                parts = line.split(":")
                p_num = parts[1].strip().split(" ")[0]
                p_type = parts[2].strip().replace("[", "").replace("]", "").strip()
                signal_history.append(f"PEREOD :- {p_num} {p_type} {result_label}")
                break
    except Exception:
        signal_history.append(f"PEREOD :- RECORDED {result_label}")
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    
    send_signal(call.message.chat.id)
    bot.answer_callback_query(call.id, f"Recorded as {result_label}!")

def run_signal_loop(chat_id):
    global is_live_running
    while True:
        with loop_lock:
            if not is_live_running:
                break
                
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

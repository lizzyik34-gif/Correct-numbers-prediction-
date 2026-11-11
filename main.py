from datetime import datetime
import os
import random
import threading
from flask import Flask
import telebot

TOKEN = "9055476591:AAHpG8hvCdU4_1DEnbFrvfJ3mXR0xSX7J7U"
ADMIN_CHAT_ID = 8842031370

AUTHORIZED_USERS = {
    8842031370: {"name": "Admin", "win_limit": 999999},
    7406955427: {"name": "User", "win_limit": 100}
}

daily_win_tracker = {}

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

is_live_running = False
loop_lock = threading.Lock()

signal_history = []
active_message_id = None
active_chat_id = None
current_period = ""
current_pred_type = ""
current_target_num = ""

@app.route('/')
def home():
    return "Bot is alive and running 24/7!"

def get_fb999_period():
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    total_minutes = (now.hour * 60) + now.minute
    period_index = total_minutes + 1  
    return f"{date_str}0001{period_index:04d}"

def create_prediction_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("✅ WIN", callback_data="btn_win"),
        telebot.types.InlineKeyboardButton("❌ LOSS", callback_data="btn_loss")
    )
    return markup

def build_message_text():
    history_block = "\n".join(signal_history[-10:]) if signal_history else "Waiting for first result..."
    
    text = (
        f"🔥 WINGO SMART AI PRO\n"
        f"(((( WINGO 1 MINUTE ))))\n\n"
        f"{history_block}\n\n"
        f"🕹️ ACTIVE PREDICTION 🕹️\n"
        f"Period: {current_period} : [ {current_pred_type} ]\n"
        f"NUMBER - [ {current_target_num} ]\n\n"
        f"👇 Tap below once result appears on fb999:"
    )
    return text

def refresh_or_send_signal(chat_id):
    global active_message_id, active_chat_id, current_period, current_pred_type, current_target_num
    active_chat_id = chat_id
    current_period = get_fb999_period()
    
    is_big = random.choice([True, False])
    current_pred_type = "BIGG" if is_big else "SMAL"
    current_target_num = random.randint(5, 9) if is_big else random.randint(0, 4)
    
    msg_text = build_message_text()
    
    if active_message_id:
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=active_message_id,
                text=msg_text,
                reply_markup=create_prediction_markup()
            )
            return
        except Exception:
            pass
            
    try:
        sent_msg = bot.send_message(chat_id, msg_text, reply_markup=create_prediction_markup())
        active_message_id = sent_msg.message_id
    except Exception as e:
        print(f"Error sending signal: {e}")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        bot.send_message(message.chat.id, "⛔ Access Denied. You are not authorized to use this bot.")
        return
    bot.send_message(message.chat.id, "🚀 Smart Sharp-Mode Bot Ready\n\n🔹 /live - Start signals\n🔹 /stop - Stop session")

@bot.message_handler(commands=['live'])
def start_live(message):
    global is_live_running, signal_history, active_message_id
    user_id = message.from_user.id
    
    if user_id not in AUTHORIZED_USERS:
        bot.send_message(message.chat.id, "⛔ Access Denied.")
        return
        
    with loop_lock:
        if is_live_running:
            bot.send_message(message.chat.id, "⚠️ Live session is already running!")
            return
        is_live_running = True
        signal_history.clear()
        active_message_id = None

    bot.send_message(message.chat.id, "🚀 Starting Smart Sharp-Mode Live Session...")
    refresh_or_send_signal(message.chat.id)

@bot.message_handler(commands=['stop'])
def stop_live(message):
    global is_live_running, active_message_id
    user_id = message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        return
        
    with loop_lock:
        if not is_live_running:
            bot.send_message(message.chat.id, "⚠️ No live session is currently running.")
            return
        is_live_running = False
        active_message_id = None
        
    bot.send_message(message.chat.id, "🛑 Live stream successfully stopped.")

@bot.callback_query_handler(func=lambda call: call.data in ["btn_win", "btn_loss"])
def handle_button(call):
    global signal_history
    user_id = call.from_user.id
    
    if user_id not in AUTHORIZED_USERS:
        bot.answer_callback_query(call.id, "⛔ Unauthorized user.", show_alert=True)
        return

    is_win = (call.data == "btn_win")
    
    today_str = datetime.now().strftime("%Y%m%d")
    if is_win:
        if user_id not in daily_win_tracker or daily_win_tracker[user_id]["date"] != today_str:
            daily_win_tracker[user_id] = {"date": today_str, "wins": 0}
            
        limit = AUTHORIZED_USERS[user_id]["win_limit"]
        if daily_win_tracker[user_id]["wins"] >= limit:
            bot.answer_callback_query(call.id, f"⚠️ Daily win limit of {limit} reached for today!", show_alert=True)
            return
            
        daily_win_tracker[user_id]["wins"] += 1

    result_label = "WIN ✅" if is_win else "LOSS ❌"
    
    # Capture the period being graded right now before shifting forward
    short_period = current_period[-5:] if len(current_period) >= 5 else current_period
    signal_history.append(f"PEREOD :- ...{short_period} {current_pred_type} {result_label}")
    
    if len(signal_history) > 10:
        signal_history.pop(0)
        
    # Instantly update and drop the next period right upon button click!
    refresh_or_send_signal(call.message.chat.id)
    
    remaining = AUTHORIZED_USERS[user_id]["win_limit"] - daily_win_tracker.get(user_id, {}).get("wins", 0)
    bot.answer_callback_query(call.id, f"Recorded! Today's wins left: {remaining}")

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("Bot polling started...")
    bot.infinity_polling()

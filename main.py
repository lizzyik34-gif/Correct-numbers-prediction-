import time
import json
import random
import urllib.request
import threading
import os
from datetime import datetime, timezone, date
from flask import Flask

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "render-secure-key-2026")

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "9055476591:AAEli2KQDFMbda-yed7J"

# 1. Unlimited Admin IDs (Fully protected from limits/trials)
UNLIMITED_USER_IDS = ["8842031370", "7891601316"]

# 2. Daily Limited Users (60 signals per day)
LIMITED_USERS = {
    "8882241036": {"limit": 60, "used": 0, "last_date": ""},
    "7406955427": {"limit": 60, "used": 0, "last_date": ""}
}

# 3. SPECIAL USER IDs (40 Wins Access)
SPECIAL_40_WINS_USERS = ["1028206063"]

# 4. STANDARD FREE TRIAL USERS (7 Wins Access)
APPROVED_TRIALS = [
    "9063263288",
    "9001526776"
]

# Active live sessions dictionary to handle /stop functionality per chat
ACTIVE_LIVE_SESSIONS = {}

TRIALS_FILE = "trials.json"

def load_trials():
    if os.path.exists(TRIALS_FILE):
        try:
            with open(TRIALS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_trials(data):
    try:
        with open(TRIALS_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving trials: {e}")

@app.route("/")
def index():
    return "FB999 Telegram Bot & Live Stream Service is Active!"

def telegram_bot_polling():
    offset = 0
    print("Telegram bot polling started...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=35) as response:
                data = json.loads(response.read().decode())
                if data.get("ok"):
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        message = update.get("message")
                        if message and "text" in message:
                            chat_id = str(message["chat"]["id"])
                            text = message["text"].strip()
                            
                            if text == "/start":
                                reply_text = (
                                    "👋 Welcome to your Professional Win Go Bot!\n\n"
                                    "Commands:\n"
                                    "🔹 /result - Get a single signal\n"
                                    "🔹 /live - Start non-stop automated live predictions\n"
                                    "🔹 /stop - Stop the active live stream"
                                )
                                send_telegram_message(chat_id, reply_text)
                            elif text == "/result":
                                handle_single_signal(chat_id)
                            elif text == "/live":
                                start_live_stream(chat_id)
                            elif text == "/stop":
                                stop_live_stream(chat_id)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

def send_telegram_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Error sending message: {e}")

def check_user_access(chat_id):
    today_str = str(date.today())
    if chat_id in UNLIMITED_USER_IDS:
        return True
    elif chat_id in LIMITED_USERS:
        user_data = LIMITED_USERS[chat_id]
        if user_data["last_date"] != today_str:
            user_data["last_date"] = today_str
            user_data["used"] = 0
        if user_data["used"] >= user_data["limit"]:
            return False
        user_data["used"] += 1
        return True
    elif chat_id in APPROVED_TRIALS or chat_id in SPECIAL_40_WINS_USERS:
        return True
    return False

def generate_signal_text():
    now = datetime.now(timezone.utc)
    period = now.strftime("%Y%m%d") + "1000" + str(random.randint(10000, 99999))
    size = random.choice(["BIG", "SMALL"])
    number = random.randint(5, 9) if size == "BIG" else random.randint(0, 4)
    confidence = random.randint(60, 96)
    
    return (
        f"📊 **WIN GO LIVE SIGNAL (1M)**\n\n"
        f"🔹 Period: `{period}`\n"
        f"📈 Current Level: Stage 1 / 6\n"
        f"🔹 Number Prediction: {number}\n"
        f"🔹 Size: **{size}**\n"
        f"🔥 Confidence Rate: {confidence}%"
    )

def handle_single_signal(chat_id):
    if not check_user_access(chat_id):
        send_telegram_message(chat_id, "❌ Daily signal limit reached or access denied.")
        return
    send_telegram_message(chat_id, generate_signal_text())

def start_live_stream(chat_id):
    if chat_id in ACTIVE_LIVE_SESSIONS and ACTIVE_LIVE_SESSIONS[chat_id]:
        send_telegram_message(chat_id, "⚠️ Live stream is already running! Send `/stop` to end it first.")
        return

    if not check_user_access(chat_id):
        send_telegram_message(chat_id, "❌ Access denied or daily limit reached.")
        return

    ACTIVE_LIVE_SESSIONS[chat_id] = True
    send_telegram_message(chat_id, "🚀 **Live Stream Started!** Automatically dropping continuous signals. Send `/stop` anytime to halt.")

    def run_stream():
        while ACTIVE_LIVE_SESSIONS.get(chat_id, False):
            if not check_user_access(chat_id):
                send_telegram_message(chat_id, "❌ Daily limit reached. Stopping live stream.")
                break
            
            signal_msg = generate_signal_text()
            send_telegram_message(chat_id, signal_msg)
            
            # Wait 30 seconds or interval before pushing the next automatic prediction
            for _ in range(30):
                if not ACTIVE_LIVE_SESSIONS.get(chat_id, False):
                    break
                time.sleep(1)

        ACTIVE_LIVE_SESSIONS[chat_id] = False
        send_telegram_message(chat_id, "🛑 **Live Stream Stopped.**")

    threading.Thread(target=run_stream, daemon=True).start()

def stop_live_stream(chat_id):
    if chat_id in ACTIVE_LIVE_SESSIONS and ACTIVE_LIVE_SESSIONS[chat_id]:
        ACTIVE_LIVE_SESSIONS[chat_id] = False
        send_telegram_message(chat_id, "🛑 Stopping live stream...")
    else:
        send_telegram_message(chat_id, "ℹ️ No active live stream found.")

if __name__ == "__main__":
    bot_thread = threading.Thread(target=telegram_bot_polling, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

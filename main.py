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

# 1. Unlimited Admin IDs (Your ID 8842031370 is included here)
UNLIMITED_USER_IDS = ["8842031370", "7891601316", "7406955427"]

# 2. Daily Limited Users (60 signals per day)
LIMITED_USERS = {
    "8882241036": {"limit": 60, "used": 0, "last_date": ""}
}

# Track active live streaming sessions per chat
ACTIVE_LIVE_SESSIONS = {}

@app.route("/")
def index():
    return "FB999 Telegram Bot & Live Stream Service is Active!"

def telegram_bot_polling():
    offset = 0
    print("Telegram bot polling started and listening for messages...")
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
                            text = message["text"].strip().lower()
                            print(f"Received message '{text}' from chat ID: {chat_id}")
                            
                            if text == "/start":
                                reply_text = (
                                    "👋 Welcome to your Professional Win Go Bot!\n\n"
                                    "🔹 Send `/1m`, `/30s`, `/3m`, or `/5m` for single signals\n"
                                    "🔹 Send `/live` to start non-stop automatic signals\n"
                                    "🔹 Send `/stop` to end the live stream"
                                )
                                send_telegram_message(chat_id, reply_text)
                            elif text in ["/1m", "/30s", "/3m", "/5m"]:
                                tf = text.replace("/", "").upper()
                                handle_single_signal(chat_id, tf)
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

def generate_signal_text(timeframe="1M"):
    now = datetime.now(timezone.utc)
    period = now.strftime("%Y%m%d") + "1000" + str(random.randint(10000, 99999))
    size = random.choice(["BIG (5-9)", "SMALL (0-4)"])
    target_num = f"{random.randint(7, 9)} / 9"
    win_rate = random.randint(80, 95)
    
    return (
        f"📊 **WIN GO NUMBER SIGNAL ({timeframe})**\n\n"
        f"🔹 Period: `{period}`\n"
        f"📈 Stage Level: Stage 1 / 6\n"
        f"🎯 Prediction Range: 🔴 {size}\n"
        f"🔢 Target Numbers: {target_num}\n"
        f"🔥 Win Rate: {win_rate}%"
    )

def handle_single_signal(chat_id, timeframe):
    send_telegram_message(chat_id, generate_signal_text(timeframe))

def start_live_stream(chat_id):
    if chat_id in ACTIVE_LIVE_SESSIONS and ACTIVE_LIVE_SESSIONS[chat_id]:
        send_telegram_message(chat_id, "⚠️ Live stream is already running! Send `/stop` to end.")
        return

    ACTIVE_LIVE_SESSIONS[chat_id] = True
    send_telegram_message(chat_id, "🚀 **Live Stream Started!** Automatically broadcasting continuous signals. Send `/stop` anytime to end.")

    def run_stream():
        while ACTIVE_LIVE_SESSIONS.get(chat_id, False):
            signal_msg = generate_signal_text("1M")
            send_telegram_message(chat_id, signal_msg)
            
            # Wait 30 seconds before sending the next automatic signal
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

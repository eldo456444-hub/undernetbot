import os
from flask import Flask, request
import telebot

TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)
ADMIN_CHAT_ID = int(os.environ.get('ADMIN_CHAT_ID', -4881160812))

app = Flask(__name__)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def home():
    return "ok"

bot.remove_webhook()
bot.set_webhook(url=f"https://undernetbot-2.onrender.com/{TOKEN}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

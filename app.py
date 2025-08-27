# app.py
import os, threading, time
from flask import Flask
import telebot

# 🔑 токен берём из переменных окружения Render
TOKEN = os.environ['TOKEN']
bot = telebot.TeleBot(TOKEN)

# 🔒 ID твоего чата или канала
ADMIN_CHAT_ID = -4881160812  # замени на свой id

# --- Команда /start ---
@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "<b>👋 Привет! Ты в предложке канала UnderNet.</b>\n\n"
        "Здесь ты можешь:\n"
        "— Предложить идею для поста\n"
        "— Попросить разобрать сайт\n"
        "— Поделиться находкой из интернета\n\n"
        "✍️ Просто напиши сообщение сюда, и оно попадёт админу.\n\n"
        "⚡️ Все твои идеи важны — спасибо, что участвуешь в проекте!\n\n"
        "(Только отправляй всё в одном сообщении. Спасибо🙏)\n"
    )
    bot.reply_to(message, welcome_text, parse_mode='html')

# --- Текстовые сообщения ---
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_message = message.text
    bot.reply_to(message, "Спасибо! Я передал твою идею автору ✅")
    bot.send_message(
        ADMIN_CHAT_ID,
        f"💡 Новая идея от @{message.from_user.username or message.from_user.id}:\n\n{user_message}"
    )

# --- Фото с подписью ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    caption = message.caption or "(без подписи)"
    bot.reply_to(message, "Спасибо за фото! Я передал его автору ✅")
    file_id = message.photo[-1].file_id
    bot.send_photo(
        ADMIN_CHAT_ID,
        file_id,
        caption=f"📷 Новая идея от @{message.from_user.username or message.from_user.id}:\n\n{caption}"
    )

# --- Flask для Render ---
app = Flask(__name__)

@app.route("/")
def home():
    return "ok"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def run_bot():
    while True:
        try:
            print("Бот запущен...")
            bot.infinity_polling(skip_pending=True, timeout=10, long_polling_timeout=20)
        except Exception as e:
            print("Bot error:", e)
            time.sleep(3)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()

import os
import threading
import time
from flask import Flask
import telebot

# 🔑 Токен берём из переменных окружения Render
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

# --- Универсальный ответ ---
def send_acknowledgement(message):
    bot.reply_to(message, "Спасибо за сообщение!")

# --- Текстовые сообщения ---
@bot.message_handler(content_types=['text'])
def handle_text(message):
    send_acknowledgement(message)
    bot.send_message(
        ADMIN_CHAT_ID,
        f"💡 Новое сообщение от @{message.from_user.username or message.from_user.id}:\n\n{message.text}"
    )

# --- Фото ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    send_acknowledgement(message)
    caption = message.caption or "(без подписи)"
    file_id = message.photo[-1].file_id
    bot.send_photo(
        ADMIN_CHAT_ID,
        file_id,
        caption=f"📷 Новое фото от @{message.from_user.username or message.from_user.id}:\n\n{caption}"
    )

# --- Видео ---
@bot.message_handler(content_types=['video'])
def handle_video(message):
    send_acknowledgement(message)
    caption = message.caption or "(без подписи)"
    file_id = message.video.file_id
    bot.send_video(
        ADMIN_CHAT_ID,
        file_id,
        caption=f"🎥 Новое видео от @{message.from_user.username or message.from_user.id}:\n\n{caption}"
    )

# --- Аудио ---
@bot.message_handler(content_types=['audio'])
def handle_audio(message):
    send_acknowledgement(message)
    file_id = message.audio.file_id
    bot.send_audio(
        ADMIN_CHAT_ID,
        file_id,
        caption=f"🎵 Новое аудио от @{message.from_user.username or message.from_user.id}"
    )

# --- Документы ---
@bot.message_handler(content_types=['document'])
def handle_document(message):
    send_acknowledgement(message)
    file_id = message.document.file_id
    bot.send_document(
        ADMIN_CHAT_ID,
        file_id,
        caption=f"📎 Новый документ от @{message.from_user.username or message.from_user.id}"
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

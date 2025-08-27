import os
import threading
import time
from flask import Flask
import telebot

# 🔑 Токен из переменных окружения Render
TOKEN = os.environ['TOKEN']
bot = telebot.TeleBot(TOKEN)

# 🔒 ID вашего чата или канала
ADMIN_CHAT_ID = -4881160812  # замените на свой ID

# --- Flask для Render ---
app = Flask(__name__)

@app.route("/")
def home():
    return "ok"

# --- /start ---
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
        "✍️ Сначала напиши своё сообщение или идею."
    )
    bot.reply_to(message, welcome_text, parse_mode='html')
    bot.register_next_step_handler(message, handle_text_step)

# --- Этап 1: текстовое сообщение ---
def handle_text_step(message):
    user_text = message.text
    bot.send_message(message.chat.id, "Спасибо за сообщение! Теперь можешь прислать фото/видео. Если не хочешь — напиши 'нет'.")
    bot.register_next_step_handler(message, handle_media_step, user_text)

# --- Этап 2: фото/видео ---
def handle_media_step(message, user_text):
    # Отправляем текст админу
    bot.send_message(ADMIN_CHAT_ID,
                     f"💡 Новое сообщение от @{message.from_user.username or message.from_user.id}:\n\n{user_text}")

    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        bot.send_photo(ADMIN_CHAT_ID, file_id,
                       caption=f"📷 От @{message.from_user.username or message.from_user.id}")
    elif message.content_type == 'video':
        file_id = message.video.file_id
        bot.send_video(ADMIN_CHAT_ID, file_id,
                       caption=f"🎥 От @{message.from_user.username or message.from_user.id}")
    elif message.text.lower() == 'нет':
        bot.send_message(message.chat.id, "Хорошо, нет так нет!")
        return
    else:
        bot.send_message(message.chat.id, "Неправильный формат. Присылай фото/видео или напиши 'нет'.")
        bot.register_next_step_handler(message, handle_media_step, user_text)
        return

    bot.send_message(message.chat.id, "Спасибо! Все данные отправлены автору ✅")

# --- Запуск Flask и бота ---
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

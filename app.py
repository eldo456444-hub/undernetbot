import os
import threading
import time
from flask import Flask
import telebot
from telebot.types import InputMediaPhoto, InputMediaVideo

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

# Словарь для хранения данных пользователей в сессии
user_sessions = {}

MAX_MEDIA = 4  # максимальное количество медиа

# --- /start ---
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_sessions[chat_id] = {'text': None, 'media': []}
    bot.reply_to(message,
                 "<b>👋 Привет! Ты в предложке канала UnderNet.</b>\n\n"
                 "Здесь ты можешь:\n"
                 "— Предложить идею для поста\n"
                 "— Попросить разобрать сайт\n"
                 "— Поделиться находкой из интернета\n\n"
                 "✍️ Просто напиши сообщение сюда, и оно попадёт админу.\n\n"
                 "⚡️ Все твои идеи важны — спасибо, что участвуешь в проекте!\n\n"
                 "💡Сначала напиши текст своего сообщения или идеи."
                 )
    bot.register_next_step_handler(message, handle_text_step)

# --- Этап 1: текстовое сообщение ---
def handle_text_step(message):
    chat_id = message.chat.id
    user_sessions[chat_id]['text'] = message.text
    bot.send_message(chat_id, "✅Текст получен!\n"
                              "📷Хочешь отправить фото/видео? Если нет — напиши 'нет'. Если да - пиши 'да'")
    bot.register_next_step_handler(message, handle_media_prompt)

# --- Этап 2: спрашиваем про медиа ---
def handle_media_prompt(message):
    chat_id = message.chat.id
    if message.text.lower() == 'нет':
        bot.send_message(chat_id, "✅Окей, спасибо! Уже бегу к админу с твоим сообщением!")
        send_to_admin(chat_id)
        user_sessions.pop(chat_id)
    else:
        bot.send_message(chat_id, f"Отправляй фото/видео (0/{MAX_MEDIA})")
        bot.register_next_step_handler(message, handle_media_step)

# --- Этап 3: приём медиа ---
def handle_media_step(message):
    chat_id = message.chat.id
    session = user_sessions.get(chat_id)
    if session is None:
        bot.send_message(chat_id, "⛔Сессия не найдена. Начни с /start")
        return

    # Проверка лимита
    if len(session['media']) >= MAX_MEDIA:
        bot.send_message(chat_id, f"⛔Нельзя отправлять больше {MAX_MEDIA} медиа!")
        bot.send_message(chat_id, "👌Если хочешь, заверши отправку, напиши 'да'.")
        bot.register_next_step_handler(message, handle_media_confirm)
        return

    # Добавляем медиа
    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        session['media'].append({'type': 'photo', 'file_id': file_id})
    elif message.content_type == 'video':
        file_id = message.video.file_id
        session['media'].append({'type': 'video', 'file_id': file_id})
    elif message.text.lower() == 'да':
        bot.send_message(chat_id, "❤Спасибо! Уже бегу к админу с твоим сообщением!")
        send_to_admin(chat_id)
        user_sessions.pop(chat_id)
        return
    else:
        bot.send_message(chat_id, "⛔Неправильный формат. Присылай фото/видео или напиши 'да', если закончил.")
        bot.register_next_step_handler(message, handle_media_step)
        return

    count = len(session['media'])
    if count >= MAX_MEDIA:
        bot.send_message(chat_id, f"{count}/{MAX_MEDIA} — достигнут лимит!")
        bot.send_message(chat_id, "❤Спасибо! Уже бегу к админу с твоим сообщением!")
        send_to_admin(chat_id)
        user_sessions.pop(chat_id)
    else:
        bot.send_message(chat_id, f"{count}/{MAX_MEDIA}, 👌это все? Если да — напиши 'да', если нет — присылай дальше.")
        bot.register_next_step_handler(message, handle_media_step)

def handle_media_confirm(message):
    chat_id = message.chat.id
    if message.text.lower() == 'да':
        bot.send_message(chat_id, "❤Спасибо! Уже бегу к админу с твоим сообщением!")
        send_to_admin(chat_id)
        user_sessions.pop(chat_id)
    else:
        bot.send_message(chat_id, "Присылай дальше фото/видео.")
        bot.register_next_step_handler(message, handle_media_step)

# --- Функция отправки админу ---
def send_to_admin(chat_id):
    session = user_sessions.get(chat_id)
    if session is None:
        return

    username = bot.get_chat(chat_id).username or chat_id

    # 1️⃣ Отправляем текст
    text = session['text'] or "(нет текста)"
    bot.send_message(ADMIN_CHAT_ID, f"💡 Новое сообщение от @{username}:\n\n{text}")

    # 2️⃣ Отправляем медиагруппу, если есть
    media_list = []
    for m in session['media']:
        if m['type'] == 'photo':
            media_list.append(InputMediaPhoto(media=m['file_id']))
        elif m['type'] == 'video':
            media_list.append(InputMediaVideo(media=m['file_id']))

    if media_list:
        # Отправка медиагруппы
        bot.send_media_group(ADMIN_CHAT_ID, media_list)

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

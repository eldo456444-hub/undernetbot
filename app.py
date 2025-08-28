import os
import threading
import time
from flask import Flask
import telebot
from telebot.types import InputMediaPhoto, InputMediaVideo

# токен берём из переменных окружения
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# замените на свой ID
ADMIN_CHAT_ID = -4881160812

app = Flask(__name__)

@app.route("/")
def home():
    return "ok"

# сессии пользователей
user_sessions = {}
MAX_MEDIA = 4

def reset_session(chat_id):
    """Сброс сессии для пользователя."""
    user_sessions[chat_id] = {'text': None, 'media': []}

def is_again_command(message):
    """Проверяем, хочет ли пользователь начать заново."""
    if message is None or message.text is None:
        return False
    t = message.text.strip().lower()
    return t == '/again' or t == 'again' or t == '/start'

# --- старт и /again как команда (для надёжности) ---
@bot.message_handler(commands=['start'])
def cmd_start(message):
    chat_id = message.chat.id
    reset_session(chat_id)
    bot.reply_to(
        message,
        "<b>👋 Привет! Ты в предложке канала UnderNet.</b>\n\n"
        "Здесь ты можешь:\n"
        "— Предложить идею для поста\n"
        "— Попросить разобрать сайт\n"
        "— Поделиться находкой из интернета\n\n"
        "✍️ Просто напиши сообщение сюда, и оно попадёт админу.\n\n"
        "⚡️ Все твои идеи важны — спасибо, что участвуешь в проекте!\n\n"
        "💡Сначала напиши текст своего сообщения или идеи.",
        parse_mode='HTML'
    )
    bot.register_next_step_handler(message, handle_text_step)

@bot.message_handler(commands=['again'])
def cmd_again(message):
    # Команда /again работает в любом состоянии
    chat_id = message.chat.id
    reset_session(chat_id)
    bot.reply_to(
        message,
        "<b>🔄 Начнём заново!</b>\n\nПожалуйста, напиши текст своего сообщения или идеи.",
        parse_mode='HTML'
    )
    bot.register_next_step_handler(message, handle_text_step)

# --- Шаг 1: текст ---
def handle_text_step(message):
    chat_id = message.chat.id

    # если пользователь ввёл /again или /start в этот момент — перезапускаем
    if is_again_command(message):
        reset_session(chat_id)
        bot.reply_to(message, "<b>🔄 Начнём заново!</b>\n\nПожалуйста, напиши текст.", parse_mode='HTML')
        bot.register_next_step_handler(message, handle_text_step)
        return

    # сохраняем текст
    user_sessions.setdefault(chat_id, {'text': None, 'media': []})
    user_sessions[chat_id]['text'] = message.text
    bot.send_message(chat_id, "✅ Текст получен!\n📷 Хочешь отправить фото/видео? Напиши 'да' или 'нет'.")
    bot.register_next_step_handler(message, handle_media_prompt)

# --- Шаг 2: спрашиваем про медиа ---
def handle_media_prompt(message):
    chat_id = message.chat.id

    # если команда /again — сразу начинаем заново
    if is_again_command(message):
        reset_session(chat_id)
        bot.reply_to(message, "<b>🔄 Начнём заново!</b>\n\nПожалуйста, напиши текст.", parse_mode='HTML')
        bot.register_next_step_handler(message, handle_text_step)
        return

    text = (message.text or "").strip().lower()
    if text == 'нет':
        bot.send_message(chat_id, "✅ Окей! Уже бегу к админу с твоим сообщением!")
        send_to_admin(chat_id)
        user_sessions.pop(chat_id, None)
    elif text == 'да':
        bot.send_message(chat_id, f"Отправляй фото/видео (0/{MAX_MEDIA})")
        bot.register_next_step_handler(message, handle_media_step)
    else:
        bot.send_message(chat_id, "⛔ Не понял? Напиши 'да' или 'нет'.")
        bot.register_next_step_handler(message, handle_media_prompt)

# --- Шаг 3: приём медиа ---
def handle_media_step(message):
    chat_id = message.chat.id

    # если команда /again — перезапускаем
    if is_again_command(message):
        reset_session(chat_id)
        bot.reply_to(message, "<b>🔄 Начнём заново!</b>\n\nПожалуйста, напиши текст.", parse_mode='HTML')
        bot.register_next_step_handler(message, handle_text_step)
        return

    session = user_sessions.get(chat_id)
    if session is None:
        bot.send_message(chat_id, "⛔ Сессия не найдена. Начни с /start")
        return

    # проверка лимита
    if len(session['media']) >= MAX_MEDIA:
        bot.send_message(chat_id, f"⛔ Нельзя отправлять больше {MAX_MEDIA} медиа!")
        bot.send_message(chat_id, "👌 Если хочешь, заверши отправку, напиши 'да'.")
        bot.register_next_step_handler(message, handle_media_confirm)
        return

    # принимаем медиа
    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        session['media'].append({'type': 'photo', 'file_id': file_id})
    elif message.content_type == 'video':
        file_id = message.video.file_id
        session['media'].append({'type': 'video', 'file_id': file_id})
    elif (message.text or "").strip().lower() == 'да':
        bot.send_message(chat_id, "❤ Спасибо! Уже бегу к админу с твоим сообщением!")
        send_to_admin(chat_id)
        user_sessions.pop(chat_id, None)
        return
    else:
        bot.send_message(chat_id, "⛔ Неправильный формат. Присылай фото/видео или напиши 'да', если закончил.")
        bot.register_next_step_handler(message, handle_media_step)
        return

    count = len(session['media'])
    if count >= MAX_MEDIA:
        bot.send_message(chat_id, f"{count}/{MAX_MEDIA} — достигнут лимит!")
        bot.send_message(chat_id, "❤ Спасибо! Уже бегу к админу с твоим сообщением!")
        send_to_admin(chat_id)
        user_sessions.pop(chat_id, None)
    else:
        bot.send_message(chat_id, f"{count}/{MAX_MEDIA}, 👌 это всё? Если да — напиши 'да', если нет — присылай дальше.")
        bot.register_next_step_handler(message, handle_media_step)

def handle_media_confirm(message):
    chat_id = message.chat.id
    if is_again_command(message):
        reset_session(chat_id)
        bot.reply_to(message, "<b>🔄 Начнём заново!</b>\n\nПожалуйста, напиши текст.", parse_mode='HTML')
        bot.register_next_step_handler(message, handle_text_step)
        return

    if (message.text or "").strip().lower() == 'да':
        bot.send_message(chat_id, "❤ Спасибо! Уже бегу к админу с твоим сообщением!")
        send_to_admin(chat_id)
        user_sessions.pop(chat_id, None)
    else:
        bot.send_message(chat_id, "Присылай дальше фото/видео.")
        bot.register_next_step_handler(message, handle_media_step)

# --- отправка админу (текст отдельно, затем медиагруппа) ---
def send_to_admin(chat_id):
    session = user_sessions.get(chat_id)
    if not session:
        return

    username = bot.get_chat(chat_id).username or chat_id
    text = session['text'] or "(нет текста)"
    bot.send_message(ADMIN_CHAT_ID, f"💡 Новое сообщение от @{username}:\n\n{text}")

    if session['media']:
        media_group = []
        for m in session['media']:
            if m['type'] == 'photo':
                media_group.append(InputMediaPhoto(m['file_id']))
            elif m['type'] == 'video':
                media_group.append(InputMediaVideo(m['file_id']))
        # отправляем медиагруппу (до 10 элементов, у нас MAX_MEDIA=4)
        bot.send_media_group(ADMIN_CHAT_ID, media_group)

# --- запуск ---
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
    # убедись, что TOKEN и ADMIN_CHAT_ID корректны
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()

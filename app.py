from telegram import Update, InputMediaPhoto, InputMediaVideo, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# --- состояния ---
TEXT, MEDIA_DECISION, MEDIA = range(3)

# --- хранилище данных ---
user_data = {}

# --- старт ---
def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id] = {"text": None, "media": []}

    update.message.reply_text(
        "<b>👋 Привет! Ты в предложке канала UnderNet.</b>\n\n"
        "Здесь ты можешь:\n"
        "— Предложить идею для поста\n"
        "— Попросить разобрать сайт\n"
        "— Поделиться находкой из интернета\n\n"
        "✍️ Просто напиши сообщение сюда, и оно попадёт админу.\n\n"
        "⚡️ Все твои идеи важны — спасибо, что участвуешь в проекте!\n\n"
        "💡Сначала напиши текст своего сообщения или идеи.",
        parse_mode=ParseMode.HTML
    )
    return TEXT

# --- обработка текста ---
def handle_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id]["text"] = update.message.text

    update.message.reply_text(
        "Хочешь добавить фото/видео?\nНапиши 'да' или 'нет'."
    )
    return MEDIA_DECISION

# --- выбор медиа ---
def handle_media_decision(update: Update, context: CallbackContext):
    text = update.message.text.lower()
    if text == "да":
        update.message.reply_text("Отправляй фото или видео (максимум 4).\n0/4")
        return MEDIA
    elif text == "нет":
        send_to_admin(update, context)
        return ConversationHandler.END
    else:
        update.message.reply_text("Не понял? Напиши ещё раз: 'да' или 'нет'.")
        return MEDIA_DECISION

# --- загрузка медиа ---
def handle_media(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    media_list = user_data[user_id]["media"]

    if len(media_list) >= 4:
        update.message.reply_text("❌ Нельзя отправлять больше 4 фото/видео!")
        return MEDIA

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        media_list.append(("photo", file_id))
    elif update.message.video:
        file_id = update.message.video.file_id
        media_list.append(("video", file_id))

    count = len(media_list)
    update.message.reply_text(
        f"{count}/4. Это всё? Напиши 'да' или продолжай отправлять."
    )
    return MEDIA_DECISION

# --- неправильный ввод на этапе выбора медиа ---
def wrong_input_media_decision(update: Update, context: CallbackContext):
    update.message.reply_text("Не понял? Напиши 'да' или 'нет'.")
    return MEDIA_DECISION

# --- неправильный ввод на этапе загрузки ---
def wrong_input_media(update: Update, context: CallbackContext):
    update.message.reply_text("⛔ Неправильный формат. Присылай фото/видео или напиши 'да', если закончил.")
    return MEDIA

# --- сброс /again ---
def again(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id] = {"text": None, "media": []}
    update.message.reply_text("🔄 Начинаем заново!\n\n💡 Напиши новый текст для отправки.")
    return TEXT

# --- отправка админу ---
def send_to_admin(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = user_data[user_id]["text"]
    media = user_data[user_id]["media"]

    admin_id = YOUR_ADMIN_ID   # 🔴 замени на свой ID

    if media:
        media_group = []
        for i, (mtype, file_id) in enumerate(media):
            caption = text if i == 0 else None
            if mtype == "photo":
                media_group.append(InputMediaPhoto(file_id, caption=caption, parse_mode=ParseMode.HTML))
            elif mtype == "video":
                media_group.append(InputMediaVideo(file_id, caption=caption, parse_mode=ParseMode.HTML))
        context.bot.send_media_group(chat_id=admin_id, media=media_group)
    else:
        context.bot.send_message(chat_id=admin_id, text=text, parse_mode=ParseMode.HTML)

    update.message.reply_text("✅ Спасибо! Уже бегу к админу с твоим сообщением!")

# --- main ---
def main():
    updater = Updater("YOUR_TOKEN", use_context=True)  # 🔴 замени на токен
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TEXT: [MessageHandler(Filters.text & ~Filters.command, handle_text)],
            MEDIA_DECISION: [
                MessageHandler(Filters.regex("^(да|нет)$"), handle_media_decision),
                MessageHandler(Filters.text & ~Filters.command, wrong_input_media_decision),
            ],
            MEDIA: [
                MessageHandler(Filters.photo | Filters.video, handle_media),
                MessageHandler(Filters.text & ~Filters.command, wrong_input_media),
            ],
        },
        fallbacks=[CommandHandler("again", again)],
    )

    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

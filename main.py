import os
import telebot
from telebot import types
from flask import Flask, request

TOKEN = os.getenv("TOKEN")
RAILWAY_URL = os.getenv("RAILWAY_STATIC_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # твой ID администратора

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

waiting_for_message = {}       # {sender_id: target_id}
last_message_ids = {}          # {sender_id: message_id у получателя}
reverse_mapping = {}           # {target_id: sender_id} для свайп-ответа


# ======== /start ========
@bot.message_handler(commands=['start'])
def start_handler(message):
    args = message.text.split()
    user_id = message.from_user.id
    bot_username = bot.get_me().username

    if len(args) > 1:
        target_id = int(args[1])
        if target_id == user_id:
            bot.send_message(message.chat.id, "❌ Нельзя написать самому себе.")
            return

        waiting_for_message[user_id] = target_id

        bot.send_message(
            message.chat.id,
            "🚀 Здесь можно отправить анонимное сообщение человеку.\n\n"
            "✍️ Напишите сюда всё, что хотите ему передать,\n"
            "и через несколько секунд он получит ваше сообщение,\n"
            "но не будет знать от кого 👀\n\n"
            "Отправить можно текст, фото, видео, голосовые, 🎥 кружки, ✨ стикеры."
        )
        return

    # Старт без аргумента
    personal_link = f"https://t.me/{bot_username}?start={user_id}"

    bot.send_message(
        message.chat.id,
        "Начните получать анонимные вопросы прямо сейчас!\n\n"
        f"👉 {personal_link}\n\n"
        "Разместите эту ссылку ☝️ в описании своего профиля "
        "Telegram, TikTok, Instagram (stories), чтобы вам могли написать 💬"
    )


# ======== Приём всех типов сообщений ========
@bot.message_handler(content_types=['text','photo','video','voice','video_note','sticker'])
def receive_all(message):
    sender_id = message.from_user.id

    if sender_id not in waiting_for_message:
        return

    target_id = waiting_for_message[sender_id]

    # ===== Пересылаем анонимно пользователю =====
    sent = bot.copy_message(
        chat_id=target_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )

    last_message_ids[sender_id] = sent.message_id
    reverse_mapping[target_id] = sender_id  # для свайп-ответа

    # ===== Логирование для админа =====
    try:
        content_desc = ""
        if message.content_type == "text":
            content_desc = f"Текст: {message.text}"
        elif message.content_type == "photo":
            content_desc = f"Фото: file_id={message.photo[-1].file_id}"
        elif message.content_type == "video":
            content_desc = f"Видео: file_id={message.video.file_id}"
        elif message.content_type == "voice":
            content_desc = f"Голосовое: file_id={message.voice.file_id}"
        elif message.content_type == "video_note":
            content_desc = f"Кружок: file_id={message.video_note.file_id}"
        elif message.content_type == "sticker":
            content_desc = f"Стикер: file_id={message.sticker.file_id}"

        log_text = (
            f"📨 Новое сообщение!\n\n"
            f"Отправитель: @{message.from_user.username} ({sender_id})\n"
            f"Получатель: {target_id}\n"
            f"Тип: {message.content_type}\n"
            f"{content_desc}"
        )
        bot.send_message(ADMIN_ID, log_text)
    except Exception as e:
        print(f"Ошибка логирования для админа: {e}")

    # ===== Сообщение отправителю с кнопками =====
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("✏️ Написать ещё раз", callback_data="write_again"),
        types.InlineKeyboardButton("🗑 Удалить сообщение", callback_data="delete_sent")
    )

    bot.send_message(
        sender_id,
        "✅ Сообщение отправлено, ожидайте ответ!",
        reply_markup=markup
    )

    waiting_for_message.pop(sender_id)


# ======== Обработка свайп-ответа пользователем =====
@bot.message_handler(func=lambda m: m.reply_to_message is not None, content_types=['text','photo','video','voice','sticker'])
def handle_reply(message):
    target_id = message.chat.id
    original_sender = reverse_mapping.get(target_id)

    if not original_sender:
        return  # это не анонимный ответ

    # Пересылаем ответ обратно отправителю анонимно
    bot.copy_message(
        chat_id=original_sender,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )

    # Добавляем кнопку "Написать ещё раз" под ответом
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("✏️ Написать ещё раз", callback_data="write_again"))
    bot.send_message(original_sender, "✅ Получен ответ!", reply_markup=markup)


# ======== Callback кнопки ========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    sender_id = call.from_user.id
    bot_username = bot.get_me().username

    if call.data == "write_again":
        last_target_id = last_message_ids.get(sender_id)
        if last_target_id:
            waiting_for_message[sender_id] = last_target_id

        bot.send_message(
            sender_id,
            "🚀 Здесь можно отправить анонимное сообщение человеку.\n\n"
            "✍️ Напишите сюда всё, что хотите ему передать,\n"
            "и через несколько секунд он получит ваше сообщение,\n"
            "но не будет знать от кого 👀\n\n"
            "Отправить можно текст, фото, видео, голосовые, 🎥 кружки, ✨ стикеры."
        )

    elif call.data == "delete_sent":
        target_id = last_message_ids.get(sender_id)
        if target_id:
            try:
                bot.delete_message(chat_id=waiting_for_message.get(sender_id, target_id), message_id=target_id)
            except:
                pass

        personal_link = f"https://t.me/{bot_username}?start={sender_id}"
        bot.send_message(
            sender_id,
            f"Начните получать анонимные вопросы прямо сейчас!\n\n👉 {personal_link}\n\n"
            "Разместите эту ссылку ☝️ в описании своего профиля "
            "Telegram, TikTok, Instagram (stories), чтобы вам могли написать 💬"
        )


# ======== Webhook ========
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Bot is running!"

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{RAILWAY_URL}/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

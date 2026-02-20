import telebot
from telebot import types

TOKEN = "ТВОЙ_ТОКЕН_СЮДА"

bot = telebot.TeleBot(TOKEN)

waiting_for_message = {}

# ================= КНОПКА ОТМЕНЫ =================
def cancel_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("❌ Отменить")
    return kb


# ================= START =================
@bot.message_handler(commands=['start'])
def start_handler(message):
    args = message.text.split()
    user_id = message.from_user.id
    bot_username = bot.get_me().username

    # Если зашли по чужой ссылке
    if len(args) > 1:
        target_id = args[1]

        if str(user_id) == target_id:
            bot.send_message(message.chat.id, "❌ Нельзя написать самому себе.")
            return

        waiting_for_message[user_id] = target_id

        bot.send_message(
            message.chat.id,
            "🚀 Здесь можно отправить анонимное сообщение человеку.\n\n"
            "✍️ Напишите сюда всё, что хотите ему передать,\n"
            "и через несколько секунд он получит ваше сообщение,\n"
            "но не будет знать от кого 👀\n\n"
            "Отправить можно фото, видео, текст,\n"
            "🎤 голосовые, 🎥 видеосообщения (кружки), ✨ стикеры.",
            reply_markup=cancel_keyboard()
        )
        return

    # Если обычный /start
    personal_link = f"https://t.me/{bot_username}?start={user_id}"

    bot.send_message(
        message.chat.id,
        "Начните получать анонимные вопросы прямо сейчас!\n\n"
        f"👉 https://t.me/{bot_username}?start={user_id}\n\n"
        "Разместите эту ссылку ☝️ в описании своего профиля "
        "Telegram, TikTok, Instagram (stories), чтобы вам могли написать 💬"
    )


# ================= ОТМЕНА =================
@bot.message_handler(func=lambda m: m.text == "❌ Отменить")
def cancel(message):
    user_id = message.from_user.id

    if user_id in waiting_for_message:
        waiting_for_message.pop(user_id)

    bot_username = bot.get_me().username

    bot.send_message(
        message.chat.id,
        "Начните получать анонимные вопросы прямо сейчас!\n\n"
        f"👉 https://t.me/{bot_username}?start={user_id}\n\n"
        "Разместите эту ссылку ☝️ в описании своего профиля "
        "Telegram, TikTok, Instagram (stories), чтобы вам могли написать 💬",
        reply_markup=types.ReplyKeyboardRemove()
    )


# ================= ПРИЁМ ВСЕХ ТИПОВ СООБЩЕНИЙ =================
@bot.message_handler(
    content_types=[
        'text',
        'photo',
        'video',
        'voice',
        'video_note',
        'sticker'
    ]
)
def receive_all(message):
    user_id = message.from_user.id

    if user_id not in waiting_for_message:
        return

    target_id = waiting_for_message.pop(user_id)

    # Отправляем полностью анонимно
    bot.copy_message(
        chat_id=target_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )

    bot.send_message(
        message.chat.id,
        "✅ Сообщение отправлено анонимно!",
        reply_markup=types.ReplyKeyboardRemove()
    )


# ================= ЗАПУСК =================
bot.remove_webhook()
bot.infinity_polling()

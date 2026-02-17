import os
import telebot
from telebot import types

# ⚡ Вставь сюда свой токен
TOKEN = os.getenv("TOKEN")  # или вставь прямо "ВАШ_ТОКЕН"
ADMIN_IDS = 7924774037, 483786028       # твой Telegram ID

bot = telebot.TeleBot(TOKEN)

# Временные словари для хранения состояния
waiting_for_message = {}
reply_to_user = {}

# ================= START =================
@bot.message_handler(commands=['start'])
def start_handler(message):
    args = message.text.split()

    # Если пользователь открыл персональную ссылку
    if len(args) > 1:
        target_id = args[1]

        if str(message.from_user.id) == target_id:
            bot.send_message(message.chat.id, "❌ Нельзя написать самому себе.")
            return

        waiting_for_message[message.from_user.id] = target_id
        bot.send_message(message.chat.id, "✍️ Напиши анонимное сообщение:")
        return

    # Обычный старт
    user_id = message.from_user.id
    bot_username = bot.get_me().username
    personal_link = f"https://t.me/{bot_username}?start={user_id}"

    bot.send_message(
        message.chat.id,
        f"🔗 Твоя персональная ссылка:\n\n{personal_link}\n\n"
        "Отправь её друзьям и получай анонимные сообщения 😎"
    )

# ================= RECEIVE MESSAGE =================
@bot.message_handler(func=lambda m: m.from_user.id in waiting_for_message)
def receive_message(message):
    sender = message.from_user
    target_id = waiting_for_message.pop(sender.id)

    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(
        "Ответить", callback_data=f"reply_{sender.id}"
    )
    markup.add(btn)

    # Отправка владельцу ссылки (анонимно)
    bot.send_message(
        target_id,
        f"📩 Анонимное сообщение:\n\n{message.text}",
        reply_markup=markup
    )

    # Копия админу с раскрытием отправителя
    bot.send_message(
        ADMIN_IDS,
        f"👀 Новое сообщение\n\n"
        f"Кому: {target_id}\n"
        f"Отправитель:\n"
        f"ID: {sender.id}\n"
        f"Username: @{sender.username if sender.username else 'нет'}\n"
        f"Имя: {sender.first_name}\n\n"
        f"Текст:\n{message.text}"
    )

    bot.send_message(message.chat.id, "✅ Сообщение отправлено анонимно!")

# ================= REPLY BUTTON =================
@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_"))
def reply_callback(call):
    sender_id = call.data.split("_")[1]
    reply_to_user[call.from_user.id] = sender_id
    bot.send_message(call.from_user.id, "✍️ Напиши ответ:")
    bot.answer_callback_query(call.id)

# ================= SEND REPLY =================
@bot.message_handler(func=lambda m: m.from_user.id in reply_to_user)
def send_reply(message):
    target_id = reply_to_user.pop(message.from_user.id)

    bot.send_message(
        target_id,
        f"📩 Тебе ответили:\n\n{message.text}"
    )

    bot.send_message(message.chat.id, "✅ Ответ отправлен!")

# ================= RUN =================
print("Бот запущен через polling...")
bot.infinity_polling()

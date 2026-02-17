import os
import telebot
from telebot import types

TOKEN = os.getenv("TOKEN")  # вставь сюда токен
ADMINS = [483786028, 7924774037]  # два админа

bot = telebot.TeleBot(TOKEN)

waiting_for_message = {}
reply_to_user = {}

# ================= START =================
@bot.message_handler(commands=['start'])
def start_handler(message):
    args = message.text.split()

    # Если открыт старт с чужой персональной ссылкой
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

    # Текст сообщения
    text = (
        "<b>Начните получать анонимные вопросы прямо сейчас!</b>\n\n"
        f"Ваша персональная ссылка:\n{personal_link}\n\n"
        "<b>Разместите эту ссылку ☝️ в описании своего профиля Telegram, TikTok, Instagram (stories), чтобы вам могли написать 💬</b>"
    )

    # Инлайн-кнопки под текстом
    markup = types.InlineKeyboardMarkup()
    share_btn = types.InlineKeyboardButton("📤 Поделиться ссылкой", switch_inline_query=personal_link)
    add_btn = types.InlineKeyboardButton("➕ Добавить бота в чат", url=f"https://t.me/{bot_username}?startgroup=true")
    markup.add(share_btn, add_btn)

    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)

# ================= RECEIVE MESSAGE =================
@bot.message_handler(func=lambda m: m.from_user.id in waiting_for_message)
def receive_message(message):
    sender = message.from_user
    target_id = waiting_for_message.pop(sender.id)

    # Кнопка ответа админу
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("Ответить", callback_data=f"reply_{sender.id}")
    markup.add(btn)

    bot.send_message(target_id, f"📩 Анонимное сообщение:\n\n{message.text}", reply_markup=markup)

    # Уведомление админов
    for admin in ADMINS:
        bot.send_message(
            admin,
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
    bot.send_message(call.from_user.id, "✍️ Напиши ответ пользователю:")
    bot.answer_callback_query(call.id)

# ================= SEND REPLY =================
@bot.message_handler(func=lambda m: m.from_user.id in reply_to_user)
def send_reply(message):
    target_id = reply_to_user.pop(message.from_user.id)
    bot.send_message(target_id, f"📩 Админ ответил:\n\n{message.text}")
    bot.send_message(message.chat.id, "✅ Ответ отправлен пользователю!")

# ================= RUN =================
print("Анонимный вопросный бот с двумя админами запущен...")
bot.infinity_polling()

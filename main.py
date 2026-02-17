import os
import telebot
from telebot import types
import urllib.parse

TOKEN = os.getenv("TOKEN")  # вставь сюда токен
ADMINS = [483786028, 7924774037]  # два админа

bot = telebot.TeleBot(TOKEN)

waiting_for_message = {}
reply_to_user = {}

# ================= START =================
@bot.message_handler(commands=['start'])
def start_handler(message):
    args = message.text.split()

    # Если старт с чужой персональной ссылкой
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

    # Инлайн-кнопки по одной на строке
    markup = types.InlineKeyboardMarkup()

    # 📤 Поделиться ссылкой через чистое окно шеринга
    share_text = urllib.parse.quote("Начните задавать мне анонимные вопросы! " + personal_link)
    share_url = f"https://t.me/share/url?url={personal_link}&text={share_text}"
    share_btn = types.InlineKeyboardButton("📤 Поделиться ссылкой", url=share_url)

    # ➕ Добавить бота в чат
    add_btn = types.InlineKeyboardButton("➕ Добавить бота в чат", url=f"https://t.me/{bot_username}?startgroup=true")

    markup.add([share_btn])
    markup.add([add_btn])

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

    # Отправка анонимного сообщения получателю
    bot.send_message(target_id, f"📩 Анонимное сообщение:\n\n{message.text}", reply_markup=markup)

    # Уведомление админов с ID + username отправителя и получателя
    recipient = bot.get_chat(target_id)
    for admin in ADMINS:
        bot.send_message(
            admin,
            f"👀 Новое анонимное сообщение\n\n"
            f"Отправитель:\n"
            f"ID: {sender.id}\n"
            f"Username: @{sender.username if sender.username else 'нет'}\n"
            f"Имя: {sender.first_name}\n\n"
            f"Получатель:\n"
            f"ID: {recipient.id}\n"
            f"Username: @{recipient.username if recipient.username else 'нет'}\n\n"
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
print("Анонимный вопросный бот с кнопкой чистого шеринга запущен...")
bot.infinity_polling()

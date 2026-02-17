import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TOKEN")  # вставь сюда токен
ADMIN = [7924774037]  # админы

bot = telebot.TeleBot(TOKEN)

waiting_for_message = {}  # кто кому пишет
reply_to_user = {}        # кто отвечает кому (анонимно)


# ================= START =================
@bot.message_handler(commands=['start'])
def start_handler(message):
    args = message.text.split()

    if len(args) > 1:
        target_id = args[1]
        if str(message.from_user.id) == target_id:
            bot.send_message(message.chat.id, "❌ Нельзя написать самому себе.")
            return
        waiting_for_message[message.from_user.id] = target_id
        bot.send_message(message.chat.id, "✍️ Напиши сообщение:")
        return

    user_id = message.from_user.id
    bot_username = bot.get_me().username
    personal_link = f"https://t.me/{bot_username}?start={user_id}"

    text = (
        "<b>Начните получать анонимные сообщения прямо сейчас!</b>\n\n"
        f"Ваша персональная ссылка:\n {personal_link}\n\n"
        "<b>Разместите эту ссылку в описании профиля, чтобы вам могли написать 💬</b>"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")


# ================= RECEIVE MESSAGE =================
@bot.message_handler(func=lambda m: m.from_user.id in waiting_for_message)
def receive_message(message):
    sender = message.from_user
    target_id = waiting_for_message.pop(sender.id)

    # Кнопка «Ответить» (полностью анонимно для B)
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("✍️ Ответить", callback_data=f"reply_{sender.id}"))

    bot.send_message(target_id, f"📩 Новое анонимное сообщение:\n\n{message.text}", reply_markup=keyboard)

    # Уведомление админов
    recipient = bot.get_chat(target_id)
    for admin in ADMIN:
        bot.send_message(
            admin,
            f"👀 Новое анонимное сообщение\nОтправитель: {sender.id} @{sender.username if sender.username else 'нет'}\n"
            f"Получатель: {recipient.id} @{recipient.username if recipient.username else 'нет'}\n"
            f"Текст:\n{message.text}"
        )

    bot.send_message(message.chat.id, "✅ Сообщение отправлено!")


# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda c: c.data.startswith("reply_"))
def reply_callback(call):
    original_sender_id = int(call.data.split("_")[1])
    reply_to_user[call.from_user.id] = original_sender_id
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, "✍️ Напиши свой ответ (анонимно):")


# ================= REPLY MESSAGE =================
@bot.message_handler(func=lambda m: m.from_user.id in reply_to_user)
def send_reply(message):
    target_id = reply_to_user.pop(message.from_user.id)

    # Отправка обратно оригинальному отправителю
    bot.send_message(target_id, f"📩 Анонимный ответ:\n\n{message.text}")

    # Уведомление админов
    sender = message.from_user
    recipient = bot.get_chat(target_id)
    for admin in ADMIN:
        bot.send_message(
            admin,
            f"👀 Анонимный ответ\nОтправитель: {sender.id} @{sender.username if sender.username else 'нет'}\n"
            f"Получатель: {recipient.id} @{recipient.username if recipient.username else 'нет'}\n"
            f"Текст:\n{message.text}"
        )

    bot.send_message(message.chat.id, "✅ Ответ отправлен анонимно!")


# ================= RUN =================
bot.remove_webhook()
bot.infinity_polling()

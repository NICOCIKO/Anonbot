import os
import telebot
from telebot import types

TOKEN = os.getenv("TOKEN")  # или вставь прямо токен
ADMINS = [483786028, 7924774037]  # два админа

bot = telebot.TeleBot(TOKEN)

# Проверим токен и получим username бота один раз
try:
    BOT_USERNAME = bot.get_me().username
except Exception as e:
    print("Ошибка при получении информации о боте:", e)
    BOT_USERNAME = "bot"

waiting_for_message = {}
reply_to_user = {}

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
        bot.send_message(message.chat.id, "✍️ Напиши анонимное сообщение:")
        return

    user_id = message.from_user.id
    personal_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

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
    btn = types.InlineKeyboardButton("Ответить", callback_data=f"reply_{sender.id}")
    markup.add(btn)

    # Отправка анонимного сообщения владельцу ссылки
    try:
        bot.send_message(
            target_id,
            f"📩 Анонимное сообщение:\n\n{message.text}",
            reply_markup=markup
        )
    except Exception as e:
        print(f"Ошибка при отправке владельцу ссылки: {e}")

    # Отправка копий всем админам
    for admin in ADMINS:
        try:
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
        except Exception as e:
            print(f"Ошибка при отправке админу {admin}: {e}")

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

    try:
        bot.send_message(
            target_id,
            f"📩 Админ ответил:\n\n{message.text}"
        )
    except Exception as e:
        print(f"Ошибка при отправке ответа пользователю: {e}")

    bot.send_message(message.chat.id, "✅ Ответ отправлен пользователю!")

# ================= RUN =================
print("Бот для анонимных вопросов с двумя админами запущен...")
bot.infinity_polling()

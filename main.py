
# full_anon_bot.py
import os
import telebot
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 7924774037))
RAILWAY_STATIC_URL = "https://anonbot-production-aeaf.up.railway.app"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Хранилище сообщений: message_id -> sender_id
sent_messages = {}

def get_personal_link(user_id):
    return f"https://t.me/{bot.get_me().username}?start={user_id}"

# ------------------- Стартовое сообщение -------------------
@bot.message_handler(commands=['start'])
def start_handler(message):
    args = message.text.split()
    if len(args) == 1:
        # Персональная ссылка пользователя
        personal_link = get_personal_link(message.from_user.id)
        text = (
            "🚀 **Начните получать анонимные вопросы прямо сейчас!**\n\n"
            f"👉 {personal_link}\n\n"
            "Разместите эту ссылку ☝️ в описании своего профиля Telegram, TikTok, Instagram (stories), чтобы вам могли написать 💬"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📤 Поделиться ссылкой", switch_inline_query=personal_link))
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)
    else:
        # Пользователь пришёл по чужой ссылке
        target_id = int(args[1])
        text = (
            "🚀 Здесь можно отправить анонимное сообщение человеку.\n\n"
            "✍️ Напишите сюда всё, что хотите ему передать,\n"
            "и через несколько секунд он получит ваше сообщение,\n"
            "но не будет знать от кого 👀\n\n"
            "Отправить можно фото, видео, текст,\n"
            "🎤 голосовые, 🎥 видеосообщения, ✨ стикеры."
        )
        bot.send_message(message.chat.id, text)
        bot.register_next_step_handler_by_chat_id(message.chat.id, lambda m: handle_send(m, target_id))

# ------------------- Отправка анонимного сообщения -------------------
def handle_send(message, target_id):
    # Отправка админу
    username = message.from_user.username if message.from_user.username else "Нет username"
    info_text = f"📩 Анонимное сообщение для {target_id}\nОтправитель: {message.from_user.id} ({username})"
    bot.send_message(ADMIN_ID, info_text)

    # Отправка получателю
    if message.content_type == "text":
        sent_msg = bot.send_message(target_id, message.text)
    elif message.content_type == "photo":
        sent_msg = bot.send_photo(target_id, message.photo[-1].file_id, caption=message.caption)
    elif message.content_type == "video":
        sent_msg = bot.send_video(target_id, message.video.file_id, caption=message.caption)
    elif message.content_type == "voice":
        sent_msg = bot.send_voice(target_id, message.voice.file_id)
    elif message.content_type == "sticker":
        sent_msg = bot.send_sticker(target_id, message.sticker.file_id)
    else:
        sent_msg = bot.send_message(target_id, "Тип файла не поддерживается.")

    sent_messages[sent_msg.message_id] = message.from_user.id

    # Кнопка свайп для ответа
    markup_swipe = InlineKeyboardMarkup()
    markup_swipe.add(InlineKeyboardButton("↩️ Свайпни для ответа", callback_data=f"reply_{sent_msg.message_id}"))
    bot.send_message(target_id, "💬 У тебя новое сообщение!", reply_markup=markup_swipe)

    # Сообщение пользователю, что отправлено
    markup_user = InlineKeyboardMarkup()
    markup_user.add(InlineKeyboardButton("Написать ещё раз", callback_data=f"again_{target_id}"))
    markup_user.add(InlineKeyboardButton("Удалить сообщение", callback_data=f"delete_{sent_msg.message_id}"))
    bot.send_message(message.chat.id, "✅ Сообщение отправлено, ожидайте ответ!", reply_markup=markup_user)

# ------------------- Обработка инлайн кнопок -------------------
@bot.callback_query_handler(func=lambda c: True)
def inline_handler(call):
    data = call.data
    if data.startswith("again_"):
        target_id = int(data.split("_")[1])
        bot.send_message(call.message.chat.id, "✍️ Напишите новое анонимное сообщение:")
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: handle_send(m, target_id))

    elif data.startswith("delete_"):
        msg_id = int(data.split("_")[1])
        if msg_id in sent_messages:
            recipient = msg_id  # сообщение для кого удалять
            try:
                bot.delete_message(sent_messages[msg_id], msg_id)
            except:
                pass
            bot.send_message(call.message.chat.id, f"Сообщение удалено. Ваша персональная ссылка: {get_personal_link(call.from_user.id)}")
            del sent_messages[msg_id]

    elif data.startswith("reply_"):
        msg_id = int(data.split("_")[1])
        if msg_id in sent_messages:
            original_sender = sent_messages[msg_id]
            bot.send_message(call.message.chat.id, "✍️ Напишите ответ на сообщение:")
            bot.register_next_step_handler_by_chat_id(call.message.chat.id,
                                                     lambda m: send_reply_to_original(m, original_sender))

# ------------------- Отправка ответа отправителю -------------------
def send_reply_to_original(message, recipient_id):
    if message.content_type == "text":
        bot.send_message(recipient_id, f"💬 Ответ: {message.text}")
    elif message.content_type == "photo":
        bot.send_photo(recipient_id, message.photo[-1].file_id, caption=message.caption)
    elif message.content_type == "video":
        bot.send_video(recipient_id, message.video.file_id, caption=message.caption)
    elif message.content_type == "voice":
        bot.send_voice(recipient_id, message.voice.file_id)
    elif message.content_type == "sticker":
        bot.send_sticker(recipient_id, message.sticker.file_id)
    else:
        bot.send_message(recipient_id, "Тип файла не поддерживается.")

    # Кнопка «Написать ещё раз» под ответом
    markup_again = InlineKeyboardMarkup()
    markup_again.add(InlineKeyboardButton("Написать ещё раз", callback_data=f"again_{recipient_id}"))
    bot.send_message(message.chat.id, "✅ Ответ отправлен!", reply_markup=markup_again)

# ------------------- Webhook для Railway -------------------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

# ------------------- Запуск на Railway -------------------
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{RAILWAY_STATIC_URL}/{TOKEN}")
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

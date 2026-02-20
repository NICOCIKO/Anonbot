import os
import telebot
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 7924774037))
RAILWAY_STATIC_URL = "https://anonbot-production-aeaf.up.railway.app"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ------------------- Хранилища -------------------
# sent_messages: message_id получателя -> {"sender_id":..., "chat_id":...}
sent_messages = {}

# ------------------- Персональная ссылка -------------------
def get_personal_link(user_id):
    return f"https://t.me/anonim_quesss_bot?start={user_id}"

def get_personal_link_text(user_id):
    link = get_personal_link(user_id)
    return (
        f"🚀 **Начните получать анонимные вопросы прямо сейчас!**\n\n"
        f"👉 {link}\n\n"
        "Разместите эту ссылку ☝️ в описании своего профиля Telegram, TikTok, Instagram (stories), чтобы вам могли написать 💬"
    )

# ------------------- Старт -------------------
@bot.message_handler(commands=['start'])
def start_handler(message):
    args = message.text.split()
    if len(args) == 1:
        # Личный старт
        text = get_personal_link_text(message.from_user.id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📤 Поделиться ссылкой", switch_inline_query=get_personal_link(message.from_user.id)))
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)
    else:
        # Пришли по чужой ссылке
        target_id = int(args[1])
        text = (
            "💌 Здесь можно отправить анонимное сообщение человеку.\n\n"
            "✍️ Напишите всё, что хотите передать,\n"
            "и через несколько секунд он получит сообщение,\n"
            "но не будет знать от кого 👀\n\n"
            "Можно отправлять текст, фото, видео, голосовые, стикеры 🎤🎥✨"
        )
        bot.send_message(message.chat.id, text)
        send_cancel_option(message.chat.id, target_id)
        bot.register_next_step_handler_by_chat_id(message.chat.id, lambda m: handle_send(m, target_id))

# ------------------- Кнопка Отмена -------------------
def send_cancel_option(chat_id, target_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_{target_id}"))
    bot.send_message(chat_id, "Если передумали, нажмите кнопку ниже:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("cancel_"))
def cancel_handler(call):
    user_id = call.from_user.id
    personal_link = get_personal_link(user_id)
    text = (
        "🚀 **Начните получать анонимные вопросы прямо сейчас!**\n\n"
        f"👉 {personal_link}\n\n"
        "Разместите эту ссылку ☝️ в описании своего профиля Telegram, TikTok, Instagram (stories), чтобы вам могли написать 💬"
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="Markdown")

# ------------------- Отправка анонимного сообщения -------------------
def handle_send(message, target_id):
    username = message.from_user.username or "Нет username"
    info_text = f"📩 Анонимное сообщение для {target_id}\nОтправитель: {message.from_user.id} ({username})"
    bot.send_message(ADMIN_ID, info_text)

    # Отправляем сообщение получателю
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

    # Сохраняем info для удаления
    sent_messages[sent_msg.message_id] = {"sender_id": message.from_user.id, "chat_id": target_id}

    # Кнопки под сообщением получателю
    markup_reply = InlineKeyboardMarkup()
    markup_reply.add(InlineKeyboardButton("✍️ Ответить", callback_data=f"reply_{sent_msg.message_id}"))
    markup_reply.add(InlineKeyboardButton("🗑️ Удалить сообщение", callback_data=f"delete_{sent_msg.message_id}"))
    bot.send_message(target_id, "💬 У тебя новое сообщение!", reply_markup=markup_reply)

# ------------------- Ответ на сообщение -------------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("reply_"))
def reply_handler(call):
    msg_id = int(call.data.split("_")[1])
    if msg_id in sent_messages:
        sender_id = sent_messages[msg_id]["sender_id"]
        bot.send_message(call.from_user.id, "✍️ Напишите свой ответ:")
        bot.register_next_step_handler_by_chat_id(call.from_user.id, lambda m: send_reply(m, sender_id))

def send_reply(message, sender_id):
    bot.send_message(sender_id, f"💌 Анонимный ответ:\n{message.text}")
    bot.send_message(message.chat.id, "✅ Ответ отправлен! Написать ещё раз 🔁")

# ------------------- Удаление сообщения -------------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("delete_"))
def delete_message_handler(call):
    msg_id = int(call.data.split("_")[1])
    if msg_id in sent_messages:
        chat_id = sent_messages[msg_id]["chat_id"]
        try:
            bot.delete_message(chat_id, msg_id)
            bot.answer_callback_query(call.id, "Сообщение удалено 🗑️")
        except:
            bot.answer_callback_query(call.id, "Не удалось удалить сообщение ❌")
    else:
        bot.answer_callback_query(call.id, "Сообщение уже удалено или не найдено ❌")

# ------------------- Webhook для Railway -------------------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "", 200

bot.remove_webhook()
bot.set_webhook(url=f"{RAILWAY_STATIC_URL}/{TOKEN}")

# ------------------- Запуск Flask -------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

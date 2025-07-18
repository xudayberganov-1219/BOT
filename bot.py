import os
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

import requests

# --- Sozlamalar ---
BOT_TOKEN = os.getenv("7950074019:AAH_lofQm_K3OjXzuiwzlWVnKovw_cLVO44")  # Render dagi Environment variable
MISTRAL_API_KEY = os.getenv("9JZcncIN9tSDXyA00KqX6f2GC7soAEW0")
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
APP_URL = os.getenv("https://math-genius.onrender.com")  # Masalan: https://math-genius.onrender.com

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Flask App ---
app = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).build()

# --- /start komandasi ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not os.path.exists("users.txt"):
        open("users.txt", "w").close()

    with open("users.txt", "r+") as f:
        users = f.read().splitlines()
        if user_id not in users:
            f.write(user_id + "\n")

    keyboard = [
        [InlineKeyboardButton("Statistika", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🤖 Menga matematik savol yuboring:", reply_markup=reply_markup)

# --- Callback tugmalar ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "stats":
        if not os.path.exists("users.txt"):
            await query.edit_message_text("Foydalanuvchilar ro'yxati mavjud emas.")
            return

        with open("users.txt", "r") as f:
            count = len(f.readlines())
        await query.edit_message_text(f"👥 Bot foydalanuvchilari soni: {count}")

# --- Mistral API orqali javob olish ---
def ask_mistral(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    json_data = {
        "model": "mistral-small",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(MISTRAL_URL, json=headers, json=json_data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Mistral API error: {e}")
        return "❌ Xatolik yuz berdi. Keyinroq urinib ko‘ring."

# --- Matn kelganda ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    await update.message.reply_chat_action("typing")
    response = ask_mistral(prompt)
    await update.message.reply_text(response)

# --- Handlers ro‘yxatdan o‘tkazish ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- Webhook sozlash ---
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    await application.update_queue.put(Update.de_json(request.get_json(force=True), application.bot))
    return "ok"

@app.route("/")
def index():
    return "🤖 Bot ishga tushdi!"

async def set_webhook():
    await application.bot.set_webhook(url=f"{APP_URL}/{BOT_TOKEN}")

# --- App run ---
if __name__ == "__main__":
    import asyncio
    asyncio.run(set_webhook())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)


MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "9JZcncIN9tSDXyA00KqX6f2GC7soAEW0")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7950074019:AAH_lofQm_K3OjXzuiwzlWVnKovw_cLVO44")

USERS_FILE = "users.txt"
BASE_COUNT = 122

user_ids = set()

# 📁 Fayldan user ID'larni yuklash
def load_users():
    global user_ids
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            user_ids = set(map(int, f.read().splitlines()))
    else:
        user_ids = set()

# ✏️ Yangi foydalanuvchini faylga yozish
def append_user(uid):
    if uid not in user_ids:
        user_ids.add(uid)
        try:
            with open(USERS_FILE, "a") as f:
                f.write(f"{uid}\n")
        except Exception as e:
            print(f"❌ Faylga yozishda xatolik: {e}")

# 🤖 Mistral API'ga so'rov yuborish
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_input = update.message.text.lower()

    append_user(uid)

    if "cos(120" in user_input or "cosinus 120" in user_input:
        reply = (
            "🔢 Cosinus funksiyasining 120° burchakdagi qiymatini hisoblaymiz:\n\n"
            "cos(120°) = cos(180° - 60°)\n"
            "          = -cos(60°)\n"
            "          = -1/2\n\n"
            "✅ Natija: cos(120°) = -1/2"
        )
        await update.message.reply_text(reply)
        return

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "system", "content": "Sen tajribali matematik bo‘lgan sun’iy intellektsan. Foydalanuvchining savoliga tushunarli qilib javob ber."},
            {"role": "user", "content": user_input}
        ]
    }

    try:
        response = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            reply = response.json()['choices'][0]['message']['content']
        else:
            reply = f"❌ API xatolik: {response.status_code}"
    except Exception as e:
        reply = f"❌ APIga ulanishda xatolik: {e}"

    await update.message.reply_text(reply)

# /start komandasi
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    append_user(uid)

    total_users = BASE_COUNT + len(user_ids)
    keyboard = [
        [InlineKeyboardButton("📚 Yordam", callback_data="help")],
        [InlineKeyboardButton("📊 Foydalanuvchilar soni", callback_data="users")]
    ]
    await update.message.reply_text(
        f"👋 Salom, {update.effective_user.first_name}!\n"
        f"📊 Botdan foydalanuvchilar soni: {total_users} ta.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Inline tugmalarni boshqarish
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    append_user(uid)

    if query.data == "help":
        await query.edit_message_text("📘 Matematik savolni yozing. Masalan: 'cos(120)' yoki 'Pifagor teoremasi'.")
    elif query.data == "users":
        total = BASE_COUNT + len(user_ids)
        await query.edit_message_text(f"📊 Bot foydalanuvchilari: {total} ta.")

# Botni ishga tushirish
def main():
    load_users()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()

import os
import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram.error import Forbidden

# 📌 Tokenlar va sozlamalar
MISTRAL_API_KEY = "9JZcncIN9tSDXyA00KqX6f2GC7soAEW0"
TELEGRAM_BOT_TOKEN = "7950074019:AAH_lofQm_K3OjXzuiwzlWVnKovw_cLVO44"
CHANNEL_USERNAME = "@IT_kanal_oo1"
BASE_COUNT = 122
user_ids = set()

# ✅ Faylga yozish
def append_user(uid):
    try:
        with open("users.txt", "a") as f:
            f.write(f"{uid}\n")
    except Exception as e:
        print(f"❌ Faylga yozishda xatolik: {e}")

# 📌 Kanalga obuna bo‘lganini tekshirish
async def is_user_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Forbidden:
        return False
    except Exception as e:
        print(f"❌ Tekshiruvda xatolik: {e}")
        return False

# 📥 Xabarlarni ko‘rib chiqish
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.lower()
    uid = update.effective_user.id

    # ❌ Obuna bo‘lmagan bo‘lsa
    if not await is_user_subscribed(context.bot, uid):
        await update.message.reply_text(f"❗ Avval {CHANNEL_USERNAME} kanaliga obuna bo‘ling.")
        return

    if uid not in user_ids:
        user_ids.add(uid)
        append_user(uid)

    # 🎯 Maxsus misol
    if "cos(120" in user_input or "cosinus 120" in user_input:
        await update.message.reply_text(
            "🔢 Cosinus funksiyasining 120° burchakdagi qiymatini hisoblaymiz:\n\n"
            "cos(120°) = cos(180° - 60°)\n"
            "          = -cos(60°)\n"
            "          = -1/2\n\n"
            "✅ Natija: cos(120°) = -1/2"
        )
        return

    # 🧠 Mistral AI javobi
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "system", "content": "Sen tajribali matematik bo‘lgan sun’iy intellektsan. Foydalanuvchining savoliga tushunarli qilib fikr yuritib javob ber."},
            {"role": "user", "content": user_input}
        ]
    }

    response = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=data)
    if response.status_code == 200:
        reply = response.json()['choices'][0]['message']['content']
    else:
        reply = f"❌ Xatolik yuz berdi: {response.status_code}"

    await update.message.reply_text(reply)

# 🚀 /start komandasi
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if not await is_user_subscribed(context.bot, uid):
        await update.message.reply_text(f"❗ Avval {CHANNEL_USERNAME} kanaliga obuna bo‘ling.")
        return

    if uid not in user_ids:
        user_ids.add(uid)
        append_user(uid)

    total_users = BASE_COUNT + len(user_ids)

    keyboard = [
        [InlineKeyboardButton("📚 Yordam", callback_data="help")],
        [InlineKeyboardButton("📊 Foydalanuvchilar soni", callback_data="users")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Salom, {update.effective_user.first_name}!\n"
        f"🤖 Men matematik savollarga javob beradigan sun’iy intellektman.\n"
        f"📊 Botdan jami foydalanuvchilar: {total_users} ta.",
        reply_markup=reply_markup
    )

# ⌨️ Tugmalar
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id

    if not await is_user_subscribed(context.bot, uid):
        await query.edit_message_text(f"❗ Avval {CHANNEL_USERNAME} kanaliga obuna bo‘ling.")
        return

    if query.data == "help":
        await query.edit_message_text(
            "📘 Yordam:\n"
            "Bot orqali matematik savollarni yozing.\n"
            "Misol: 'Pifagor teoremasi qanday ishlaydi?' yoki 'cos(120°)'"
        )
    elif query.data == "users":
        total = BASE_COUNT + len(user_ids)
        await query.edit_message_text(f"📊 Jami foydalanuvchilar: {total} ta.")

# 🧠 Asosiy
async def main():
    global user_ids
    try:
        with open("users.txt", "r") as f:
            user_ids = set(map(int, f.read().splitlines()))
    except FileNotFoundError:
        user_ids = set()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot ishga tushdi (polling)...")
    await app.run_polling()

# 🏁 Ishga tushirish
if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

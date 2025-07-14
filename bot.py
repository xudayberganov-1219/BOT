import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

MISTRAL_API_KEY = "9JZcncIN9tSDXyA00KqX6f2GC7soAEW0"
TELEGRAM_BOT_TOKEN = "7950074019:AAH_lofQm_K3OjXzuiwzlWVnKovw_cLVO44"

# Foydalanuvchilar to'plami
user_ids = set()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    # Yangi foydalanuvchini ro'yxatga olish
    uid = update.effective_user.id
    if uid not in user_ids:
        user_ids.add(uid)
        with open("users.txt", "a") as f:
            f.write(f"{uid}\n")

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

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_ids:
        user_ids.add(uid)
        with open("users.txt", "a") as f:
            f.write(f"{uid}\n")

    total_users = len(user_ids)
    text = f"👋 Salom, {update.effective_user.first_name}!\n🤖 Men matematik savollarga yordam beradigan sun’iy intellektman.\n📊 Jami foydalanuvchilar: {total_users} ta."
    await update.message.reply_text(text)

def main():
    global user_ids
    try:
        with open("users.txt", "r") as f:
            user_ids = set(map(int, f.read().splitlines()))
    except FileNotFoundError:
        user_ids = set()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()

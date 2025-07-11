# Fayl: main.py
# Cookie fayllar tashqi papkada
# 144p sifati olib tashlangan
# To‘liq ishlaydigan Telegram Bot

import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
import yt_dlp
from urllib.parse import urlparse
from aiohttp import web

TOKEN = '7619009078:AAF7TKU9j4QikKjIb46BZktox3-MCd9SbME'
CHANNEL_USERNAME = '@IT_kanal_oo1'
WEBHOOK_URL = 'https://web-production-65853.up.railway.app'
PORT = int(os.getenv('PORT', 8080))
MAX_FILE_SIZE = 50 * 1024 * 1024

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
application = None

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def detect_platform(url):
    if 'instagram.com' in url:
        return 'instagram'
    elif 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube'
    elif 'tiktok.com' in url:
        return 'tiktok'
    return 'unknown'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user.id)
        if member.status not in ['member', 'administrator', 'creator']:
            raise Exception("Not a member")
    except:
        keyboard = [
            [InlineKeyboardButton("🔔 Obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")],
            [InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")]
        ]
        await update.message.reply_text("Botdan foydalanish uchun kanalga obuna bo‘ling:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    await update.message.reply_text("📥 Video yoki audio link yuboring...")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not is_valid_url(url):
        await update.message.reply_text("❌ Noto'g'ri link!")
        return
    platform = detect_platform(url)
    if platform == 'unknown':
        await update.message.reply_text("❌ Platform qo‘llab-quvvatlanmaydi.")
        return
    context.user_data['url'] = url
    context.user_data['platform'] = platform

    buttons = [
        [InlineKeyboardButton("🎬 MP4 (Video)", callback_data="download_mp4")]
    ]
    if platform in ['youtube', 'instagram']:
        buttons.insert(0, [InlineKeyboardButton("🎵 MP3 (Audio)", callback_data="download_mp3")])
    await update.message.reply_text("Format tanlang:", reply_markup=InlineKeyboardMarkup(buttons))

async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    fmt = query.data.split('_')[1]
    url = context.user_data.get('url')
    platform = context.user_data.get('platform')
    cookie_file = None

    if platform == 'youtube':
        cookie_file = 'cookies_youtube.txt'
    elif platform == 'instagram':
        cookie_file = 'cookies_instagram.txt'

    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
        'cookiefile': cookie_file if cookie_file and os.path.exists(cookie_file) else None,
    }

    if fmt == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        })
    else:
        ydl_opts.update({
            'format': 'best[height<=720]/best',
            'merge_output_format': 'mp4'
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if fmt == 'mp3':
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            if not os.path.exists(filename):
                await query.edit_message_text("❌ Fayl topilmadi!")
                return
            if os.path.getsize(filename) > MAX_FILE_SIZE:
                os.remove(filename)
                await query.edit_message_text("❌ Fayl juda katta (>50MB)!")
                return
            caption = f"{info.get('title', 'Fayl')} ✅"
            with open(filename, 'rb') as f:
                if fmt == 'mp3':
                    await context.bot.send_audio(chat_id=query.message.chat.id, audio=f, caption=caption)
                else:
                    await context.bot.send_video(chat_id=query.message.chat.id, video=f, caption=caption)
            os.remove(filename)
            await query.edit_message_text("✅ Yuborildi.")
    except Exception as e:
        await query.edit_message_text(f"❌ Xato: {str(e)[:100]}")

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, update.effective_user.id)
        if member.status in ['member', 'creator', 'administrator']:
            await query.edit_message_text("✅ Obuna tasdiqlandi!")
        else:
            await query.answer("❌ Obuna topilmadi!", show_alert=True)
    except:
        await query.answer("❌ Xato yuz berdi!", show_alert=True)

async def webhook_handler(request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return web.Response(status=200)

async def health(request):
    return web.Response(text="OK")

def main():
    global application
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(download_callback, pattern="^download_"))
    application.add_handler(CallbackQueryHandler(check_subscription, pattern="check_sub"))

    app = web.Application()
    app.router.add_post("/webhook", webhook_handler)
    app.router.add_get("/", health)

    async def setup():
        await application.initialize()
        await application.start()
        await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")

    async def init_app():
        await setup()
        return app

    web.run_app(init_app(), host="0.0.0.0", port=PORT)

if __name__ == '__main__':
    main()

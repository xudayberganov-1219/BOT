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

# 🔐 To'g'ridan-to'g'ri TOKEN
TOKEN = '7619009078:AAF7TKU9j4QikKjIb46BZktox3-MCd9SbME'
CHANNEL_USERNAME = '@IT_kanal_oo1'
WEBHOOK_URL = 'https://web-production-65853.up.railway.app'  # Railway URL
PORT = int(os.getenv('PORT', 8000))
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# 📋 Logger
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
    else:
        return 'unknown'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user.id)
        is_member = member.status in ['member', 'creator', 'administrator']
    except:
        is_member = False

    if not is_member:
        keyboard = [
            [InlineKeyboardButton("🔔 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")],
            [InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Iltimos kanalga obuna bo'ling:", reply_markup=reply_markup)
    else:
        await show_main_menu(update, context)

async def show_main_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("📥 Yuklab olish", callback_data="download_menu")],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎬 Link yuboring (Instagram, YouTube, TikTok):", reply_markup=reply_markup)

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not is_valid_url(url):
        await update.message.reply_text("❌ Noto'g'ri link!")
        return

    platform = detect_platform(url)
    if platform == 'unknown':
        await update.message.reply_text("❌ Platforma qo‘llab-quvvatlanmaydi!")
        return

    context.user_data['url'] = url
    context.user_data['platform'] = platform

    buttons = [[InlineKeyboardButton("🎬 MP4", callback_data="format_mp4")]]
    if platform in ['youtube', 'instagram']:
        buttons.insert(0, [InlineKeyboardButton("🎵 MP3", callback_data="format_mp3")])
    await update.message.reply_text("Formatni tanlang:", reply_markup=InlineKeyboardMarkup(buttons))

async def show_quality(update, context, format_type):
    context.user_data['format'] = format_type
    query = update.callback_query
    await query.answer()

    if format_type == 'mp3':
        quality_buttons = [
            [InlineKeyboardButton("128 kbps", callback_data="q_128")],
            [InlineKeyboardButton("192 kbps", callback_data="q_192")],
            [InlineKeyboardButton("320 kbps", callback_data="q_320")]
        ]
    else:
        quality_buttons = [
            [InlineKeyboardButton("360p", callback_data="q_360")],
            [InlineKeyboardButton("720p", callback_data="q_720")]
        ]

    await query.edit_message_text("Sifatni tanlang:", reply_markup=InlineKeyboardMarkup(quality_buttons))

async def download(update, context, quality):
    query = update.callback_query
    await query.answer()
    url = context.user_data.get('url')
    platform = context.user_data.get('platform')
    format_type = context.user_data.get('format')

    await query.edit_message_text("📥 Yuklab olinmoqda...")

    cookiefile = None
    if platform == 'youtube':
        cookiefile = 'cookies_youtube.txt'
    elif platform == 'instagram':
        cookiefile = 'cookies_instagram.txt'

    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
        'cookiefile': cookiefile,
        'no_warnings': True,
        'ignoreerrors': True
    }

    if format_type == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality
            }]
        })
    else:
        ydl_opts.update({
            'format': f'best[height<={quality}]',
            'merge_output_format': 'mp4'
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if format_type == 'mp3':
                filename = filename.rsplit('.', 1)[0] + '.mp3'

        if os.path.getsize(filename) > MAX_FILE_SIZE:
            os.remove(filename)
            await query.edit_message_text("❌ Fayl juda katta!")
            return

        with open(filename, 'rb') as f:
            if format_type == 'mp3':
                await context.bot.send_audio(query.message.chat_id, audio=f)
            else:
                await context.bot.send_video(query.message.chat_id, video=f, supports_streaming=True)
        os.remove(filename)
    except Exception as e:
        await query.edit_message_text(f"❌ Yuklab olishda xatolik: {e}")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    if data == "check_sub":
        await start(update, context)
    elif data == "download_menu":
        await show_main_menu(update, context)
    elif data == "help":
        await update.callback_query.edit_message_text("Yordam: video link yuboring, format va sifat tanlang.")
    elif data.startswith("format_"):
        await show_quality(update, context, data.split("_")[1])
    elif data.startswith("q_"):
        await download(update, context, data.split("_")[1])

async def webhook_handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return web.Response(status=200)
    except Exception as e:
        return web.Response(status=500, text=str(e))

async def health(request):
    return web.Response(text="OK")

def main():
    global application
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    app = web.Application()
    app.router.add_post("/webhook", webhook_handler)
    app.router.add_get("/health", health)

    async def start_bot():
        await application.initialize()
        await application.start()
        await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
        return app

    web.run_app(start_bot(), host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()

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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TOKEN', '7619009078:AAF7TKU9j4QikKjIb46BZktox3-MCd9SbME')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', '@IT_kanal_oo1')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://web-production-65853.up.railway.app')
PORT = int(os.getenv('PORT', 8000))
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Instagram va YouTube cookie matni environment variables sifatida saqlanadi
COOKIES_INSTAGRAM = os.getenv('COOKIES_INSTAGRAM')  # cookies_instagram.txt ichidagi matn
COOKIES_YOUTUBE = os.getenv('COOKIES_YOUTUBE')      # cookies_youtube.txt ichidagi matn

def save_cookies_to_file(cookie_str: str, filename: str):
    if not cookie_str:
        return False
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(cookie_str)
    return True

# Cookie fayllar nomlari root papkada
INSTAGRAM_COOKIE_FILE = 'cookies_instagram.txt'
YOUTUBE_COOKIE_FILE = 'cookies_youtube.txt'

# Cookie fayllarni saqlab qo'yamiz
save_cookies_to_file(COOKIES_INSTAGRAM, INSTAGRAM_COOKIE_FILE)
save_cookies_to_file(COOKIES_YOUTUBE, YOUTUBE_COOKIE_FILE)

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

application = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user.id)
        is_member = member.status in ['member', 'creator', 'administrator']
    except Exception as e:
        logger.error(f"Kanal a'zoligini tekshirishda xato: {e}")
        is_member = False

    if not is_member:
        keyboard = [
            [InlineKeyboardButton("🔔 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")],
            [InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome_text = (
            "👋 Assalomu alaykum!\n\n"
            "🎬 **Video Downloader Bot**ga xush kelibsiz!\n\n"
            "📱 **Qo'llab-quvvatlanadigan platformalar:**\n"
            "• Instagram ✅\n"
            "• YouTube ⚠️\n"
            "• TikTok ✅\n\n"
            "📥 **Formatlar:**\n"
            "• MP4 (Video)\n"
            "• MP3 (Audio)\n\n"
            "🎯 **Sifat tanlovlari:**\n"
            "• 360p, 720p, 1080p\n\n"
            "⚠️ Botdan foydalanish uchun kanalga obuna bo'ling:"
        )

        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await show_main_menu(update, context)

async def show_main_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("📥 Video yuklash", callback_data="download_menu")],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data="help"),
         InlineKeyboardButton("📊 Statistika", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    menu_text = (
        "🎬 **Video Downloader Bot**\n\n"
        "📱 Video linkini yuboring:\n\n"
        "🔗 **Eng yaxshi ishlaydiganlar:**\n"
        "• Instagram: instagram.com/p/... ✅\n"
        "• TikTok: tiktok.com/@.../video/... ✅\n"
        "• YouTube: youtube.com/watch?v=... ⚠️\n\n"
        "💡 **Maslahat:** Instagram va TikTok linklar eng yaxshi ishlaydi!"
    )

    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user.id)
        is_member = member.status in ['member', 'creator', 'administrator']
    except Exception as e:
        logger.error(f"Obunani tekshirishda xato: {e}")
        is_member = False
    if not is_member:
        await query.answer("❌ Hali obuna bo'lmagansiz! Iltimos, kanalga obuna bo'ling.", show_alert=True)
    else:
        await query.edit_message_text("✅ Obuna tasdiqlandi!")
        await asyncio.sleep(1)
        await show_main_menu(update, context)

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not is_valid_url(url):
        await update.message.reply_text("❌ Noto'g'ri link! Iltimos, to'g'ri link yuboring.")
        return
    platform = detect_platform(url)
    if platform == 'unknown':
        await update.message.reply_text(
            "❌ Qo'llab-quvvatlanmaydigan platform!\n\n"
            "✅ Qo'llab-quvvatlanadigan platformalar:\n"
            "• Instagram ✅\n"
            "• TikTok ✅\n"
            "• YouTube ⚠️ (ba'zan muammo)"
        )
        return
    context.user_data['url'] = url
    context.user_data['platform'] = platform
    await show_format_menu(update, context, platform)

async def show_format_menu(update, context, platform):
    keyboard = []
    if platform in ['youtube', 'instagram']:
        keyboard.extend([
            [InlineKeyboardButton("🎵 MP3 (Audio)", callback_data="format_mp3")],
            [InlineKeyboardButton("🎬 MP4 (Video)", callback_data="format_mp4")]
        ])
    else:
        keyboard.append([InlineKeyboardButton("🎬 MP4 (Video)", callback_data="format_mp4")])
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    platform_names = {
        'instagram': 'Instagram ✅',
        'youtube': 'YouTube ⚠️',
        'tiktok': 'TikTok ✅'
    }
    text = f"📱 **{platform_names[platform]}** link aniqlandi!\n\nFormat tanlang:"
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_quality_menu(update, context, format_type):
    query = update.callback_query
    await query.answer()
    context.user_data['format'] = format_type
    if format_type == 'mp3':
        keyboard = [
            [InlineKeyboardButton("🎵 128 kbps", callback_data="quality_128")],
            [InlineKeyboardButton("🎵 192 kbps", callback_data="quality_192")],
            [InlineKeyboardButton("🎵 320 kbps", callback_data="quality_320")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_format")]
        ]
        text = "🎵 **Audio sifatini** tanlang:"
    else:
        keyboard = [
            [InlineKeyboardButton("📱 360p", callback_data="quality_360")],
            [InlineKeyboardButton("📱 720p", callback_data="quality_720")],
            [InlineKeyboardButton("📱 1080p", callback_data="quality_1080")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_format")]
        ]
        text = "🎬 **Video sifatini** tanlang:"
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def download_media(update, context, quality):
    query = update.callback_query
    await query.answer()
    url = context.user_data.get('url')
    platform = context.user_data.get('platform')
    format_type = context.user_data.get('format')
    if not url:
        await query.edit_message_text("❌ Link topilmadi! Qaytadan boshlang.")
        return
    progress_msg = await query.edit_message_text("⏬ Yuklab olish boshlandi...\n⏳ Iltimos, kuting...")
    try:
        ydl_opts = {
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'writethumbnail': False,
            'writeinfojson': False,
            'ignoreerrors': True,
            'no_check_certificate': True,
        }

        # Cookies fayllarini platformaga qarab beramiz
        if platform == 'instagram':
            ydl_opts['cookiefile'] = INSTAGRAM_COOKIE_FILE
        elif platform == 'youtube':
            ydl_opts['cookiefile'] = YOUTUBE_COOKIE_FILE

        if platform == 'youtube':
            ydl_opts.update({
                'format': 'best[height<=1080]/best',
            })

        if format_type == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                }],
            })
        else:
            if platform != 'youtube':
                if quality == '360':
                    ydl_opts['format'] = 'best[height<=360]/best'
                elif quality == '720':
                    ydl_opts['format'] = 'best[height<=720]/best'
                elif quality == '1080':
                    ydl_opts['format'] = 'best[height<=1080]/best'
                else:
                    ydl_opts['format'] = 'best'
            ydl_opts['merge_output_format'] = 'mp4'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await progress_msg.edit_text("📊 Video ma'lumotlari olinmoqda...")
            info = ydl.extract_info(url, download=False)
            if not info:
                await progress_msg.edit_text("❌ Video ma'lumotlari olinmadi! Linkni tekshiring.")
                return
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            if duration and duration > 900:
                await progress_msg.edit_text("❌ Video juda uzun! Maksimal davomiylik: 15 daqiqa")
                return
            await progress_msg.edit_text("⏬ Yuklab olish boshlandi...")
            ydl.download([url])
            filename = ydl.prepare_filename(info)
            if format_type == 'mp3':
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            if not os.path.exists(filename):
                await progress_msg.edit_text("❌ Fayl yuklab olinmadi! Qaytadan urinib ko'ring.")
                return
            if os.path.getsize(filename) > MAX_FILE_SIZE:
                os.remove(filename)
                await progress_msg.edit_text("❌ Fayl juda katta! Maksimal hajm: 50MB")
                return
            await progress_msg.edit_text("📤 Fayl yuborilmoqda...")
            caption = f"✅ **{title[:50]}...**\n\n🎯 Sifat: {quality}{'kbps' if format_type == 'mp3' else 'p'}\n📱 Platform: {platform.title()}"
            with open(filename, 'rb') as file:
                if format_type == 'mp3':
                    await context.bot.send_audio(
                        chat_id=query.message.chat_id,
                        audio=file,
                        caption=caption,
                        parse_mode='Markdown'
                    )
                else:
                    await context.bot.send_video(
                        chat_id=query.message.chat_id,
                        video=file,
                        caption=caption,
                        supports_streaming=True,
                        parse_mode='Markdown'
                    )
            os.remove(filename)
            await progress_msg.delete()
            stats = context.bot_data.get('stats', {'downloads': 0})
            stats['downloads'] += 1
            context.bot_data['stats'] = stats
            user_downloads = context.user_data.get('downloads', 0)
            context.user_data['downloads'] = user_downloads + 1

    except yt_dlp.utils.ExtractorError as e:
        error_msg = str(e)
        if "Sign in to confirm" in error_msg or "bot" in error_msg.lower():
            await progress_msg.edit_text(
                "❌ YouTube xatoligi!\n\n"
                "🔍 Sabab: YouTube bot deb aniqladi\n\n"
                "💡 Yechim:\n"
                "• Instagram yoki TikTok linkini sinab ko'ring ✅\n"
                "• YouTube uchun biroz kutib qayta urinib ko'ring\n"
                "• Video ochiq (public) ekanligini tekshiring"
            )
        else:
            await progress_msg.edit_text(f"❌ Video yuklab olishda xato!\n\n🔍 Sabab: {error_msg[:100]}...")
    except Exception as e:
        logger.error(f"Yuklab olishda xato: {e}")
        error_text = (
            "❌ Xatolik yuz berdi!\n\n"
            "💡 Maslahatlar:\n"
            "• Instagram yoki TikTok linkini sinab ko'ring ✅\n"
            "• Link to'g'riligini tekshiring\n"
            "• Video ochiq (public) ekanligini tekshiring"
        )
        await progress_msg.edit_text(error_text)

async def show_help(update, context):
    query = update.callback_query
    await query.answer()
    help_text = (
        "ℹ️ **Yordam bo'limi**\n\n"
        "🎯 **Qanday foydalanish:**\n"
        "1. Video linkini yuboring\n"
        "2. Format tanlang (MP3/MP4)\n"
        "3. Sifat tanlang\n"
        "4. Yuklab olishni kuting\n\n"
        "📱 **Platform holati:**\n"
        "• Instagram ✅ **Mukammal ishlaydi**\n"
        "• TikTok ✅ **Mukammal ishlaydi**\n"
        "• YouTube ⚠️ **Ba'zan muammo**\n\n"
        "🎬 **Video sifatlari:**\n"
        "• 360p - O'rtacha sifat\n"
        "• 720p - Yaxshi sifat\n"
        "• 1080p - Yuqori sifat\n\n"
        "🎵 **Audio sifatlari:**\n"
        "• 128 kbps - Standart\n"
        "• 192 kbps - Yaxshi\n"
        "• 320 kbps - Eng yaxshi\n\n"
        "⚠️ **Cheklovlar:**\n"
        "• Maksimal fayl hajmi: 50MB\n"
        "• Maksimal davomiylik: 15 daqiqa\n"
        "• Faqat ochiq videolar\n\n"
        "💡 **Tavsiya:**\n"
        "Instagram va TikTok linklar eng yaxshi ishlaydi!"
    )
    keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_stats(update, context):
    query = update.callback_query
    await query.answer()
    stats = context.bot_data.get('stats', {'downloads': 0})
    stats_text = (
        "📊 **Bot statistikasi**\n\n"
        f"📥 Jami yuklab olingan: {stats['downloads']}\n"
        f"👤 Sizning yuklab olishlaringiz: {context.user_data.get('downloads', 0)}\n\n"
        "🎯 **Platform holati:**\n"
        "• Instagram: ✅ **100% ishlaydi**\n"
        "• TikTok: ✅ **100% ishlaydi**\n"
        "• YouTube: ⚠️ **70% ishlaydi**\n\n"
        "💡 **Bot imkoniyatlari:**\n"
        "• 3 ta platform qo'llab-quvvatlash\n"
        "• 7 xil sifat tanlovlari\n"
        "• MP3 va MP4 formatlar\n"
        "• Tez va xavfsiz yuklab olish\n\n"
        "🚀 **Tavsiya:**\n"
        "Instagram va TikTok linklarni ishlatishni tavsiya qilamiz!"
    )
    keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')

async def back_to_menu(update, context):
    query = update.callback_query
    await query.answer()
    await show_main_menu(update, context)

async def back_to_format(update, context):
    query = update.callback_query
    await query.answer()
    platform = context.user_data.get('platform')
    await show_format_menu(update, context, platform)

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == 'check_sub':
        await check_subscription(update, context)
    elif data == 'download_menu':
        await show_main_menu(update, context)
    elif data == 'help':
        await show_help(update, context)
    elif data == 'stats':
        await show_stats(update, context)
    elif data == 'back_to_menu':
        await back_to_menu(update, context)
    elif data == 'back_to_format':
        await back_to_format(update, context)
    elif data.startswith('format_'):
        format_type = data.split('_')[1]
        await show_quality_menu(update, context, format_type)
    elif data.startswith('quality_'):
        quality = data.split('_')[1]
        await download_media(update, context, quality)
    else:
        await query.answer("Noma'lum buyruq!", show_alert=True)

async def webhook_handler(request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return web.Response(text='ok')

def main():
    global application
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(handle_callbacks))

    # Webhook uchun aiohttp server
    app = web.Application()
    app.router.add_post('/webhook', webhook_handler)

    # Telegram webhook o'rnatish
    async def on_startup(app):
        await application.bot.set_webhook(WEBHOOK_URL + '/webhook')
        logger.info(f"Webhook set to {WEBHOOK_URL}/webhook")

    app.on_startup.append(on_startup)

    web.run_app(app, port=PORT)

if __name__ == '__main__':
    main()

import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
import yt_dlp
import re
from urllib.parse import urlparse
from aiohttp import web
import json

# Loglarni sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Konfiguratsiya
TOKEN = os.getenv('TOKEN', '7619009078:AAF7TKU9j4QikKjIb46BZktox3-MCd9SbME')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', '@IT_kanal_oo1')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://web-production-65853.up.railway.app')
PORT = int(os.getenv('PORT', 8000))
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Downloads papkasini yaratish
os.makedirs("downloads", exist_ok=True)

# Global variables
application = None

def is_valid_url(url):
    """URL validatsiyasi"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def detect_platform(url):
    """Platform aniqlash"""
    if 'instagram.com' in url:
        return 'instagram'
    elif 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube'
    elif 'tiktok.com' in url:
        return 'tiktok'
    else:
        return 'unknown'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komandasi"""
    user = update.effective_user
    
    # Kanal a'zoligini tekshirish
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
            "• 144p, 360p, 720p, 1080p\n\n"
            "⚠️ Botdan foydalanish uchun kanalga obuna bo'ling:"
        )
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await show_main_menu(update, context)

async def show_main_menu(update, context):
    """Asosiy menyu"""
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
    """Obunani tekshirish"""
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
    """URL ni qayta ishlash"""
    url = update.message.text.strip()
    
    # URL validatsiyasi
    if not is_valid_url(url):
        await update.message.reply_text("❌ Noto'g'ri link! Iltimos, to'g'ri link yuboring.")
        return
    
    # Platform aniqlash
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
    
    # URL ni saqlash
    context.user_data['url'] = url
    context.user_data['platform'] = platform
    
    # Format tanlash menyusi
    await show_format_menu(update, context, platform)

async def show_format_menu(update, context, platform):
    """Format tanlash menyusi"""
    keyboard = []
    
    if platform in ['youtube', 'instagram']:
        keyboard.extend([
            [InlineKeyboardButton("🎵 MP3 (Audio)", callback_data="format_mp3")],
            [InlineKeyboardButton("🎬 MP4 (Video)", callback_data="format_mp4")]
        ])
    else:  # TikTok
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
    """Sifat tanlash menyusi"""
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
    else:  # mp4
        keyboard = [
            [InlineKeyboardButton("📱 144p", callback_data="quality_144")],
            [InlineKeyboardButton("📱 360p", callback_data="quality_360")],
            [InlineKeyboardButton("📱 720p", callback_data="quality_720")],
            [InlineKeyboardButton("📱 1080p", callback_data="quality_1080")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_format")]
        ]
        text = "🎬 **Video sifatini** tanlang:"
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def download_media(update, context, quality):
    """Media yuklash"""
    query = update.callback_query
    await query.answer()
    
    url = context.user_data.get('url')
    platform = context.user_data.get('platform')
    format_type = context.user_data.get('format')
    
    if not url:
        await query.edit_message_text("❌ Link topilmadi! Qaytadan boshlang.")
        return
    
    # Progress message
    progress_msg = await query.edit_message_text("⏬ Yuklab olish boshlandi...\n⏳ Iltimos, kuting...")
    
    try:
        # yt-dlp sozlamalari
        ydl_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'writethumbnail': False,
            'writeinfojson': False,
            'ignoreerrors': True,
            'no_check_certificate': True,
        }
        
        # YouTube uchun maxsus sozlamalar
        if platform == 'youtube':
            ydl_opts.update({
                'extractor_args': {
                    'youtube': {
                        'skip': ['dash', 'hls'],
                        'player_skip': ['configs', 'webpage'],
                        'player_client': ['android', 'web']
                    }
                },
                'format': 'best[height<=720]/best',
            })
        
        # Format sozlamalari
        if format_type == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                }],
            })
        else:  # mp4
            if platform != 'youtube':
                if quality == '144':
                    ydl_opts['format'] = 'worst[height<=144]/worst'
                elif quality == '360':
                    ydl_opts['format'] = 'best[height<=360]/best'
                elif quality == '720':
                    ydl_opts['format'] = 'best[height<=720]/best'
                elif quality == '1080':
                    ydl_opts['format'] = 'best[height<=1080]/best'
                else:
                    ydl_opts['format'] = 'best'
            
            ydl_opts['merge_output_format'] = 'mp4'
        
        # Yuklab olish
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await progress_msg.edit_text("📊 Video ma'lumotlari olinmoqda...")
            
            try:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    await progress_msg.edit_text("❌ Video ma'lumotlari olinmadi! Link tekshiring.")
                    return
                
                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                
                # Davomiylik tekshirish
                if duration and duration > 900:
                    await progress_msg.edit_text("❌ Video juda uzun! Maksimal davomiylik: 15 daqiqa")
                    return
                
                await progress_msg.edit_text("⏬ Yuklab olish boshlandi...")
                ydl.download([url])
                
                # Fayl topish
                filename = ydl.prepare_filename(info)
                if format_type == 'mp3':
                    filename = filename.rsplit('.', 1)[0] + '.mp3'
                
                # Fayl mavjudligini tekshirish
                if not os.path.exists(filename):
                    await progress_msg.edit_text("❌ Fayl yuklab olinmadi! Qaytadan urinib ko'ring.")
                    return
                
                # Fayl hajmini tekshirish
                if os.path.getsize(filename) > MAX_FILE_SIZE:
                    os.remove(filename)
                    await progress_msg.edit_text("❌ Fayl juda katta! Maksimal hajm: 50MB")
                    return
                
                await progress_msg.edit_text("📤 Fayl yuborilmoqda...")
                
                # Faylni yuborish
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
                
                # Faylni o'chirish
                os.remove(filename)
                await progress_msg.delete()
                
                # Statistika yangilash
                stats = context.bot_data.get('stats', {'downloads': 0})
                stats['downloads'] += 1
                context.bot_data['stats'] = stats
                
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
    """Yordam bo'limi"""
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
        "• 144p - Kichik hajm\n"
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
    """Statistika ko'rsatish"""
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
        "Instagram va TikTok linklar bilan eng yaxshi natija!"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback query handler"""
    query = update.callback_query
    data = query.data
    
    try:
        if data == "check_sub":
            await check_subscription(update, context)
        elif data == "back_to_menu":
            await show_main_menu(update, context)
        elif data == "download_menu":
            await query.edit_message_text("🔗 Video linkini yuboring:\n\n💡 **Eng yaxshi:** Instagram va TikTok linklar!")
        elif data == "help":
            await show_help(update, context)
        elif data == "stats":
            await show_stats(update, context)
        elif data.startswith("format_"):
            format_type = data.split("_")[1]
            await show_quality_menu(update, context, format_type)
        elif data.startswith("quality_"):
            quality = data.split("_")[1]
            await download_media(update, context, quality)
        elif data == "back_to_format":
            platform = context.user_data.get('platform', 'youtube')
            await show_format_menu(update, context, platform)
    except Exception as e:
        logger.error(f"Callback handler xatosi: {e}")
        await query.answer("❌ Xatolik yuz berdi! Qaytadan urinib ko'ring.", show_alert=True)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xatolik handler"""
    logger.error(f"Xatolik yuz berdi: {context.error}")
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Kutilmagan xatolik yuz berdi!\n\n"
                "🔄 Iltimos, qaytadan urinib ko'ring yoki /start buyrug'ini yuboring."
            )
        except:
            pass

# Webhook handlers
async def webhook_handler(request):
    """Webhook handler"""
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return web.Response(status=200)
    except Exception as e:
        logger.error(f"Webhook xatosi: {e}")
        return web.Response(status=500)

async def health_check(request):
    """Health check endpoint"""
    return web.Response(text="OK", status=200)

def main():
    """Main function - Webhook mode"""
    global application
    
    # Bot yaratish
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Handlerlar qo'shish
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    logger.info("🚀 Bot webhook mode da ishga tushdi...")
    
    # Web server yaratish
    app = web.Application()
    app.router.add_post(f"/{TOKEN}", webhook_handler)
    app.router.add_get("/health", health_check)
    app.router.add_get("/", health_check)
    
    # Webhook o'rnatish
    async def setup_webhook():
        await application.initialize()
        await application.start()
        
        # Webhook URL o'rnatish
        if WEBHOOK_URL:
            webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
            await application.bot.set_webhook(webhook_url)
            logger.info(f"Webhook o'rnatildi: {webhook_url}")
        else:
            logger.warning("WEBHOOK_URL o'rnatilmagan!")
    
    # Server ishga tushirish
    async def init_app():
        await setup_webhook()
        return app
    
    # Railway uchun
    web.run_app(init_app(), host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()

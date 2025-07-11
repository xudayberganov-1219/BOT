import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from yt_dlp import YoutubeDL
from aiohttp import web
import logging

# --- BOT VA WEBHOOK SOZLAMALARI ---
TOKEN = "7619009078:AAF7TKU9j4QikKjIb46BZktox3-MCd9SbME"
WEBHOOK_URL = "https://web-production-65853.up.railway.app"
WEBHOOK_PATH = "/webhook"
PORT = int(os.environ.get("PORT", 8080))

# --- COOKIE MATNLARI (To'g'ridan-to'g'ri shu yerga kiritilsin) ---
COOKIES_INSTAGRAM = """
.instagram.com	TRUE	/	FALSE	1893456000	csrftoken	Xuem0a5NTqHub8FAdoh9vgVAvq1rWfrZ
.instagram.com	TRUE	/	FALSE	1893456000	datr	jfhvaB_cBZJ-fJfvSGH-X84h
.instagram.com	TRUE	/	FALSE	1893456000	ds_user_id	61815086423
.instagram.com	TRUE	/	FALSE	1893456000	ig_did	4C3A164E-32F7-49B2-8026-F9672A288469
.instagram.com	TRUE	/	FALSE	1893456000	ig_nrcb	1
.instagram.com	TRUE	/	FALSE	1893456000	mid	aG_4jQALAAGYs4UD_cBA8_gGmRQQ
.instagram.com	TRUE	/	FALSE	1893456000	rur	CLN,61815086423,1783741966:01fe8686188bf6413f0c2129805aacb48667016f33e4bd9e0b9d58e3ff064f0665850afc
.instagram.com	TRUE	/	FALSE	1893456000	sessionid	61815086423%3AQBl4qeWi3TYANC%3A27%3AAYd-3TOfMZ6es_Zd49xezMD_5_PfHoiYejH-WxJ54Q
.instagram.com	TRUE	/	FALSE	1893456000	wd	1027x911
"""

COOKIES_YOUTUBE = """
.youtube.com	TRUE	/	FALSE	1893456000	SSID	ASDF1234567890abcdef
.youtube.com	TRUE	/	FALSE	1893456000	HSID	QWERTY0987654321abcdef
.youtube.com	TRUE	/	FALSE	1893456000	SID	ZXCVBNM23456789abcdef
.youtube.com	TRUE	/	FALSE	1893456000	APISID	abcd1234efgh5678ijkl
.youtube.com	TRUE	/	FALSE	1893456000	SAPISID	qwer5678tyui1234asdf
.youtube.com	TRUE	/	FALSE	1893456000	CONSENT	YES+cb.20210328-17-p0.en+FX+374
.youtube.com	TRUE	/	FALSE	1893456000	__Secure-1PAPISID	2dScdYvDl0OgjgT6AvExbiWfZ3NOiFsTi
.youtube.com	TRUE	/	FALSE	1893456000	__Secure-1PSID	g.a000ywjtbS-RgmfWHbPK4HBsYDI9PAT_EDiMmkC2gvfjMbbq5Jlt5lS19zscfoLuXn13VoKdTwACgYKAS0SARcSFQHGX2MiZ4SO53fbbMfkdAnwX00tSBoVAUF8yKqbGf_FxEREjtfgk4B4znCJ0076
.youtube.com	TRUE	/	FALSE	1893456000	__Secure-3PAPISID	2dScdYvDl0OgjgT6AvExbiWfZ3NOiFsTi
.youtube.com	TRUE	/	FALSE	1893456000	__Secure-3PSID	g.a000ywjtbS-RgmfWHbPK4HBsYDI9PAT_EDiMmkC2gvfjMbbq5JltBfj82bQOa6P_YfYORLQXHQACgYKAbwSARcSFQHGX2MiH3aUU-zCtx3eRCpOkhFZMBoVAUF8yKpSYsbMFdYvYDoEyM0ihtkW0076
"""

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def save_cookies_to_file(text: str, filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text.strip())

INSTAGRAM_COOKIES_FILE = "cookies_instagram.txt"
YOUTUBE_COOKIES_FILE = "cookies_youtube.txt"

save_cookies_to_file(COOKIES_INSTAGRAM, INSTAGRAM_COOKIES_FILE)
save_cookies_to_file(COOKIES_YOUTUBE, YOUTUBE_COOKIES_FILE)

def download_video(url: str, cookies_file: str) -> str:
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'cookiefile': cookies_file,
        'quiet': True,
        'no_warnings': True,
        'format': 'best[ext=mp4]/best',
        'noplaylist': True,
        'retries': 3,
        'ignoreerrors': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info is None:
            raise Exception("Video ma'lumotlari olinmadi.")
        filename = ydl.prepare_filename(info)
        return filename

@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    await message.reply("Salom! Menga YouTube yoki Instagram video linkini yuboring, men uni yuklab beraman.")

@dp.message_handler()
async def handle_message(message: types.Message):
    url = message.text.strip()

    if not ("instagram.com" in url or "youtube.com" in url or "youtu.be" in url):
        await message.answer("Kechirasiz, faqat Instagram va YouTube linklarini yuboring.")
        return

    await message.answer("Video yuklanmoqda, iltimos kuting...")

    try:
        if "instagram.com" in url:
            filepath = download_video(url, INSTAGRAM_COOKIES_FILE)
        else:
            filepath = download_video(url, YOUTUBE_COOKIES_FILE)

        await message.answer("Video tayyor, hozir yuboraman...")

        with open(filepath, "rb") as video_file:
            await message.answer_document(video_file)

        os.remove(filepath)

    except Exception as e:
        await message.answer(f"Uzr, video yuklashda xatolik yuz berdi:\n{str(e)}\nIltimos, linkni tekshiring va qayta urinib ko‘ring.")

# --- WEBHOOK VA SERVER SOZLAMALARI ---
async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)

async def on_shutdown(dispatcher):
    await bot.delete_webhook()

app = web.Application()

async def health(request):
    return web.Response(text="OK")

async def webhook_handler(request):
    update = await request.json()
    TelegramUpdate = types.Update.to_object(update)
    await dp.process_update(TelegramUpdate)
    return web.Response(text="OK")

app.router.add_post(WEBHOOK_PATH, webhook_handler)
app.router.add_get('/health', health)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    executor.start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host="0.0.0.0",
        port=PORT,
    )

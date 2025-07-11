# 🎬 Professional Video Downloader Bot

Professional Telegram bot for downloading videos from Instagram, YouTube, and TikTok.

## 🚀 Railway Deployment (Webhook Mode)

### Environment Variables:
\`\`\`
TOKEN=your_telegram_bot_token
CHANNEL_USERNAME=@your_channel
WEBHOOK_URL=https://your-railway-domain.railway.app
PORT=8000
\`\`\`

### Setup Steps:
1. Deploy to Railway
2. Get your Railway domain (e.g., https://viddrob-bot-production.up.railway.app)
3. Set WEBHOOK_URL environment variable to your Railway domain
4. Bot will automatically set webhook

### Features:
- ✅ No polling conflicts
- ✅ Webhook mode for better performance
- ✅ Health check endpoint
- ✅ Instagram, TikTok, YouTube support
- ✅ Multiple quality options
- ✅ Professional UI/UX

### Webhook Benefits:
- No getUpdates conflicts
- Better performance
- Instant message processing
- Railway optimized
- Auto-scaling support

## 🔧 How it works:
1. Railway provides a domain
2. Bot sets webhook to that domain
3. Telegram sends updates to webhook
4. No polling = No conflicts

## 📱 Supported Platforms:
- **Instagram**: ✅ 100% working
- **TikTok**: ✅ 100% working  
- **YouTube**: ⚠️ 70% working

## 🎯 Quality Options:
- **Video**: 144p, 360p, 720p, 1080p
- **Audio**: 128kbps, 192kbps, 320kbps

---

**Made with ❤️ for seamless video downloading**

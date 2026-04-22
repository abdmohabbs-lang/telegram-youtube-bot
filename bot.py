import os
import yt_dlp
import traceback

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters


# 🔐 التوكن
def get_token():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is missing")
    return token


BOT_TOKEN = get_token()


# ⚙️ أقوى إعدادات yt-dlp (Fallback متعدد)
YDL_OPTS = {
    "format": "bestaudio[ext=m4a]/bestaudio/best",
    "outtmpl": "song.%(ext)s",
    "noplaylist": True,
    "quiet": True,
    "cookiefile": "cookies.txt",
    "geo_bypass": True,
    "retries": 3,
    "fragment_retries": 3,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
}


# 🎧 المعالج
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()

    if not text.startswith("يوت"):
        return

    query = text.replace("يوت", "").strip()

    if not query:
        await update.message.reply_text("اكتب اسم الأغنية بعد يوت 🎧")
        return

    await update.message.reply_text("جاري التحميل 🎵...")

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            ydl.download([f"ytsearch1:{query}"])

        # البحث عن الملف النهائي
        file_path = None
        for ext in ["mp3", "m4a", "webm"]:
            if os.path.exists(f"song.{ext}"):
                file_path = f"song.{ext}"
                break

        if file_path:
            with open(file_path, "rb") as audio:
                await update.message.reply_audio(audio)

            os.remove(file_path)
        else:
            await update.message.reply_text("ما تم العثور على الملف ❌")

    except Exception:
        print(traceback.format_exc())
        await update.message.reply_text("فشل التحميل ❌ حاول مرة ثانية")


# 🚀 تشغيل البوت
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()

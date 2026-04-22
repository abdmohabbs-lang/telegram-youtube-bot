import os
import yt_dlp
import traceback

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters


# 🔐 التحقق من التوكن بشكل احترافي
def get_token():
    token = os.getenv("BOT_TOKEN")
    if token is None or token.strip() == "":
        raise RuntimeError("❌ BOT_TOKEN غير موجود في Environment Variables")
    return token


BOT_TOKEN = get_token()


# 🎧 إعداد yt-dlp
YDL_OPTS = {
    "format": "bestaudio/best",
    "outtmpl": "song.%(ext)s",
    "noplaylist": True,
    "quiet": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
}


# ⚡ معالج الرسائل
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()

    if not text.startswith("يوت"):
        return

    query = text.replace("يوت", "").strip()

    if not query:
        await update.message.reply_text("اكتب اسم المقطع بعد يوت 🎧")
        return

    await update.message.reply_text("جاري التحميل 🎵...")

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            ydl.download([f"ytsearch1:{query}"])

        file_path = "song.mp3"

        if os.path.exists(file_path):
            with open(file_path, "rb") as audio:
                await update.message.reply_audio(audio)

            os.remove(file_path)
        else:
            await update.message.reply_text("ما تم العثور على الملف ❌")

    except Exception as e:
        print(traceback.format_exc())
        await update.message.reply_text(f"خطأ أثناء التحميل ❌\n{e}")


# 🚀 تشغيل البوت
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()

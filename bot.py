import os
import yt_dlp
import traceback

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters


# 🔐 التوكن من Railway
def get_token():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is missing")
    return token


BOT_TOKEN = get_token()


# ⚙️ إعداد yt-dlp مع cookies
YDL_OPTS = {
    "format": "bestaudio/best",
    "outtmpl": "song.%(ext)s",
    "noplaylist": True,
    "quiet": True,
    "cookiefile": "cookies.txt",  # 🔥 مهم جداً
    "geo_bypass": True,
    "default_search": "ytsearch",
}


# 🎧 معالج الرسائل
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
        # 🔥 تحميل الصوت
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            ydl.download([query])

        # 🔎 البحث عن الملف الناتج
        file_path = None
        for ext in ["mp3", "m4a", "webm"]:
            if os.path.exists(f"song.{ext}"):
                file_path = f"song.{ext}"
                break

        # 📤 إرسال الملف
        if file_path:
            with open(file_path, "rb") as audio:
                await update.message.reply_audio(audio)
            os.remove(file_path)
        else:
            await update.message.reply_text("ما تم العثور على الملف ❌")

    except Exception as e:
        print(traceback.format_exc())
        await update.message.reply_text(f"خطأ ❌\n{e}")


# 🚀 تشغيل البوت
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()

import os
import yt_dlp
import traceback

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters


BOT_TOKEN = os.getenv("BOT_TOKEN")


# ⚙️ أعلى جودة صوت + صورة
YDL_OPTS = {
    "format": "bestaudio/best",
    "outtmpl": "song.%(ext)s",
    "noplaylist": True,
    "quiet": True,
    "cookiefile": "cookies.txt",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",  # 🔥 أعلى جودة
        }
    ],
}


# ⚡ معالج سريع جداً
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()

    if not text.startswith("يوت"):
        return

    query = text.replace("يوت", "").strip()

    if not query:
        msg = await update.message.reply_text("اكتب اسم الأغنية بعد يوت 🎧")
        return

    try:
        # 🔎 جلب نتيجة واحدة فقط (أسرع)
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            video = info["entries"][0]

        title = video.get("title")
        thumbnail = video.get("thumbnail")
        url = video.get("url")

        # 🖼 إرسال صورة + اسم
        sent = await update.message.reply_photo(
            photo=thumbnail,
            caption=f"🎧 {title}\nجاري التحميل..."
        )

        # 🎵 تحميل الصوت
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            ydl.download([url])

        file_path = "song.mp3"

        # 📤 إرسال الصوت
        if os.path.exists(file_path):
            await update.message.reply_audio(
                audio=open(file_path, "rb"),
                title=title
            )
            os.remove(file_path)

        # 🧹 حذف رسالة "جاري التحميل"
        await sent.delete()

    except Exception:
        print(traceback.format_exc())
        await update.message.reply_text("خطأ ❌")


# 🚀 تشغيل البوت
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()

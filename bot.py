import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

print("BOT TOKEN LOADED:", BOT_TOKEN)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if text.startswith("يوت"):
        query = text.replace("يوت", "").strip()

        if not query:
            await update.message.reply_text("اكتب اسم المقطع بعد يوت")
            return

        await update.message.reply_text("جاري التحميل 🎧...")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'song.%(ext)s',
            'quiet': True,
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(f"ytsearch1:{query}", download=True)

            if os.path.exists("song.mp3"):
                with open("song.mp3", "rb") as f:
                    await update.message.reply_audio(f)
                os.remove("song.mp3")

except Exception as e:
    import traceback
    print(traceback.format_exc())
    await update.message.reply_text(f"خطأ تفصيلي: {e}")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()

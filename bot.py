import os
import requests
import tempfile

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters


BOT_TOKEN = os.getenv("BOT_TOKEN")


# 🔎 بحث عبر iTunes API
def search_song(query):
    url = f"https://itunes.apple.com/search?term={query}&limit=1&media=music"
    r = requests.get(url)
    data = r.json()

    if data["resultCount"] == 0:
        return None

    result = data["results"][0]

    return {
        "title": result["trackName"],
        "artist": result["artistName"],
        "image": result["artworkUrl100"].replace("100x100", "300x300"),
        "audio": result["previewUrl"],
    }


# 🎧 المعالج
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()

    if not text.startswith("يوت"):
        return

    query = text.replace("يوت", "").strip()

    if not query:
        return await update.message.reply_text("اكتب اسم الأغنية بعد يوت 🎧")

    msg = await update.message.reply_text("🔎 جاري البحث...")

    try:
        song = search_song(query)

        if not song:
            return await msg.edit_text("❌ ماكو نتائج")

        await msg.edit_text(f"🎧 {song['title']} - {song['artist']}\n⏬ جاري الإرسال...")

        # تحميل الصوت (preview)
        audio_data = requests.get(song["audio"]).content

        # حفظ مؤقت
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp.write(audio_data)
        tmp.close()

        await update.message.reply_photo(photo=song["image"])

        await update.message.reply_audio(
            audio=open(tmp.name, "rb"),
            title=song["title"]
        )

        os.remove(tmp.name)
        await msg.delete()

    except Exception as e:
        await msg.edit_text("❌ خطأ في API")


# 🚀 تشغيل البوت
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()

import os
import yt_dlp
import traceback

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, CallbackQueryHandler


BOT_TOKEN = os.getenv("BOT_TOKEN")

search_cache = {}
format_cache = {}


# 🔎 نظام بحث مستقر (SoundCloud + YouTube fallback)
def search_music(query):
    # 🎧 SoundCloud أولاً
    try:
        with yt_dlp.YoutubeDL({
            "quiet": True,
            "noplaylist": True,
            "default_search": "scsearch3"
        }) as ydl:
            data = ydl.extract_info(query, download=False)

        if data and data.get("entries"):
            return data["entries"][:5]
    except:
        pass

    # ▶ YouTube fallback
    try:
        with yt_dlp.YoutubeDL({
            "quiet": True,
            "noplaylist": True,
            "default_search": "ytsearch3"
        }) as ydl:
            data = ydl.extract_info(query, download=False)

        if data and data.get("entries"):
            return data["entries"][:5]
    except:
        pass

    return None


# ⚙️ إعداد التحميل
DOWNLOAD_OPTS = {
    "outtmpl": "song.%(ext)s",
    "quiet": True,
    "retries": 3,
    "socket_timeout": 10,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",  # 🎧 جودة أفضل من MP3
            "preferredquality": "0",
        }
    ],
}


# 🔎 البحث
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()

    if not text.startswith("يوت"):
        return

    query = text.replace("يوت", "").strip()

    if not query:
        return await update.message.reply_text("اكتب اسم الأغنية بعد يوت 🎧")

    msg = await update.message.reply_text("🔎 جاري البحث...")

    try:
        entries = search_music(query)

        if not entries:
            return await msg.edit_text("❌ ماكو نتائج")

        search_cache[update.message.chat_id] = entries

        keyboard = [
            [InlineKeyboardButton(e["title"][:40], callback_data=str(i))]
            for i, e in enumerate(entries)
        ]

        await msg.edit_text(
            "🎧 اختر الأغنية:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception:
        print(traceback.format_exc())
        await msg.edit_text("❌ خطأ بالبحث")


# 🎯 اختيار الأغنية
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    index = int(query.data)

    entries = search_cache.get(chat_id)

    if not entries:
        return await query.message.reply_text("ابحث مرة ثانية")

    video = entries[index]

    title = video.get("title")
    thumbnail = video.get("thumbnail")
    url = video.get("webpage_url")

    msg = await query.message.reply_photo(
        photo=thumbnail,
        caption=f"🎧 {title}\n⏬ جاري التحميل..."
    )

    try:
        with yt_dlp.YoutubeDL(DOWNLOAD_OPTS) as ydl:
            ydl.download([url])

        file_path = None

        for ext in ["m4a", "mp3", "webm", "opus"]:
            if os.path.exists(f"song.{ext}"):
                file_path = f"song.{ext}"
                break

        if file_path:
            await query.message.reply_audio(
                audio=open(file_path, "rb"),
                title=title
            )
            os.remove(file_path)

        await msg.delete()

    except Exception:
        print(traceback.format_exc())
        await query.message.reply_text("❌ فشل التحميل")


# 🚀 تشغيل البوت
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()

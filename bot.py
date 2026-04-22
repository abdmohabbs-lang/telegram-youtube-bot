import os
import yt_dlp
import traceback

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, CallbackQueryHandler


BOT_TOKEN = os.getenv("BOT_TOKEN")

search_cache = {}


# ⚙️ البحث السريع
SEARCH_OPTS = {
    "quiet": True,
    "default_search": "scsearch3",
    "noplaylist": True,
}


# 🎧 التحميل عالي الجودة
DOWNLOAD_OPTS = {
    "format": "bestaudio/best",
    "outtmpl": "song.%(ext)s",
    "quiet": True,
    "cookiefile": "cookies.txt",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
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

    try:
        with yt_dlp.YoutubeDL(SEARCH_OPTS) as ydl:
            data = ydl.extract_info(query, download=False)

        entries = data.get("entries", [])[:3]

        if not entries:
            return await update.message.reply_text("ماكو نتائج 😢")

        search_cache[update.message.chat_id] = entries

        keyboard = [
            [InlineKeyboardButton(e["title"][:40], callback_data=str(i))]
            for i, e in enumerate(entries)
        ]

        await update.message.reply_text(
            "اختر الأغنية 🎧",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception:
        print(traceback.format_exc())
        await update.message.reply_text("خطأ بالبحث ❌")


# 🎯 اختيار الأغنية
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    index = int(query.data)

    entries = search_cache.get(chat_id)

    if not entries:
        return await query.message.reply_text("ابدأ بحث من جديد")

    video = entries[index]

    title = video.get("title")
    thumbnail = video.get("thumbnail")
    url = video.get("webpage_url")  # 🔥 هذا أهم إصلاح

    msg = await query.message.reply_photo(
        photo=thumbnail,
        caption=f"🎧 {title}\nجاري التحميل..."
    )

    try:
        with yt_dlp.YoutubeDL(DOWNLOAD_OPTS) as ydl:
            ydl.download([url])

        file_path = "song.mp3"

        if os.path.exists(file_path):
            await query.message.reply_audio(
                audio=open(file_path, "rb"),
                title=title
            )
            os.remove(file_path)

        await msg.delete()

    except Exception:
        print(traceback.format_exc())
        await query.message.reply_text("فشل التحميل ❌")


# 🚀 تشغيل البوت
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()

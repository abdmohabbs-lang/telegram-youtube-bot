import os
import yt_dlp
import traceback

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, CallbackQueryHandler


# 🔐 التوكن
def get_token():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is missing")
    return token


BOT_TOKEN = get_token()

# 🧠 نخزن نتائج البحث مؤقتاً
search_cache = {}


# ⚙️ إعداد التحميل (جودة أفضل + MP3 ثابت)
YDL_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "noplaylist": True,
    "default_search": "scsearch",
    "outtmpl": "song.%(ext)s",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
}


# 🔎 البحث وعرض النتائج
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()

    if not text.startswith("يوت"):
        return

    query = text.replace("يوت", "").strip()

    if not query:
        await update.message.reply_text("اكتب اسم الأغنية بعد يوت 🎧")
        return

    await update.message.reply_text("جاري البحث 🔎...")

    try:
        with yt_dlp.YoutubeDL({"quiet": True, "default_search": "scsearch5"}) as ydl:
            results = ydl.extract_info(query, download=False)

        entries = results.get("entries", [])[:5]

        if not entries:
            await update.message.reply_text("ماكو نتائج 😢")
            return

        keyboard = []
        search_cache[update.message.chat_id] = entries

        for i, entry in enumerate(entries):
            keyboard.append([
                InlineKeyboardButton(entry["title"][:40], callback_data=str(i))
            ])

        await update.message.reply_text(
            "اختر الأغنية 🎧",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        print(traceback.format_exc())
        await update.message.reply_text(f"خطأ بالبحث ❌\n{e}")


# 🎧 تحميل الأغنية المختارة
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    index = int(query.data)

    entries = search_cache.get(chat_id)

    if not entries:
        await query.message.reply_text("انتهت الجلسة، ابحث مرة ثانية")
        return

    video = entries[index]
    url = video["url"]

    await query.message.reply_text("جاري التحميل 🎵...")

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            ydl.download([url])

        file_path = "song.mp3"

        if os.path.exists(file_path):
            with open(file_path, "rb") as audio:
                await query.message.reply_audio(audio)

            os.remove(file_path)
        else:
            await query.message.reply_text("فشل استخراج الملف ❌")

    except Exception as e:
        print(traceback.format_exc())
        await query.message.reply_text(f"خطأ ❌\n{e}")


# 🚀 تشغيل البوت
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()

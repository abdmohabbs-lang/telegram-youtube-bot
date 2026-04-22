import os
import yt_dlp
import traceback
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, CallbackQueryHandler


BOT_TOKEN = os.getenv("BOT_TOKEN")
search_cache = {}


# ⚙️ البحث السريع
YDL_SEARCH_OPTS = {
    "quiet": True,
    "default_search": "scsearch3",
    "noplaylist": True,
}


# ⚙️ التحميل
YDL_DOWNLOAD_OPTS = {
    "format": "bestaudio/best",
    "outtmpl": "song.%(ext)s",
    "quiet": True,
    "cookiefile": "cookies.txt",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
}


# 🔎 البحث (بدون تعليق البوت)
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()

    if not text.startswith("يوت"):
        return

    query = text.replace("يوت", "").strip()

    if not query:
        await update.message.reply_text("اكتب اسم الأغنية بعد يوت 🎧")
        return

    # 🔥 رد فوري (مهم جداً لمنع timeout)
    await update.message.reply_text("جاري البحث 🔎...")

    try:
        with yt_dlp.YoutubeDL(YDL_SEARCH_OPTS) as ydl:
            results = ydl.extract_info(query, download=False)

        entries = results.get("entries", [])[:3]

        if not entries:
            await update.message.reply_text("ماكو نتائج 😢")
            return

        search_cache[update.message.chat_id] = entries

        keyboard = [
            [InlineKeyboardButton(e["title"][:40], callback_data=str(i))]
            for i, e in enumerate(entries)
        ]

        await update.message.reply_text(
            "اختر الأغنية 🎧",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        print(traceback.format_exc())
        await update.message.reply_text("خطأ بالبحث ❌")


# 🎧 التحميل بالخلفية (بدون تعليق البوت)
async def download_and_send(query, url, message):
    try:
        with yt_dlp.YoutubeDL(YDL_DOWNLOAD_OPTS) as ydl:
            ydl.download([url])

        if os.path.exists("song.mp3"):
            with open("song.mp3", "rb") as audio:
                await message.reply_audio(audio)

            os.remove("song.mp3")

    except Exception as e:
        print(traceback.format_exc())
        await message.reply_text("فشل التحميل ❌")


# 🎯 اختيار الأغنية
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    index = int(query.data)

    entries = search_cache.get(chat_id)

    if not entries:
        await query.message.reply_text("ابدأ بحث من جديد")
        return

    video = entries[index]

    await query.message.reply_text("جاري التحميل 🎵...")

    # 🔥 تشغيل بالخلفية (مهم جداً لمنع timeout)
    asyncio.create_task(
        download_and_send(video["title"], video["url"], query.message)
    )


# 🚀 تشغيل البوت
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()

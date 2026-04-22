import os
import yt_dlp
import traceback

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, CallbackQueryHandler


BOT_TOKEN = os.getenv("BOT_TOKEN")

search_cache = {}
format_cache = {}


# 🔎 بحث متعدد
SEARCH_OPTS = {
    "quiet": True,
    "noplaylist": True,
    "default_search": "scsearch5/ytsearch5",
}


# 🎧 تحميل حسب الجودة
DOWNLOAD_OPTS = {
    "outtmpl": "song.%(ext)s",
    "quiet": True,
    "noplaylist": True,
    "retries": 3,
    "socket_timeout": 10,
}


FORMATS = {
    "m4a": "bestaudio[ext=m4a]/bestaudio/best",
    "opus": "bestaudio[ext=opus]/bestaudio/best",
    "mp3": "bestaudio/best",
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
        with yt_dlp.YoutubeDL(SEARCH_OPTS) as ydl:
            data = ydl.extract_info(query, download=False)

        entries = data.get("entries", [])[:5]

        if not entries:
            return await msg.edit_text("❌ ماكو نتائج")

        search_cache[update.message.chat_id] = entries

        keyboard = [
            [InlineKeyboardButton(e["title"][:40], callback_data=f"song_{i}")]
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
    data = query.data

    # 🎵 اختيار أغنية
    if data.startswith("song_"):
        index = int(data.split("_")[1])

        entries = search_cache.get(chat_id)
        if not entries:
            return await query.message.reply_text("ابحث مرة ثانية")

        video = entries[index]

        format_cache[chat_id] = video

        keyboard = [
            [InlineKeyboardButton("🎵 M4A (عالي)", callback_data="fmt_m4a")],
            [InlineKeyboardButton("⚡ OPUS (خفيف)", callback_data="fmt_opus")],
            [InlineKeyboardButton("🎧 MP3", callback_data="fmt_mp3")],
        ]

        await query.message.reply_photo(
            photo=video.get("thumbnail"),
            caption=f"🎧 {video.get('title')}\nاختر الجودة:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # 🎚 اختيار الجودة
    elif data.startswith("fmt_"):
        fmt = data.split("_")[1]

        video = format_cache.get(chat_id)
        if not video:
            return await query.message.reply_text("ابدأ من جديد")

        url = video["webpage_url"]
        title = video["title"]

        await query.message.reply_text("⏬ جاري التحميل...")

        try:
            ydl_opts = DOWNLOAD_OPTS.copy()
            ydl_opts["format"] = FORMATS[fmt]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            file_path = "song.mp3"

            # أحياناً يكون m4a أو opus
            for ext in ["mp3", "m4a", "opus", "webm"]:
                if os.path.exists(f"song.{ext}"):
                    file_path = f"song.{ext}"
                    break

            if os.path.exists(file_path):
                await query.message.reply_audio(
                    audio=open(file_path, "rb"),
                    title=title
                )

                os.remove(file_path)

        except Exception:
            print(traceback.format_exc())
            await query.message.reply_text("❌ فشل التحميل")


# 🚀 تشغيل
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()

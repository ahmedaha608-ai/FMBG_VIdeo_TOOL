# KMD PRO FINAL BOT

import os
import sys
import time
import asyncio
import logging
import requests
import yt_dlp
import speedtest

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client(
    "KMD_PRO",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

user_tasks = {}

# =========================
# Progress
# =========================

async def progress_bar(current, total, msg, start, uid):

    if uid in user_tasks and user_tasks[uid]["cancel"]:
        raise Exception("تم الإلغاء")

    now = time.time()
    diff = now - start

    if diff == 0:
        return

    speed = current / diff
    percentage = current * 100 / total
    eta = (total - current) / speed if speed > 0 else 0

    done = int(percentage / 10)
    bar = "█" * done + "░" * (10 - done)

    text = (
        f"📥 {percentage:.1f}%\n"
        f"[{bar}]\n\n"
        f"⚡ {speed / 1024 / 1024:.2f} MB/s\n"
        f"⏳ ETA: {int(eta)} sec"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data=f"cancel_{uid}"
            )
        ]
    ])

    try:
        await msg.edit_text(
            text,
            reply_markup=keyboard
        )
    except:
        pass


# =========================
# Cancel
# =========================

@app.on_callback_query(filters.regex("^cancel_"))
async def cancel_task(client, cq: CallbackQuery):

    uid = int(cq.data.split("_")[1])

    if cq.from_user.id != uid:
        return await cq.answer(
            "هذا التحميل ليس لك",
            show_alert=True
        )

    if uid in user_tasks:
        user_tasks[uid]["cancel"] = True

    await cq.answer("تم إلغاء عمليتك")


# =========================
# START
# =========================

@app.on_message(filters.command("start"))
async def start_cmd(client, m: Message):

    text = """
🔥 KMD Professional Bot

/leechkmd
/ytleechkmd
/VideoReduse
/changethumb
/qbleechkmd
/extractaudio
/screenshot
/Speedtestkmd
/kmdrestart
"""

    await m.reply_text(text)


# =========================
# THUMBNAIL
# =========================

@app.on_message(filters.command("changethumb"))
async def change_thumb(client, m: Message):

    if not m.reply_to_message:
        return await m.reply_text("⚠️ رد على صورة")

    if not m.reply_to_message.photo:
        return await m.reply_text("⚠️ الصورة غير موجودة")

    await m.reply_to_message.download(
        file_name=f"thumb_{m.from_user.id}.jpg"
    )

    await m.reply_text("✅ تم حفظ Thumbnail")


# =========================
# DIRECT LEECH
# =========================

@app.on_message(filters.command("leechkmd"))
async def leech_file(client, m: Message):

    if len(m.command) < 2:
        return await m.reply_text("⚠️ أرسل الرابط")

    uid = m.from_user.id

    user_tasks[uid] = {
        "cancel": False
    }

    url = m.command[1]

    filename = f"{DOWNLOAD_DIR}/{time.time()}"

    msg = await m.reply_text("📥 بدء التحميل...")

    try:

        r = requests.get(url, stream=True)

        total = int(r.headers.get('content-length', 0))

        downloaded = 0
        start = time.time()

        with open(filename, "wb") as f:

            for chunk in r.iter_content(chunk_size=1024 * 512):

                if user_tasks[uid]["cancel"]:
                    raise Exception("تم الإلغاء")

                if chunk:

                    f.write(chunk)

                    downloaded += len(chunk)

                    await progress_bar(
                        downloaded,
                        total,
                        msg,
                        start,
                        uid
                    )

        await msg.edit_text("📤 جاري الرفع...")

        await m.reply_document(
            filename,
            caption="✅ تم الرفع بواسطة KMD PRO"
        )

    except Exception as e:

        await msg.edit_text(f"❌ {e}")

    finally:

        if os.path.exists(filename):
            os.remove(filename)

        user_tasks.pop(uid, None)


# =========================
# YT LEECH
# =========================

@app.on_message(filters.command("ytleechkmd"))
async def yt_leech(client, m: Message):

    if len(m.command) < 2:
        return await m.reply_text("⚠️ أرسل الرابط")

    url = m.command[1]

    msg = await m.reply_text("🔍 جاري استخراج الجودات...")

    try:

        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:

            info = ydl.extract_info(url, download=False)

            formats = info.get('formats', [])

            buttons = []

            added = set()

            for f in formats:

                ext = f.get("ext")

                if ext != "mp4":
                    continue

                height = f.get("height")

                if not height:
                    continue

                if height in added:
                    continue

                added.add(height)

                size = f.get("filesize")

                if size:
                    size_text = f"{round(size / 1024 / 1024)}MB"
                else:
                    size_text = "?"

                text = f"{height}p • {size_text}"

                buttons.append([
                    InlineKeyboardButton(
                        text,
                        callback_data=f"yt_{f['format_id']}_{url}"
                    )
                ])

            await msg.edit_text(
                "🎬 اختر الجودة",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

    except Exception as e:

        await msg.edit_text(f"❌ {e}")


@app.on_callback_query(filters.regex("^yt_"))
async def yt_download(client, cq: CallbackQuery):

    data = cq.data.split("_", 2)

    fid = data[1]
    url = data[2]

    uid = cq.from_user.id

    user_tasks[uid] = {
        "cancel": False
    }

    filename = f"{DOWNLOAD_DIR}/{time.time()}.mp4"

    msg = cq.message

    await msg.edit_text("📥 جاري التحميل...")

    try:

        ydl_opts = {
            'format': fid,
            'outtmpl': filename,
            'quiet': True,
            'merge_output_format': 'mp4'
        }

        loop = asyncio.get_event_loop()

        await loop.run_in_executor(
            None,
            lambda: yt_dlp.YoutubeDL(ydl_opts).download([url])
        )

        await msg.edit_text("📤 جاري الرفع...")

        thumb = f"thumb_{uid}.jpg"

        await cq.message.reply_video(
            filename,
            thumb=thumb if os.path.exists(thumb) else None,
            caption="✅ تم التحميل بواسطة KMD PRO"
        )

    except Exception as e:

        await msg.edit_text(f"❌ {e}")

    finally:

        if os.path.exists(filename):
            os.remove(filename)

        user_tasks.pop(uid, None)


# =========================
# VIDEO REDUSE
# =========================

@app.on_message(filters.command("VideoReduse"))
async def video_reduce(client, m: Message):

    if not m.reply_to_message:
        return await m.reply_text("⚠️ رد على فيديو")

    keyboard = InlineKeyboardMarkup([

        [
            InlineKeyboardButton("144p", callback_data="reduce_144"),
            InlineKeyboardButton("240p", callback_data="reduce_240")
        ],

        [
            InlineKeyboardButton("360p", callback_data="reduce_360"),
            InlineKeyboardButton("480p", callback_data="reduce_480")
        ],

        [
            InlineKeyboardButton("720p", callback_data="reduce_720"),
            InlineKeyboardButton("1080p", callback_data="reduce_1080")
        ]

    ])

    await m.reply_text(
        "🎬 اختر الجودة المطلوبة",
        reply_markup=keyboard
    )


# =========================
# SPEEDTEST
# =========================

@app.on_message(filters.command("Speedtestkmd"))
async def speedtest_cmd(client, m: Message):

    msg = await m.reply_text("🚀 اختبار السرعة...")

    try:

        s = speedtest.Speedtest()

        s.get_best_server()

        d = s.download() / 1024 / 1024
        u = s.upload() / 1024 / 1024
        p = s.results.ping

        text = (
            f"📊 Download: {d:.2f} Mbps\\n"
            f"📤 Upload: {u:.2f} Mbps\\n"
            f"📡 Ping: {p:.0f} ms"
        )

        await msg.edit_text(text)

    except Exception as e:
        await msg.edit_text(f"❌ {e}")


# =========================
# RESTART
# =========================

@app.on_message(filters.command("kmdrestart"))
async def restart_bot(client, m: Message):

    await m.reply_text("♻️ جاري إعادة التشغيل...")

    os.execv(sys.executable, ['python'] + sys.argv)


if __name__ == "__main__":
    app.run()

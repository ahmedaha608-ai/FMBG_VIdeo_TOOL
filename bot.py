import os
import sys
import time
import math
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

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

app = Client(
    "KMD_FINAL",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

yt_links = {}
reduce_tasks = {}

# =========================
# SAFE EDIT
# =========================

async def safe_edit(msg, text):

    try:
        await msg.edit_text(text)
    except:
        pass

# =========================
# ULTRA PROGRESS
# =========================

async def ultra_progress(
    current,
    total,
    msg,
    start,
    filename="video.mp4"
):

    diff = time.time() - start

    if diff == 0:
        return

    percentage = current * 100 / total

    speed = current / diff

    elapsed = round(diff)

    eta = round((total-current)/speed)

    current_mb = current / 1024 / 1024

    total_mb = total / 1024 / 1024

    speed_mb = speed / 1024 / 1024

    filled = math.floor(percentage / 5)

    bar = "█" * filled + "░" * (20-filled)

    text = f"""

╭━━━〔 🚀 KMD UPLOADER 〕━━━╮

📂 NAME:
{filename}

[{bar}]

📊 DONE:
{percentage:.2f}%

⚡ SPEED:
{speed_mb:.2f} MB/s

📦 SIZE:
{current_mb:.2f}/{total_mb:.2f} MB

⏳ LEFT:
{eta} sec

⌛ ELAPSED:
{elapsed} sec

╰━━━━━━━━━━━━━━━━━━━━╯

"""

    try:
        await msg.edit_text(text)
    except:
        pass

# =========================
# START
# =========================

@app.on_message(filters.command("start"))
async def start_cmd(client, m: Message):

    text = """

🔥 KMD FINAL BOT

/leechkmd
/ytleechkmd
/VideoReduse
/Speedtestkmd
/kmdrestart

"""

    await m.reply_text(text)

# =========================
# DIRECT LEECH
# =========================

@app.on_message(filters.command(["leechkmd","Leechkmd"]))
async def leechkmd(client, m: Message):

    if len(m.command) < 2:
        return await m.reply_text("⚠️ أرسل رابط")

    url = m.command[1]

    msg = await m.reply_text("📥 جاري التحميل...")

    try:

        r = requests.get(url, stream=True)

        total = int(r.headers.get("content-length", 0))

        filename = os.path.join(
            DOWNLOAD_DIR,
            f"{int(time.time())}.mp4"
        )

        downloaded = 0

        start = time.time()

        with open(filename, "wb") as f:

            for chunk in r.iter_content(chunk_size=1024*512):

                if chunk:

                    f.write(chunk)

                    downloaded += len(chunk)

                    await ultra_progress(
                        downloaded,
                        total,
                        msg,
                        start,
                        os.path.basename(filename)
                    )

        await safe_edit(msg, "📤 جاري الرفع...")

        await m.reply_video(
            filename,
            supports_streaming=True,
            caption="✅ تم التحميل",
            progress=ultra_progress,
            progress_args=(
                msg,
                time.time(),
                os.path.basename(filename)
            )
        )

        os.remove(filename)

    except Exception as e:

        await safe_edit(msg, f"❌ {e}")

# =========================
# YT LEECH
# =========================

@app.on_message(filters.command(["ytleechkmd","Ytlleechkmd"]))
async def ytleechkmd(client, m: Message):

    if len(m.command) < 2:
        return await m.reply_text("⚠️ أرسل رابط")

    url = m.command[1]

    uid = m.from_user.id

    yt_links[uid] = url

    msg = await m.reply_text("📥 استخراج الجودات...")

    try:

        ydl_opts = {
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

        formats = info.get("formats", [])

        buttons = []

        added = set()

        for f in formats:

            h = f.get("height")

            fid = f.get("format_id")

            if h and fid:

                label = f"{h}p"

                if label not in added:

                    buttons.append([

                        InlineKeyboardButton(
                            label,
                            callback_data=f"yt_{fid}"
                        )

                    ])

                    added.add(label)

        keyboard = InlineKeyboardMarkup(buttons[:10])

        await msg.edit_text(
            "🎬 اختر الجودة",
            reply_markup=keyboard
        )

    except Exception as e:

        await safe_edit(msg, f"❌ {e}")

# =========================
# YT DOWNLOAD
# =========================

@app.on_callback_query(filters.regex("^yt_"))
async def yt_download(client, cq: CallbackQuery):

    uid = cq.from_user.id

    format_id = cq.data.split("_")[1]

    url = yt_links.get(uid)

    if not url:
        return await cq.answer("⚠️ انتهت العملية")

    msg = await cq.message.edit_text("📥 جاري التحميل...")

    outtmpl = os.path.join(
        DOWNLOAD_DIR,
        f"{uid}_%(title)s.%(ext)s"
    )

    ydl_opts = {
        "format": format_id,
        "outtmpl": outtmpl,
        "quiet": True
    }

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(url, download=True)

            file_path = ydl.prepare_filename(info)

        await safe_edit(msg, "📤 جاري الرفع...")

        await cq.message.reply_video(
            file_path,
            supports_streaming=True,
            caption="✅ تم التحميل",
            progress=ultra_progress,
            progress_args=(
                msg,
                time.time(),
                os.path.basename(file_path)
            )
        )

        os.remove(file_path)

    except Exception as e:

        await safe_edit(msg, f"❌ {e}")

# =========================
# VIDEO REDUCE HEVC
# =========================

qualities = {
    "360": "scale=-2:360",
    "480": "scale=-2:480",
    "720": "scale=-2:720"
}

@app.on_message(filters.command(["VideoReduse","videoreduse"]))
async def video_reduce(client, m: Message):

    if not m.reply_to_message:
        return await m.reply_text("⚠️ رد على فيديو")

    uid = m.from_user.id

    reduce_tasks[uid] = m.reply_to_message.id

    keyboard = InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "360p HEVC",
                callback_data="reduce_360"
            )
        ],

        [
            InlineKeyboardButton(
                "480p HEVC",
                callback_data="reduce_480"
            )
        ],

        [
            InlineKeyboardButton(
                "720p HEVC",
                callback_data="reduce_720"
            )
        ]

    ])

    await m.reply_text(
        "🎬 اختر الجودة",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex("^reduce_"))
async def reduce_callback(client, cq: CallbackQuery):

    quality = cq.data.split("_")[1]

    uid = cq.from_user.id

    msg_id = reduce_tasks.get(uid)

    if not msg_id:
        return await cq.answer("⚠️ انتهت العملية")

    video_msg = await client.get_messages(
        cq.message.chat.id,
        msg_id
    )

    msg = await cq.message.edit_text(
        f"📥 ضغط الفيديو HEVC {quality}p..."
    )

    input_file = await video_msg.download(
        file_name=f"{DOWNLOAD_DIR}/{uid}_input.mp4"
    )

    output_file = (
        f"{DOWNLOAD_DIR}/{uid}_{quality}_hevc.mp4"
    )

    thumb_file = (
        f"{DOWNLOAD_DIR}/{uid}_thumb.jpg"
    )

    scale = qualities[quality]

    cmd = [

        "ffmpeg",

        "-threads", "1",

        "-i", input_file,

        "-vf", f"{scale},thumbnail",

        "-c:v", "libx265",

        "-preset", "ultrafast",

        "-crf", "32",

        "-tag:v", "hvc1",

        "-pix_fmt", "yuv420p",

        "-movflags", "+faststart",

        "-c:a", "aac",

        "-b:a", "96k",

        "-max_muxing_queue_size", "9999",

        output_file,

        "-y"

    ]

    process = await asyncio.create_subprocess_exec(*cmd)

    await process.wait()

    thumb_cmd = [

        "ffmpeg",

        "-i", output_file,

        "-ss", "00:00:03",

        "-vframes", "1",

        thumb_file,

        "-y"

    ]

    thumb_process = await asyncio.create_subprocess_exec(
        *thumb_cmd
    )

    await thumb_process.wait()

    await msg.edit_text("📤 جاري الرفع...")

    await cq.message.reply_video(

        output_file,

        thumb=thumb_file,

        supports_streaming=True,

        width=1280,

        height=720,

        duration=video_msg.video.duration,

        caption=f"✅ HEVC x265 {quality}p",

        progress=ultra_progress,

        progress_args=(

            msg,

            time.time(),

            os.path.basename(output_file)

        )

    )

    try:

        os.remove(input_file)
        os.remove(output_file)
        os.remove(thumb_file)

    except:
        pass

# =========================
# SPEEDTEST
# =========================

@app.on_message(filters.command("Speedtestkmd"))
async def speedtest_cmd(client, m: Message):

    msg = await m.reply_text("🚀 اختبار السرعة...")

    try:

        s = speedtest.Speedtest(secure=True)

        s.get_best_server()

        d = s.download() / 1024 / 1024
        u = s.upload() / 1024 / 1024

        await msg.edit_text(
            f"📥 Download: {d:.2f} Mbps\n"
            f"📤 Upload: {u:.2f} Mbps"
        )

    except Exception as e:

        await msg.edit_text(f"❌ {e}")

# =========================
# RESTART
# =========================

@app.on_message(filters.command("kmdrestart"))
async def restart_bot(client, m: Message):

    await m.reply_text("♻️ إعادة التشغيل...")

    await asyncio.sleep(2)

    os.execl(
        sys.executable,
        sys.executable,
        *sys.argv
    )

app.run()

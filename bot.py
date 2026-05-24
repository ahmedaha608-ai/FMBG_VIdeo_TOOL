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
logging.getLogger("pyrogram").setLevel(logging.ERROR)

app = Client(
    "KMD_PRO",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

user_tasks = {}
yt_links = {}
reduce_tasks = {}
last_edit = {}

async def safe_edit(msg, text):

    try:
        await msg.edit_text(text)
    except:
        pass

async def progress_bar(current, total, msg, start):

    diff = time.time() - start

    if diff == 0:
        return

    percentage = current * 100 / total

    speed = current / diff

    filled = math.floor(percentage / 5)

    bar = "█" * filled + "░" * (20-filled)

    current_mb = current / 1024 / 1024
    total_mb = total / 1024 / 1024

    speed_mb = speed / 1024 / 1024

    text = f"""

🚀 KMD PROGRESS

[{bar}]

📊 {percentage:.2f}%

⚡ {speed_mb:.2f} MB/s

📦 {current_mb:.2f}/{total_mb:.2f} MB

"""

    try:
        await msg.edit_text(text)
    except:
        pass

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

                    await progress_bar(
                        downloaded,
                        total,
                        msg,
                        start
                    )

        await msg.edit_text("📤 جاري الرفع...")

        await m.reply_video(
            filename,
            supports_streaming=True,
            caption="✅ تم التحميل"
        )

        os.remove(filename)

    except Exception as e:

        await msg.edit_text(f"❌ {e}")

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
            caption="✅ تم التحميل"
        )

        os.remove(file_path)

    except Exception as e:

        await safe_edit(msg, f"❌ {e}")

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

    scale = qualities[quality]

    cmd = [

        "ffmpeg",

        "-threads", "1",

        "-i", input_file,

        "-vf", scale,

        "-c:v", "libx265",

        "-preset", "ultrafast",

        "-crf", "32",

        "-tag:v", "hvc1",

        "-pix_fmt", "yuv420p",

        "-c:a", "aac",

        "-b:a", "96k",

        "-movflags", "+faststart",

        output_file,

        "-y"

    ]

    process = await asyncio.create_subprocess_exec(*cmd)

    await process.wait()

    await msg.edit_text("📤 جاري الرفع...")

    await cq.message.reply_video(
        output_file,
        supports_streaming=True,
        caption=f"✅ HEVC x265 {quality}p"
    )

    try:
        os.remove(input_file)
        os.remove(output_file)
    except:
        pass

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

@app.on_message(filters.command("kmdrestart"))
async def restart_bot(client, m: Message):

    await m.reply_text("♻️ إعادة التشغيل...")

    await asyncio.sleep(2)

    os.execl(
        sys.executable,
        sys.executable,
        *sys.argv
    )








=========================

ULTRA PROGRESS BAR

=========================

async def ultra_progress(
current,
total,
msg,
start,
filename="video.mp4"
):

now = time.time()

diff = now - start

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
{current_mb:.2f} MB
/
{total_mb:.2f} MB

⏳ LEFT:
{eta} sec

⌛ ELAPSED:
{elapsed} sec

╰━━━━━━━━━━━━━━━━━━━━╯

"""

keyboard = InlineKeyboardMarkup([

    [

        InlineKeyboardButton(
            "❌ CANCEL",
            callback_data="cancel_task"
        ),

        InlineKeyboardButton(
            "🔄 REFRESH",
            callback_data="refresh_task"
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

=========================

CANCEL BUTTON

=========================

cancel_tasks = {}

@app.on_callback_query(
filters.regex("^cancel_task")
)
async def cancel_upload(client, cq: CallbackQuery):

uid = cq.from_user.id

cancel_tasks[uid] = True

await cq.answer(
    "❌ تم إلغاء العملية",
    show_alert=True
)

=========================

REFRESH BUTTON

=========================

@app.on_callback_query(
filters.regex("^refresh_task")
)
async def refresh_upload(client, cq: CallbackQuery):

await cq.answer(
    "🔄 تم التحديث",
    show_alert=False
)

=========================

DOWNLOAD WITH PROGRESS

=========================

msg = await m.reply_text(
"📥 بدء التحميل..."
)

start = time.time()

filename = os.path.basename(
file_path
)

with open(filename, "wb") as f:

for chunk in r.iter_content(
    chunk_size=1024*512
):

    if cancel_tasks.get(
        m.from_user.id
    ):

        raise Exception(
            "❌ تم الإلغاء"
        )

    if chunk:

        f.write(chunk)

        downloaded += len(chunk)

        await ultra_progress(

            downloaded,

            total,

            msg,

            start,

            filename

        )

=========================

TELEGRAM UPLOAD PROGRESS

=========================

await m.reply_video(

file_path,

supports_streaming=True,

caption="✅ تم الرفع",

progress=ultra_progress,

progress_args=(

    msg,

    time.time(),

    os.path.basename(file_path)

)

)

=========================

DOCUMENT UPLOAD

=========================

await m.reply_document(

file_path,

caption="✅ تم الرفع",

progress=ultra_progress,

progress_args=(

    msg,

    time.time(),

    os.path.basename(file_path)

)

)
app.run()

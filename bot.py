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
send_modes = {}

# =========================
# ULTRA PROGRESS
# =========================

async def ultra_progress(
    current,
    total,
    msg,
    start,
    uid,
    filename="video.mp4"
):

    if uid in user_tasks:

        if user_tasks[uid]["cancel"]:
            raise Exception("❌ تم إلغاء العملية")

    now = time.time()
    diff = now - start

    if diff == 0:
        return

    percentage = current * 100 / total
    speed = current / diff

    eta = (
        (total - current) / speed
        if speed > 0 else 0
    )

    done = int(percentage / 5)

    bar = (
        "█" * done +
        "░" * (20 - done)
    )

    current_mb = current / 1024 / 1024
    total_mb = total / 1024 / 1024
    remaining_mb = total_mb - current_mb
    speed_mb = speed / 1024 / 1024

    elapsed = int(diff)

    mins = elapsed // 60
    secs = elapsed % 60

    eta_mins = int(eta) // 60
    eta_secs = int(eta) % 60

    text = f"""
╭──────────────────────────────╮
│       🚀 KMD PROGRESS        │
├──────────────────────────────┤

📄 الملف:
{filename[:45]}

📊 شريط التقدم:

[{bar}]

✅ النسبة:
{percentage:.2f}%

📦 الحجم الأصلي:
{total_mb:.2f} MB

📥 تم التحميل:
{current_mb:.2f} MB

📉 المتبقي:
{remaining_mb:.2f} MB

⚡ سرعة التحميل:
{speed_mb:.2f} MB/s

⏱ الوقت المنقضي:
{mins}m {secs}s

⌛ الوقت المتبقي:
{eta_mins}m {eta_secs}s

👤 المستخدم:
{uid}

╰──────────────────────────────╯
"""

    keyboard = InlineKeyboardMarkup([

        [

            InlineKeyboardButton(
                "🔄 Refresh",
                callback_data=f"refresh_{uid}"
            ),

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
# SEND TYPE SELECTOR
# =========================

async def send_type_selector(msg, action):

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎬 رفع كفيديو",
                callback_data=f"sendvideo_{action}"
            ),

            InlineKeyboardButton(
                "📁 رفع كمستند",
                callback_data=f"senddoc_{action}"
            )
        ]
    ])

    await msg.reply_text(
        "📤 اختر طريقة تنزيل الملف",
        reply_markup=keyboard
    )

# =========================
# SAVE SEND TYPE
# =========================

@app.on_callback_query(
    filters.regex("^sendvideo_|^senddoc_")
)
async def save_send_type(
    client,
    cq: CallbackQuery
):

    uid = cq.from_user.id

    data = cq.data

    if data.startswith("sendvideo_"):

        mode = "video"

    else:

        mode = "document"

    send_modes[uid] = {

        "mode": mode

    }

    await cq.answer(
        f"✅ تم اختيار {mode}"
    )

# =========================
# CANCEL BUTTON
# =========================

@app.on_callback_query(filters.regex("^cancel_"))
async def cancel_task(client, cq: CallbackQuery):

    uid = int(cq.data.split("_")[1])

    if cq.from_user.id != uid:

        return await cq.answer(
            "⚠️ هذا التحميل ليس لك",
            show_alert=True
        )

    if uid in user_tasks:

        user_tasks[uid]["cancel"] = True

    await cq.answer(
        "❌ تم إلغاء عمليتك"
    )

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
/videotool
/enhance
/splitvideo
/watermark
/intro
/addsub
/changethumb
/Speedtestkmd
/kmdrestart
/qbleechkmd
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
# VIDEO TOOL MENU
# =========================

@app.on_message(filters.command("videotool"))
async def video_tool(client, m: Message):

    keyboard = InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🎨 تغيير الخلفية",
                callback_data="tool_bg"
            )
        ],

        [
            InlineKeyboardButton(
                "✨ تحسين الجودة",
                callback_data="tool_enhance"
            )
        ],

        [
            InlineKeyboardButton(
                "✂️ تقسيم 3GB",
                callback_data="tool_split"
            )
        ],

        [
            InlineKeyboardButton(
                "📝 إضافة ترجمة",
                callback_data="tool_sub"
            )
        ],

        [
            InlineKeyboardButton(
                "💧 علامة مائية",
                callback_data="tool_watermark"
            )
        ],

        [
            InlineKeyboardButton(
                "🎬 إضافة انترو",
                callback_data="tool_intro"
            )
        ]

    ])

    await m.reply_text(
        "🛠 KMD VIDEO TOOL",
        reply_markup=keyboard
    )

# =========================
# VIDEO REDUSE
# =========================

@app.on_message(filters.command("VideoReduse"))
async def video_reduce(client, m: Message):

    if not m.reply_to_message:
        return await m.reply_text("⚠️ رد على فيديو")

    keyboard = InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "144p",
                callback_data="reduce_144"
            ),
            InlineKeyboardButton(
                "240p",
                callback_data="reduce_240"
            )
        ],

        [
            InlineKeyboardButton(
                "360p",
                callback_data="reduce_360"
            ),
            InlineKeyboardButton(
                "480p",
                callback_data="reduce_480"
            )
        ],

        [
            InlineKeyboardButton(
                "720p",
                callback_data="reduce_720"
            ),
            InlineKeyboardButton(
                "1080p",
                callback_data="reduce_1080"
            )
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
            f"📊 Download: {d:.2f} Mbps\n"
            f"📤 Upload: {u:.2f} Mbps\n"
            f"📡 Ping: {p:.0f} ms"
        )

        await msg.edit_text(text)

    except Exception as e:
        await msg.edit_text(f"❌ {e}")
FFMPEG_PRESET = "ultrafast"
FFMPEG_CRF = "30"

=========================

SAFE ENHANCE VIDEO

=========================

@app.on_message(filters.command("enhance"))
async def enhance_video(client, m: Message):

if not m.reply_to_message:
    return await m.reply_text(
        "⚠️ رد على فيديو"
    )

uid = m.from_user.id

msg = await m.reply_text(
    "✨ تحسين الجودة..."
)

input_file = await m.reply_to_message.download(
    file_name=f"{DOWNLOAD_DIR}/enhance_input.mp4"
)

output_file = f"{DOWNLOAD_DIR}/enhanced.mp4"

start = time.time()

user_tasks[uid] = {
    "cancel": False
}

cmd = [

    "ffmpeg",

    "-threads", "1",

    "-i", input_file,

    "-vf",
    "scale=-2:720",

    "-c:v", "libx264",

    "-preset", FFMPEG_PRESET,

    "-crf", FFMPEG_CRF,

    "-c:a", "aac",

    "-b:a", "128k",

    output_file,

    "-y"

]

process = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE
)

while True:

    if user_tasks[uid]["cancel"]:

        process.kill()

        return await msg.edit_text(
            "❌ تم الإلغاء"
        )

    if process.returncode is not None:
        break

    await asyncio.sleep(2)

await process.communicate()

await msg.edit_text(
    "📤 جاري الرفع..."
)

mode = send_modes.get(
    uid,
    {}
).get(
    "mode",
    "video"
)

thumb = f"thumb_{uid}.jpg"

if mode == "video":

    await m.reply_video(

        output_file,

        thumb=thumb if os.path.exists(thumb) else None,

        caption="✨ تم تحسين الجودة"

    )

else:

    await m.reply_document(

        output_file,

        thumb=thumb if os.path.exists(thumb) else None,

        caption="✨ تم تحسين الجودة"

    )

try:

    if os.path.exists(input_file):
        os.remove(input_file)

    if os.path.exists(output_file):
        os.remove(output_file)

except:
    pass

user_tasks.pop(uid, None)

=========================

SAFE VIDEO REDUSE

=========================

@app.on_callback_query(filters.regex("^reduce_"))
async def reduce_callback(client, cq: CallbackQuery):

quality = cq.data.split("_")[1]

uid = cq.from_user.id

user_tasks[uid] = {
    "cancel": False
}

msg = cq.message

await msg.edit_text(
    f"📥 جاري الضغط {quality}p..."
)

input_file = await cq.message.reply_to_message.download(
    file_name=f"{DOWNLOAD_DIR}/input_{uid}.mp4"
)

output_file = f"{DOWNLOAD_DIR}/reduced_{quality}_{uid}.mp4"

scale = f"scale=-2:{quality}"

cmd = [

    "ffmpeg",

    "-threads", "1",

    "-i", input_file,

    "-vf", scale,

    "-c:v", "libx264",

    "-preset", FFMPEG_PRESET,

    "-crf", FFMPEG_CRF,

    "-c:a", "aac",

    "-b:a", "128k",

    output_file,

    "-y"

]

process = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE
)

while True:

    if user_tasks[uid]["cancel"]:

        process.kill()

        return await msg.edit_text(
            "❌ تم الإلغاء"
        )

    if process.returncode is not None:
        break

    await asyncio.sleep(2)

await process.communicate()

await msg.edit_text(
    "📤 جاري الرفع..."
)

mode = send_modes.get(
    uid,
    {}
).get(
    "mode",
    "video"
)

thumb = f"thumb_{uid}.jpg"

if mode == "video":

    await cq.message.reply_video(

        output_file,

        thumb=thumb if os.path.exists(thumb) else None,

        caption=f"✅ الجودة النهائية {quality}p"

    )

else:

    await cq.message.reply_document(

        output_file,

        thumb=thumb if os.path.exists(thumb) else None,

        caption=f"✅ الجودة النهائية {quality}p"

    )

try:

    if os.path.exists(input_file):
        os.remove(input_file)

    if os.path.exists(output_file):
        os.remove(output_file)

except:
    pass

user_tasks.pop(uid, None)






# =========================
# RESTART
# =========================

@app.on_message(filters.command("kmdrestart"))
async def restart_bot(client, m: Message):

    await m.reply_text("♻️ جاري إعادة التشغيل...")

    os.execv(sys.executable, ['python'] + sys.argv)

# =========================
# RUN BOT
# =========================

if __name__ == "__main__":
    app.run()

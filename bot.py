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
=========================

KMD ULTRA PROGRESS BAR

=========================

async def ultra_progress(
current,
total,
msg,
start,
uid,
filename="video.mp4"
):

# =========================
# CANCEL CHECK
# =========================

if uid in user_tasks:

    if user_tasks[uid]["cancel"]:

        raise Exception("❌ تم إلغاء العملية")

# =========================
# TIME
# =========================

now = time.time()

diff = now - start

if diff == 0:
    return

# =========================
# SPEED + ETA
# =========================

percentage = current * 100 / total

speed = current / diff

eta = (
    (total - current) / speed
    if speed > 0 else 0
)

# =========================
# BAR STYLE
# =========================

done = int(percentage / 5)

bar = (
    "█" * done +
    "░" * (20 - done)
)

# =========================
# SIZE
# =========================

current_mb = current / 1024 / 1024

total_mb = total / 1024 / 1024

remaining_mb = total_mb - current_mb

speed_mb = speed / 1024 / 1024

# =========================
# TIME FORMAT
# =========================

elapsed = int(diff)

mins = elapsed // 60
secs = elapsed % 60

eta_mins = int(eta) // 60
eta_secs = int(eta) % 60

# =========================
# MESSAGE STYLE 19:16
# =========================

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

# =========================
# BUTTONS
# =========================

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

# =========================
# UPDATE MESSAGE
# =========================

try:

    await msg.edit_text(

        text,

        reply_markup=keyboard

    )

except:
    pass

=========================

REFRESH BUTTON

=========================

@app.on_callback_query(filters.regex("^refresh_"))
async def refresh_task(client, cq: CallbackQuery):

uid = int(
    cq.data.split("_")[1]
)

if cq.from_user.id != uid:

    return await cq.answer(

        "⚠️ هذا التحميل ليس لك",

        show_alert=True

    )

await cq.answer(

    "🔄 تم تحديث البيانات",

    show_alert=False

)

=========================

CANCEL BUTTON

=========================

@app.on_callback_query(filters.regex("^cancel_"))
async def cancel_task(client, cq: CallbackQuery):

uid = int(
    cq.data.split("_")[1]
)

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

=========================

EXAMPLE USE

=========================

داخل أي تحميل استخدم:

"""
await ultra_progress(

downloaded,
total,
msg,
start,
uid,
os.path.basename(filename)

)
"""


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
=========================

FINISH NOTIFY

=========================

async def finish_notify(
client,
user_id,
operation,
filename=""
):

text = f"""

✅ انتهت العملية بنجاح

📌 العملية:
{operation}

📄 الملف:
{filename}
"""

try:

    # DM MESSAGE
    await client.send_message(
        user_id,
        text
    )

except:

    pass

=========================

GROUP MENTION

=========================

async def group_mention(
msg,
user_id,
operation
):

mention = f"[اضغط هنا](tg://user?id={user_id})"

text = f"""

✅ {mention}

انتهت العملية:
{operation}
"""

await msg.reply_text(
    text,
    disable_web_page_preview=True
    )






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
=========================

send_modes = {}

=========================

VIDEO TOOL MENU

=========================

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

=========================

SEND TYPE SELECTOR

=========================

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

=========================

SAVE SEND TYPE

=========================

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

    action = data.replace(
        "sendvideo_",
        ""
    )

else:

    mode = "document"

    action = data.replace(
        "senddoc_",
        ""
    )

send_modes[uid] = {

    "mode": mode,
    "action": action

}

await cq.answer(
    f"✅ تم اختيار {mode}"
)

=========================

ENHANCE VIDEO

=========================

@app.on_callback_query(filters.regex("^tool_enhance"))
async def tool_enhance(client, cq: CallbackQuery):

await cq.message.reply_text(
    "✨ رد على الفيديو ثم أرسل:\n/enhance"
)

@app.on_message(filters.command("enhance"))
async def enhance_video(client, m: Message):

if not m.reply_to_message:
    return await m.reply_text(
        "⚠️ رد على فيديو"
    )

uid = m.from_user.id

await send_type_selector(
    m,
    "enhance"
)

msg = await m.reply_text(
    "✨ تحسين الجودة..."
)

input_file = await m.reply_to_message.download(
    file_name=f"{DOWNLOAD_DIR}/enhance_input.mp4"
)

output_file = f"{DOWNLOAD_DIR}/enhanced.mp4"

cmd = [

    "ffmpeg",
    "-i", input_file,

    "-vf",
    "scale=1920:1080:flags=lanczos,eq=contrast=1.1:brightness=0.02:saturation=1.2",

    "-c:v", "libx265",
    "-preset", "medium",
    "-crf", "24",

    "-c:a", "aac",
    "-b:a", "192k",

    output_file,
    "-y"
]

process = await asyncio.create_subprocess_exec(
    *cmd
)

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

=========================

WATERMARK

=========================

@app.on_callback_query(filters.regex("^tool_watermark"))
async def tool_watermark(client, cq: CallbackQuery):

await cq.message.reply_text(
    "💧 رد على فيديو واكتب:\n/watermark نص"
)

@app.on_message(filters.command("watermark"))
async def watermark_video(client, m: Message):

if not m.reply_to_message:
    return await m.reply_text(
        "⚠️ رد على فيديو"
    )

uid = m.from_user.id

await send_type_selector(
    m,
    "watermark"
)

if len(m.command) < 2:
    return await m.reply_text(
        "⚠️ أكتب النص"
    )

text = " ".join(m.command[1:])

msg = await m.reply_text(
    "💧 إضافة العلامة المائية..."
)

input_file = await m.reply_to_message.download(
    file_name=f"{DOWNLOAD_DIR}/watermark.mp4"
)

output_file = f"{DOWNLOAD_DIR}/watermarked.mp4"

draw = (
    f"drawtext=text='{text}':"
    f"x=w-tw-20:y=h-th-20:"
    f"fontsize=32:fontcolor=white:"
    f"box=1:boxcolor=black@0.5"
)

cmd = [

    "ffmpeg",
    "-i", input_file,

    "-vf", draw,

    "-c:v", "libx265",
    "-preset", "medium",
    "-crf", "26",

    output_file,
    "-y"
]

process = await asyncio.create_subprocess_exec(
    *cmd
)

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

        caption="💧 تمت إضافة العلامة المائية"

    )

else:

    await m.reply_document(

        output_file,

        thumb=thumb if os.path.exists(thumb) else None,

        caption="💧 تمت إضافة العلامة المائية"

    )
# =========================
# SCALE
# =========================

scale = f"scale=-2:{quality}"

# =========================
# FFMPEG PROFESSIONAL
# =========================

cmd = [

    "ffmpeg",

    "-i", input_file,

    # SCALE
    "-vf", scale,

    # HEVC
    "-c:v", "libx265",

    # أقصى ضغط
    "-preset", "slow",

    # جودة احترافية
    "-crf", "30",

    # 10BIT
    "-pix_fmt", "yuv420p10le",

    # تحسين الضغط
    "-x265-params",
    "aq-mode=3:aq-strength=1.0:deblock=-1,-1:me=3:subme=4:rd=4",

    # AUDIO
    "-c:a", "aac",
    "-b:a", "64k",

    # FASTSTART
    "-movflags", "+faststart",

    output_file,

    "-y"
]

await msg.edit_text(
    f"🔄 ضغط الفيديو HEVC x265 {quality}p..."
)

process = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE
)

await process.communicate()

if user_tasks[uid]["cancel"]:

    if os.path.exists(output_file):
        os.remove(output_file)

    return await msg.edit_text("❌ تم الإلغاء")

await msg.edit_text("📤 جاري الرفع...")

thumb = f"thumb_{uid}.jpg"

await cq.message.reply_video(
    output_file,
    thumb=thumb if os.path.exists(thumb) else None,
    caption=(
        f"✅ تم الضغط HEVC x265\n"
        f"🎬 الجودة: {quality}p"
    )
)

# CLEAN
for f in [input_file, output_file]:

    if os.path.exists(f):
        os.remove(f)

user_tasks.pop(uid, None)


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


=========================

VIDEO TOOL MENU

=========================

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

=========================

CHANGE BACKGROUND

=========================

@app.on_callback_query(filters.regex("^tool_bg"))
async def tool_bg(client, cq: CallbackQuery):

await cq.message.reply_text(
    "🎨 أرسل الفيديو + الخلفية الجديدة"
)

=========================

ENHANCE VIDEO QUALITY

=========================

@app.on_callback_query(filters.regex("^tool_enhance"))
async def tool_enhance(client, cq: CallbackQuery):

await cq.message.reply_text(
    "✨ رد على الفيديو للتحسين"
)

@app.on_message(filters.command("enhance"))
async def enhance_video(client, m: Message):

if not m.reply_to_message:
    return await m.reply_text("⚠️ رد على فيديو")

msg = await m.reply_text("✨ تحسين الجودة...")

input_file = await m.reply_to_message.download(
    file_name=f"{DOWNLOAD_DIR}/enhance_input.mp4"
)

output_file = f"{DOWNLOAD_DIR}/enhanced.mp4"

cmd = [

    "ffmpeg",
    "-i", input_file,

    "-vf",
    "scale=1920:1080:flags=lanczos,eq=contrast=1.1:brightness=0.02:saturation=1.2",

    "-c:v", "libx265",
    "-preset", "medium",
    "-crf", "24",

    "-c:a", "aac",
    "-b:a", "192k",

    output_file,
    "-y"
]

process = await asyncio.create_subprocess_exec(
    *cmd
)

await process.communicate()

await msg.edit_text("📤 جاري الرفع...")

await m.reply_video(
    output_file,
    caption="✨ تم تحسين الجودة"
)

=========================

SPLIT VIDEO 3GB

=========================

@app.on_callback_query(filters.regex("^tool_split"))
async def tool_split(client, cq: CallbackQuery):

await cq.message.reply_text(
    "✂️ رد على الفيديو ثم أرسل:\n/splitvideo"
)

@app.on_message(filters.command("splitvideo"))
async def split_video(client, m: Message):

if not m.reply_to_message:
    return await m.reply_text("⚠️ رد على فيديو")

msg = await m.reply_text("✂️ تقسيم الفيديو...")

input_file = await m.reply_to_message.download(
    file_name=f"{DOWNLOAD_DIR}/split_input.mp4"
)

output_pattern = f"{DOWNLOAD_DIR}/part_%03d.mp4"

cmd = [

    "ffmpeg",
    "-i", input_file,

    "-c", "copy",

    "-map", "0",

    "-segment_time", "3600",

    "-f", "segment",

    "-reset_timestamps", "1",

    output_pattern,
    "-y"
]

process = await asyncio.create_subprocess_exec(
    *cmd
)

await process.communicate()

await msg.edit_text("✅ تم التقسيم")

=========================

ADD SUBTITLE

=========================

@app.on_callback_query(filters.regex("^tool_sub"))
async def tool_sub(client, cq: CallbackQuery):

await cq.message.reply_text(
    "📝 أرسل الفيديو + ملف SRT"
)

@app.on_message(filters.command("addsub"))
async def add_subtitle(client, m: Message):

await m.reply_text(
    "📝 رد على الفيديو وملف الترجمة"
)

=========================

WATERMARK

=========================

@app.on_callback_query(filters.regex("^tool_watermark"))
async def tool_watermark(client, cq: CallbackQuery):

await cq.message.reply_text(
    "💧 رد على فيديو واكتب:\n/watermark نص"
)

@app.on_message(filters.command("watermark"))
async def watermark_video(client, m: Message):

if not m.reply_to_message:
    return await m.reply_text("⚠️ رد على فيديو")

if len(m.command) < 2:
    return await m.reply_text("⚠️ أكتب النص")

text = " ".join(m.command[1:])

msg = await m.reply_text("💧 إضافة العلامة المائية...")

input_file = await m.reply_to_message.download(
    file_name=f"{DOWNLOAD_DIR}/watermark.mp4"
)

output_file = f"{DOWNLOAD_DIR}/watermarked.mp4"

draw = (
    f"drawtext=text='{text}':"
    f"x=w-tw-20:y=h-th-20:"
    f"fontsize=32:fontcolor=white:"
    f"box=1:boxcolor=black@0.5"
)

cmd = [

    "ffmpeg",
    "-i", input_file,

    "-vf", draw,

    "-c:v", "libx265",
    "-preset", "medium",
    "-crf", "26",

    output_file,
    "-y"
]

process = await asyncio.create_subprocess_exec(
    *cmd
)

await process.communicate()

await msg.edit_text("📤 جاري الرفع...")

await m.reply_video(
    output_file,
    caption="💧 تمت إضافة العلامة المائية"
)

=========================

INTRO VIDEO

=========================

@app.on_callback_query(filters.regex("^tool_intro"))
async def tool_intro(client, cq: CallbackQuery):

await cq.message.reply_text(
    "🎬 رد على الفيديو ثم:\n/intro اسم_الجروب"
)

@app.on_message(filters.command("intro"))
async def add_intro(client, m: Message):

if not m.reply_to_message:
    return await m.reply_text("⚠️ رد على فيديو")

if len(m.command) < 2:
    return await m.reply_text("⚠️ أرسل اسم الجروب")

group_name = " ".join(m.command[1:])

msg = await m.reply_text("🎬 إنشاء الانترو...")

input_file = await m.reply_to_message.download(
    file_name=f"{DOWNLOAD_DIR}/intro_input.mp4"
)

intro_file = f"{DOWNLOAD_DIR}/intro.mp4"

output_file = f"{DOWNLOAD_DIR}/final_intro.mp4"

cmd_intro = [

    "ffmpeg",

    "-f", "lavfi",

    "-i",
    "color=c=black:s=1280x720:d=5",

    "-vf",
    f"drawtext=text='{group_name}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2",

    intro_file,
    "-y"
]

process = await asyncio.create_subprocess_exec(
    *cmd_intro
)

await process.communicate()

concat_txt = f"{DOWNLOAD_DIR}/concat.txt"

with open(concat_txt, "w", encoding="utf-8") as f:

    f.write(f"file '{intro_file}'\\n")
    f.write(f"file '{input_file}'\\n")

cmd_concat = [

    "ffmpeg",

    "-f", "concat",

    "-safe", "0",

    "-i", concat_txt,

    "-c", "copy",

    output_file,
    "-y"
]

process2 = await asyncio.create_subprocess_exec(
    *cmd_concat
)

await process2.communicate()

await msg.edit_text("📤 جاري الرفع...")

await m.reply_video(
    output_file,
    caption="🎬 تم إضافة الانترو"
)


# =========================
# RESTART
# =========================

@app.on_message(filters.command("kmdrestart"))
async def restart_bot(client, m: Message):

    await m.reply_text("♻️ جاري إعادة التشغيل...")

    os.execv(sys.executable, ['python'] + sys.argv)


if __name__ == "__main__":
    app.run()

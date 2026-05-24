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

import asyncio
import os
import time
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
last_edit_time = {}  # المتغير الجديد لتفادي Flood Wait

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
        if user_tasks[uid].get("cancel"):
            raise Exception("❌ تم إلغاء العملية")

    now = time.time()
    
    # التأكد من وجود المفتاح في القاموس
    if uid not in last_edit_time:
        last_edit_time[uid] = 0
    
    # شرط التحديث كل 5 ثوانٍ فقط لتجنب Flood Wait
    if now - last_edit_time[uid] > 5:
        diff = now - start
        if diff == 0: return
        
        percentage = current * 100 / total
        speed = current / diff
        
        # ... (باقي كود الحساب) ...
        # ملاحظة: تم ترك مساحة للكود الخاص بك، تأكد من إكمال بناء 'text' هنا
        
        try:
            # هنا يتم تحديث الرسالة
            # await msg.edit_text(text) 
            last_edit_time[uid] = now
        except Exception:
            pass



=========================

SAVE VIDEO MESSAGE

=========================

reduce_tasks = {}

@app.on_message(filters.command("VideoReduse"))
async def video_reduce(client, m: Message):

if not m.reply_to_message:
    return await m.reply_text(
        "⚠️ رد على فيديو"
    )

uid = m.from_user.id

reduce_tasks[uid] = m.reply_to_message.id

keyboard = InlineKeyboardMarkup([

    [
        InlineKeyboardButton(
            "240p",
            callback_data="reduce_240"
        ),

        InlineKeyboardButton(
            "360p",
            callback_data="reduce_360"
        )
    ],

    [
        InlineKeyboardButton(
            "480p",
            callback_data="reduce_480"
        ),

        InlineKeyboardButton(
            "720p",
            callback_data="reduce_720"
        )
    ]

])

await m.reply_text(
    "🎬 اختر الجودة",
    reply_markup=keyboard
)

=========================

REDUCE CALLBACK

=========================

@app.on_callback_query(filters.regex("^reduce_"))
async def reduce_callback(client, cq: CallbackQuery):

quality = cq.data.split("_")[1]

uid = cq.from_user.id

if uid not in reduce_tasks:

    return await cq.answer(
        "⚠️ انتهت العملية",
        show_alert=True
    )

msg_id = reduce_tasks[uid]

video_msg = await client.get_messages(
    cq.message.chat.id,
    msg_id
)

msg = await cq.message.edit_text(
    f"📥 ضغط الفيديو {quality}p..."
)

input_file = await video_msg.download(
    file_name=f"{DOWNLOAD_DIR}/{uid}_input.mp4"
)

output_file = (
    f"{DOWNLOAD_DIR}/{uid}_{quality}.mp4"
)

scale = f"scale=-2:{quality}"

cmd = [

    "ffmpeg",

    "-threads", "1",

    "-i", input_file,

    "-vf", scale,

    "-c:v", "libx264",

    "-preset", "ultrafast",

    "-crf", "30",

    "-c:a", "aac",

    "-b:a", "128k",

    output_file,

    "-y"

]

process = await asyncio.create_subprocess_exec(
    *cmd
)

await process.wait()

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

        caption=f"✅ الجودة {quality}p"

    )

else:

    await cq.message.reply_document(

        output_file,

        thumb=thumb if os.path.exists(thumb) else None,

        caption=f"✅ الجودة {quality}p"

    )

try:

    os.remove(input_file)
    os.remove(output_file)

except:
    pass

reduce_tasks.pop(uid, None)





import os
import sys
import asyncio
import uuid
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv

# إعدادات البوت
load_dotenv()
app = Client("Eng_Bot", api_id=int(os.getenv("API_ID")), api_hash=os.getenv("API_HASH"), bot_token=os.getenv("BOT_TOKEN"))

active_tasks = {}

# --- [1. دالة العرض الاحترافي (شكل لوحة التحكم)] ---
def progress_hook(d, message: Message, task_id: str):
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%').replace(' ', '')
        speed = d.get('_speed_str', 'N/A')
        total = d.get('_total_bytes_str', 'N/A')
        done = d.get('_downloaded_bytes_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')
        
        filled = int(float(p.replace('%', '')) / 5)
        bar = "▓" * filled + "░" * (20 - filled)
        
        text = (
            f"🚀 **Downloading...**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"[{bar}] {p}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ **Speed  :** {speed}\n"
            f"📦 **Done    :** {done}\n"
            f"📂 **Total   :** {total}\n"
            f"⏳ **ETA      :** {eta}\n"
            f"⚙️ **Engine  :** `yt-dlp`\n"
            f"🆔 **Task ID :** `{task_id}`\n"
            f"🛑 **Stop    :** `/stop_{task_id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        try: asyncio.run_coroutine_threadsafe(message.edit_text(text), asyncio.get_event_loop())
        except: pass

# --- [2. دالة التحميل الاحترافية] ---
async def download_worker(url, message, task_id, format_id='best'):
    try:
        ydl_opts = {'format': format_id, 'quiet': True, 'progress_hooks': [lambda d: progress_hook(d, message, task_id)]}
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
        await message.edit_text(f"✅ **اكتمل التحميل بنجاح.**\n`Task ID: {task_id}`")
    except Exception as e:
        await message.edit_text(f"❌ **فشل التحميل:**\n`{str(e)}`")
    finally:
        active_tasks.pop(task_id, None)

# --- [3. الأوامر] ---
@app.on_message(filters.command("kmdytleech"))
async def choose_quality(_, m: Message):
    url = m.command[1] if len(m.command) > 1 else ""
    if not url: return await m.reply_text("⚠️ **الرابط مطلوب.**")
    
    # القائمة الثابتة للجودات
    kb = [
        [InlineKeyboardButton("🎥 1080p - mp4", callback_data=f"dl_137_{url}")],
        [InlineKeyboardButton("🎥 720p - mp4", callback_data=f"dl_136_{url}")],
        [InlineKeyboardButton("🎥 480p - mp4", callback_data=f"dl_135_{url}")],
        [InlineKeyboardButton("🎥 360p - mp4", callback_data=f"dl_134_{url}")]
    ]
    await m.reply_text("✅ **اختر الجودة المطلوبة:**", reply_markup=InlineKeyboardMarkup(kb))

@app.on_callback_query(filters.regex("dl_"))
async def start_dl(_, cq: CallbackQuery):
    _, format_id, url = cq.data.split("_", 2)
    task_id = str(uuid.uuid4())[:8]
    status = await cq.message.edit_text("📥 **جاري بدء التحميل...**")
    active_tasks[task_id] = asyncio.create_task(download_worker(url, status, task_id, format_id))

@app.on_message(filters.regex(r"^/stop_([a-zA-Z0-9]+)$"))
async def stop_command(_, m: Message):
    task_id = m.matches[0].group(1)
    if task_id in active_tasks:
        active_tasks[task_id].cancel()
        await m.reply_text("🛑 **تم إيقاف المهمة.**")
    else: await m.reply_text("❌ **المهمة غير موجودة.**")

@app.on_message(filters.command("kmdvideo_tool"))
async def video_tool(_, m: Message):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎞 تحويل (MKV)", callback_data="conv")],
        [InlineKeyboardButton("📉 ضغط (x265)", callback_data="comp")]
    ])
    await m.reply_text("🛠 **KMD Engineering Suite:**", reply_markup=kb)

@app.on_message(filters.command("kmdrestart"))
async def restart(_, m: Message):
    os.execl(sys.executable, sys.executable, *sys.argv)

if __name__ == "__main__":
    app.run()

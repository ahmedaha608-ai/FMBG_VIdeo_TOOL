import os
import sys
import asyncio
import uuid
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv

load_dotenv()
app = Client("Eng_Bot", api_id=int(os.getenv("API_ID")), api_hash=os.getenv("API_HASH"), bot_token=os.getenv("BOT_TOKEN"))

# قاموس لتتبع المهام - لإيقاف التحميل برمجياً
active_tasks = {}

# --- [1. دالة العرض الاحترافي (Torrent Style)] ---
def progress_hook(d, message: Message, task_id: str):
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%').replace(' ', '')
        speed = d.get('_speed_str', 'N/A')
        total = d.get('_total_bytes_str', 'N/A')
        done = d.get('_downloaded_bytes_str', 'N/A')
        
        filled = int(float(p.replace('%', '')) / 10)
        bar = "●" * filled + "○" * (10 - filled)
        
        text = (f"📥 **Task ID:** `{task_id}`\n[{bar}] {p}\nStatus : **Download**\n"
                f"Done : `{done}`\nTotal : `{total}`\nSpeed : `{speed}`\n"
                f"Engine : `yt-dlp`\n> Stop : /stop_{task_id}")
        try: asyncio.run_coroutine_threadsafe(message.edit_text(text), asyncio.get_event_loop())
        except: pass

# --- [2. دالة التحميل مع تحكم كامل] ---
async def download_worker(url, message, task_id, format_id='best'):
    try:
        ydl_opts = {'format': format_id, 'quiet': True, 'progress_hooks': [lambda d: progress_hook(d, message, task_id)]}
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
        await message.edit_text(f"✅ **اكتمل التحميل.**\n`Task ID: {task_id}`")
    except Exception as e:
        await message.edit_text(f"❌ **توقف التحميل:**\n`{str(e)}`")
    finally:
        active_tasks.pop(task_id, None)

# --- [3. الأوامر] ---
@app.on_message(filters.command("kmdytleech"))
async def get_formats(_, m: Message):
    url = m.command[1] if len(m.command) > 1 else ""
    if not url: return await m.reply_text("⚠️ **الرابط مطلوب.**")
    status = await m.reply_text("🔍 **جاري تحليل الجودات...**")
    try:
        info = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL({'quiet': True}).extract_info(url, download=False))
        kb = [[InlineKeyboardButton(f"{f['height']}p - {f.get('ext')}", callback_data=f"dl_{f['format_id']}_{info['id']}")] 
              for f in info.get('formats', []) if f.get('height') and f.get('vcodec') != 'none'][:10]
        await status.edit_text("✅ **اختر الجودة:**", reply_markup=InlineKeyboardMarkup(kb))
    except Exception as e: await status.edit_text(f"❌ **فشل:** `{str(e)}`")

@app.on_callback_query(filters.regex("dl_"))
async def start_dl(_, cq: CallbackQuery):
    _, format_id, vid_id = cq.data.split("_")
    task_id = str(uuid.uuid4())[:8]
    status = await cq.message.edit_text("📥 **جاري بدء التحميل...**")
    active_tasks[task_id] = asyncio.create_task(download_worker(f"https://youtu.be/{vid_id}", status, task_id, format_id))

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
    await m.reply_text("🛠 **KMD Suite:**", reply_markup=kb)

@app.on_message(filters.command("kmdrestart"))
async def restart(_, m: Message):
    os.execl(sys.executable, sys.executable, *sys.argv)

if __name__ == "__main__":
    app.run()

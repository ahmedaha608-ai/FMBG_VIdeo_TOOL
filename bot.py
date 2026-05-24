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

# قاموس لتتبع المهام
active_tasks = {}

# --- [دالة التنسيق الاحترافي - مطابق للصورة] ---
def progress_hook(d, message: Message, task_id: str):
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%').replace(' ', '')
        speed = d.get('_speed_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')
        total = d.get('_total_bytes_str', 'N/A')
        done = d.get('_downloaded_bytes_str', 'N/A')
        
        # رسم شريط التقدم
        filled = int(float(p.replace('%', '')) / 10)
        bar = "●" * filled + "○" * (10 - filled)
        
        text = (
            f"📥 **Task ID:** `{task_id}`\n"
            f"[{bar}] {p}\n"
            f"Status : **Download**\n"
            f"Done : `{done}`\n"
            f"Total : `{total}`\n"
            f"Speed : `{speed}`\n"
            f"ETA : `{eta}`\n"
            f"Engine : `yt-dlp`\n"
            f"> Stop : /stop_{task_id}"
        )
        
        try:
            asyncio.run_coroutine_threadsafe(message.edit_text(text), asyncio.get_event_loop())
        except: pass

# --- [دالة التحميل] ---
async def download_worker(url, message, task_id):
    try:
        ydl_opts = {'format': 'best', 'quiet': True, 'progress_hooks': [lambda d: progress_hook(d, message, task_id)]}
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
        
        if not asyncio.current_task().cancelled():
            await message.edit_text(f"✅ **اكتمل التحميل.**\n`Task ID: {task_id}`")
    except asyncio.CancelledError:
        await message.edit_text("🛑 **تم إلغاء المهمة.**")
    except Exception:
        await message.edit_text("❌ **فشل التحميل.**")
    finally:
        active_tasks.pop(task_id, None)

# --- [الأوامر المحدثة بـ KMD] ---
@app.on_message(filters.command(["kmdleech", "kmdytleech"]))
async def download_handler(_, m: Message):
    url = m.command[1] if len(m.command) > 1 else ""
    if not url: return await m.reply_text("⚠️ **الرابط مطلوب.**")
    
    task_id = str(uuid.uuid4())[:8]
    status = await m.reply_text("📥 **جاري بدء التحميل...**")
    
    task = asyncio.create_task(download_worker(url, status, task_id))
    active_tasks[task_id] = task

@app.on_message(filters.regex(r"^/stop_([a-zA-Z0-9]+)$"))
async def stop_command(_, m: Message):
    task_id = m.matches[0].group(1)
    task = active_tasks.get(task_id)
    if task:
        task.cancel()
        await m.reply_text("⚠️ **تم إيقاف المهمة.**")
    else:
        await m.reply_text("❌ **المهمة غير موجودة.**")

@app.on_message(filters.command("kmdvideo_tool"))
async def video_tool(_, m: Message):
    await m.reply_text("🛠 **KMD Engineering Suite:**", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🎥 Video Composer", callback_data="comp")],
        [InlineKeyboardButton("🤖 AI Enhancer", callback_data="ai")]
    ]))

@app.on_message(filters.command("kmdrestart"))
async def restart(_, m: Message):
    await m.reply_text("🔄 **Rebooting...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

if __name__ == "__main__":
    app.run()

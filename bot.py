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

# قاموس لتتبع المهام الجارية
active_tasks = {}

# --- [1. دالة التنسيق الاحترافي (Torrent Style)] ---
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

# --- [2. دالة التحميل مع كاشف الأخطاء] ---
async def download_worker(url, message, task_id):
    try:
        ydl_opts = {'format': 'best', 'quiet': True, 'progress_hooks': [lambda d: progress_hook(d, message, task_id)]}
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
        
        if not asyncio.current_task().cancelled():
            await message.edit_text(f"✅ **اكتمل التحميل بنجاح.**\n`Task ID: {task_id}`")
            
    except asyncio.CancelledError:
        await message.edit_text("🛑 **تم إلغاء المهمة.**")
    except Exception as e:
        # هنا سيظهر الخطأ الحقيقي إذا فشل التحميل
        await message.edit_text(f"❌ **فشل التحميل:**\n`{str(e)}`")
    finally:
        active_tasks.pop(task_id, None)

# --- [3. الأوامر المحدثة بـ KMD] ---
@app.on_message(filters.command(["kmdleech", "kmdytleech"]))
async def download_handler(_, m: Message):
    url = m.command[1] if len(m.command) > 1 else ""
    if not url: return await m.reply_text("⚠️ **الرابط مطلوب.**")
    
    task_id = str(uuid.uuid4())[:8]
    status = await m.reply_text("📥 **جاري بدء التحميل...**")
    active_tasks[task_id] = asyncio.create_task(download_worker(url, status, task_id))

@app.on_message(filters.regex(r"^/stop_([a-zA-Z0-9]+)$"))
async def stop_command(_, m: Message):
    task_id = m.matches[0].group(1)
    if task_id in active_tasks:
        active_tasks[task_id].cancel()
        await m.reply_text("⚠️ **تم إنهاء المهمة بنجاح.**")
    else:
        await m.reply_text("❌ **المهمة غير موجودة أو انتهت.**")

@app.on_message(filters.command("kmdvideo_tool"))
async def video_tool(_, m: Message):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎞 تحويل الصيغة (MKV)", callback_data="conv_mkv")],
        [InlineKeyboardButton("➕ إضافة ترجمة", callback_data="add_sub")],
        [InlineKeyboardButton("📉 ضغط (x265)", callback_data="comp_x265")],
        [InlineKeyboardButton("🤖 تحسين الجودة (AI)", callback_data="ai_enhance")]
    ])
    await m.reply_text("🛠 **KMD Engineering Suite:**", reply_markup=kb)

@app.on_callback_query()
async def callback_handler(_, cq: CallbackQuery):
    if cq.data == "conv_mkv": await cq.message.edit_text("⚙️ **جاري التحويل...**")
    elif cq.data == "comp_x265": await cq.message.edit_text("🚀 **جاري الضغط...**")
    else: await cq.answer("هذه الميزة تحت التطوير الهندسي")

@app.on_message(filters.command("kmdrestart"))
async def restart(_, m: Message):
    await m.reply_text("🔄 **Rebooting...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

if __name__ == "__main__":
    app.run()

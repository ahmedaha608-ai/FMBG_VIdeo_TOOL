import os
import sys
import asyncio
import uuid
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv

# إعدادات الاتصال
load_dotenv()
app = Client("Eng_Bot", api_id=int(os.getenv("API_ID")), api_hash=os.getenv("API_HASH"), bot_token=os.getenv("BOT_TOKEN"))

# إعدادات هندسية
semaphore = asyncio.Semaphore(3)
active_tasks = {} # لتخزين المهام الحالية من أجل الإلغاء
failed_links = {}
QUALITY_OPTIONS = ["240p", "360p", "480p", "720p", "1080p"]

# --- [نظام عداد التحميل مع زر الإلغاء] ---
def progress_hook(d, message: Message, task_id: str):
    if d['status'] == 'downloading':
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚫 إلغاء المهمة", callback_data=f"stop_{task_id}")]])
        try:
            asyncio.run_coroutine_threadsafe(
                message.edit_text(f"📥 **التحميل:** {d.get('_percent_str')}\n⚡ **السرعة:** {d.get('_speed_str')}", reply_markup=kb), 
                asyncio.get_event_loop())
        except: pass

# --- [أوامر التحميل] ---
@app.on_message(filters.command(["leech", "ytleech"]))
async def download_handler(_, m: Message):
    url = m.command[1] if len(m.command) > 1 else ""
    if not url: return await m.reply_text("⚠️ **الرابط مطلوب.**")
    
    task_id = str(uuid.uuid4())[:8]
    status = await m.reply_text("⏳ **جارٍ الإضافة للطابور...**")
    
    async def run_task():
        async with semaphore:
            active_tasks[task_id] = asyncio.current_task()
            try:
                ydl_opts = {'format': 'best', 'progress_hooks': [lambda d: progress_hook(d, status, task_id)]}
                await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
                await status.edit_text("✅ **اكتمل التحميل.**")
            except asyncio.CancelledError:
                await status.edit_text("🛑 **تم إلغاء المهمة.**")
            finally:
                active_tasks.pop(task_id, None)

    asyncio.create_task(run_task())

# --- [زر الإلغاء] ---
@app.on_callback_query(filters.regex("stop_"))
async def stop_task(_, cq: CallbackQuery):
    task_id = cq.data.split("_")[1]
    task = active_tasks.get(task_id)
    if task:
        task.cancel()
        await cq.answer("تم الإيقاف")
    else:
        await cq.answer("المهمة غير موجودة أو انتهت")

# --- [أداة الفيديو] ---
@app.on_message(filters.command("video_tool"))
async def video_tool(_, m: Message):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎥 Video Composer", callback_data="comp_menu")],
        [InlineKeyboardButton("🤖 AI Enhancer", callback_data="ai_enhance")]
    ])
    await m.reply_text("🛠 **Engineering Suite:**", reply_markup=kb)

@app.on_callback_query(filters.regex("comp_menu"))
async def comp_menu(_, cq: CallbackQuery):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(q, callback_data=f"proc_{q}")] for q in QUALITY_OPTIONS])
    await cq.message.edit_text("⚙️ **اختر الجودة:**", reply_markup=kb)

# --- [الريستارت] ---
@app.on_message(filters.command("restart"))
async def restart(_, m: Message):
    await m.reply_text("🔄 **Rebooting...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

if __name__ == "__main__":
    app.run()

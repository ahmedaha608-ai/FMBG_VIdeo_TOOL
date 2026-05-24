import os
import sys
import asyncio
import uuid
import yt_dlp
import speedtest
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv

load_dotenv()
app = Client("Eng_Bot", api_id=int(os.getenv("API_ID")), api_hash=os.getenv("API_HASH"), bot_token=os.getenv("BOT_TOKEN"))

active_tasks = {}

# --- [دالة العرض الضخمة] ---
def progress_hook(d, message: Message, task_id: str):
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%').replace(' ', '')
        text = (
            f"🚀 **KMD Professional Downloader**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"[{'▓' * int(float(p.replace('%', ''))/2.5)}{'░' * (40 - int(float(p.replace('%', ''))/2.5))}]\n"
            f"**Progress :** {p} | **Speed :** {d.get('_speed_str', 'N/A')}\n"
            f"**ETA :** {d.get('_eta_str', 'N/A')} | **Task ID :** `{task_id}`\n"
            f"🛑 **Stop :** `/stop_{task_id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        try: asyncio.run_coroutine_threadsafe(message.edit_text(text), asyncio.get_event_loop())
        except: pass

# --- [دالة التحميل الاحترافية] ---
async def download_worker(url, message, task_id, format_id='best'):
    def hook(d):
        if task_id not in active_tasks: raise Exception("STOPPED_BY_USER")
        progress_hook(d, message, task_id)
    try:
        ydl_opts = {'format': format_id, 'quiet': True, 'progress_hooks': [hook]}
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
        await message.edit_text(f"✅ **اكتمل التحميل.**\n`Task ID: {task_id}`")
    except Exception as e:
        if str(e) == "STOPPED_BY_USER": await message.edit_text("🛑 **تم إيقاف المهمة.**")
        else: await message.edit_text(f"❌ **فشل التحميل:**\n`{str(e)}`")
    finally: active_tasks.pop(task_id, None)

# --- [الأوامر الموحدة (leechkmd)] ---
@app.on_message(filters.command("leechkmdleech"))
async def direct_leech(_, m: Message):
    url = m.command[1] if len(m.command) > 1 else ""
    if not url or "http" not in url: return await m.reply_text("⚠️ **أدخل رابطاً مباشراً.**")
    await m.reply_text("📥 **جاري التحميل المباشر...**")

@app.on_message(filters.command("leechkmdytleech"))
async def yt_leech(_, m: Message):
    if len(m.command) < 2: return await m.reply_text("⚠️ **الرجاء إرسال الرابط.**")
    url = m.command[1]
    kb = [[InlineKeyboardButton(f"🎥 {q}p - mp4", callback_data=f"dl_{fid}_{url}")] 
          for q, fid in [("1080", "137"), ("720", "136"), ("480", "135")]]
    await m.reply_text("✅ **اختر الجودة المطلوبة:**", reply_markup=InlineKeyboardMarkup(kb))

@app.on_callback_query(filters.regex("dl_"))
async def start_dl(_, cq: CallbackQuery):
    _, format_id, url = cq.data.split("_", 2)
    task_id = str(uuid.uuid4())[:8]
    status = await cq.message.edit_text("📥 **جاري بدء المعالجة...**")
    active_tasks[task_id] = asyncio.create_task(download_worker(url, status, task_id, format_id))

@app.on_message(filters.command("leechkmdSpeedtest"))
async def speedtest_cmd(_, m: Message):
    status = await m.reply_text("🚀 **جاري اختبار سرعة السيرفر...**")
    s = speedtest.Speedtest()
    s.get_best_server()
    await status.edit_text(f"📊 **نتائج السرعة:**\n📥 D: `{s.download()/1024/1024:.2f} Mbps`\n📤 U: `{s.upload()/1024/1024:.2f} Mbps`")

@app.on_message(filters.command("leechkmdvideo_tool"))
async def video_tool(_, m: Message):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎞 Composer", callback_data="comp"), InlineKeyboardButton("✨ AI Enhancer", callback_data="ai")],
        [InlineKeyboardButton("📄 Doc Converter", callback_data="to_doc"), InlineKeyboardButton("🎥 MP4 Converter", callback_data="to_mp4")],
        [InlineKeyboardButton("🧪 فيديو تجريبي", callback_data="test_vid"), InlineKeyboardButton("🖼 تغيير الخلفية", callback_data="bg_change")]
    ])
    await m.reply_text("🛠 **KMD Engineering Suite:**", reply_markup=kb)

@app.on_message(filters.regex(r"^/stop_([a-zA-Z0-9]+)$"))
async def stop_command(_, m: Message):
    task_id = m.matches[0].group(1)
    if task_id in active_tasks:
        active_tasks.pop(task_id)
        await m.reply_text("🛑 **تم إيقاف المهمة.**")

@app.on_message(filters.command("leechkmdrestart"))
async def restart(_, m: Message):
    await m.reply_text("🔄 **Rebooting...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

@app.on_callback_query()
async def callbacks(_, cq: CallbackQuery):
    if cq.data == "test_vid":
        await cq.message.reply_video("https://www.w3schools.com/html/mov_bbb.mp4", caption="🧪 **فيديو تجريبي.**")
    else: await cq.answer("هذه الميزة تحت التطوير الهندسي.")

if __name__ == "__main__":
    app.run()

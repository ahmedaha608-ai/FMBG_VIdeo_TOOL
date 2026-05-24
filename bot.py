import os
import sys
import asyncio
import uuid
import yt_dlp
import speedtest
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv

# تهيئة البوت
load_dotenv()
app = Client("Eng_Bot", api_id=int(os.getenv("API_ID")), api_hash=os.getenv("API_HASH"), bot_token=os.getenv("BOT_TOKEN"))

active_tasks = {}

# --- [دالة العرض المدمجة الاحترافية] ---
def progress_hook(d, message: Message, task_id: str):
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%').replace(' ', '')
        speed = d.get('_speed_str', 'N/A')
        total = d.get('_total_bytes_str', 'N/A')
        done = d.get('_downloaded_bytes_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')
        
        filled = int(float(p.replace('%', '')) / 2.5)
        bar = "▓" * filled + "░" * (80 - filled)
        
        text = (
            f"🚀 **KMD Professional Downloader**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"[{bar}]\n"
            f"**Progress :** {p}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ **Speed  :** {speed}\n"
            f"📦 **Done    :** {done}\n"
            f"📂 **Total   :** {total}\n"
            f"⏳ **ETA      :** {eta}\n"
            f"⚙️ **Engine  :** `yt-dlp`\n"
            f"🆔 **Task ID :** `{task_id}`\n"
            f"🛑 **Stop    :** `/stop_{task_id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        try: asyncio.run_coroutine_threadsafe(message.edit_text(text), asyncio.get_event_loop())
        except: pass

# --- [الأوامر الموحدة (تنتهي بـ kmd)] ---

# 1. التحميل المباشر
@app.on_message(filters.command("Leechkmd"))
async def direct_leech(_, m: Message):
    if len(m.command) < 2: return await m.reply_text("⚠️ **الرجاء إرسال رابط مباشر.**")
    await m.reply_text("📥 **جاري تحميل الملف المباشر...**")

# 2. تحميل المنصات
@app.on_message(filters.command("YtLeechkmd"))
async def yt_leech(_, m: Message):
    if len(m.command) < 2: return await m.reply_text("⚠️ **أرسل رابط (YT, VK, IG, TikTok).**")
    await m.reply_text("🔍 **جاري معالجة الفيديو...**")

# 3. اختبار السرعة
@app.on_message(filters.command("Speedtestkmd"))
async def speedtest_cmd(_, m: Message):
    status = await m.reply_text("🚀 **جاري قياس سرعة السيرفر...**")
    try:
        s = speedtest.Speedtest()
        s.get_best_server()
        d = s.download() / 1024 / 1024
        u = s.upload() / 1024 / 1024
        await status.edit_text(f"📊 **النتائج:**\n📥 D: `{d:.2f} Mbps`\n📤 U: `{u:.2f} Mbps`")
    except Exception as e:
        await status.edit_text(f"❌ **فشل:** `{str(e)}`")

# 4. لوحة أدوات الفيديو المتقدمة
@app.on_message(filters.command("Videotoolkmd"))
async def video_tool(_, m: Message):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("1. Video Composer", callback_data="v_comp")],
        [InlineKeyboardButton("2. تحسين جودة الصور", callback_data="v_ai")],
        [InlineKeyboardButton("3. تحويل الفيديو لمستند", callback_data="v_doc")],
        [InlineKeyboardButton("4. تحويل الملف لـ MP4", callback_data="v_mp4")],
        [InlineKeyboardButton("5. فيديو تجريبي", callback_data="v_test")],
        [InlineKeyboardButton("6. تغيير صورة الخلفية", callback_data="v_bg")]
    ])
    await m.reply_text("🛠 **KMD Video Tools Suite:**", reply_markup=kb)

@app.on_callback_query(filters.regex("v_"))
async def tool_callback(_, cq: CallbackQuery):
    if cq.data == "v_test":
        await cq.message.reply_video("https://www.w3schools.com/html/mov_bbb.mp4", caption="🧪 **فيديو تجريبي.**")
    else:
        await cq.answer("تم تفعيل الأداة...", show_alert=True)

# 5. الإيقاف
@app.on_message(filters.regex(r"^/stop_([a-zA-Z0-9]+)$"))
async def stop_command(_, m: Message):
    task_id = m.matches[0].group(1)
    if task_id in active_tasks:
        active_tasks.pop(task_id)
        await m.reply_text("🛑 **تم الإيقاف.**")

if __name__ == "__main__":
    app.run()

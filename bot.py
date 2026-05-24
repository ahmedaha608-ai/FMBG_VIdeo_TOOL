import os
import sys
import asyncio
import uuid
import yt_dlp
import speedtest
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv

# 1. إعداد المتغيرات
load_dotenv()
api_id = int(os.getenv("API_ID", 0))
api_hash = os.getenv("API_HASH", "")
bot_token = os.getenv("BOT_TOKEN", "")

# 2. تهيئة البوت
app = Client("KMD_Bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
active_tasks = {}

# --- [دالة العرض الاحترافية] ---
def progress_hook(d, message: Message, task_id: str):
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%')
        speed = d.get('_speed_str', 'N/A')
        text = (f"🚀 **KMD Downloader**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"**Progress :** {p}\n"
                f"⚡ **Speed :** {speed}\n"
                f"🆔 **ID :** `{task_id}`\n"
                f"🛑 `/stop_{task_id}`")
        try: asyncio.run_coroutine_threadsafe(message.edit_text(text), asyncio.get_event_loop())
        except: pass

# --- [الأوامر الموحدة (تنتهي بـ kmd)] ---

@app.on_message(filters.command(["Leechkmd"]))
async def direct_leech(client, m: Message):
    if len(m.command) < 2: return await m.reply_text("⚠️ أرسل الرابط المباشر.")
    await m.reply_text("📥 جاري بدء التحميل المباشر...")

@app.on_message(filters.command(["YtLeechkmd"]))
async def yt_leech(client, m: Message):
    if len(m.command) < 2: return await m.reply_text("⚠️ أرسل رابط (YT, VK, IG, TikTok).")
    await m.reply_text("🔍 جاري معالجة الفيديو (بدون علامة مائية)...")

@app.on_message(filters.command(["Speedtestkmd"]))
async def speedtest_cmd(client, m: Message):
    status = await m.reply_text("🚀 جاري قياس سرعة السيرفر...")
    try:
        s = speedtest.Speedtest()
        s.get_best_server()
        d = s.download() / 1024 / 1024
        u = s.upload() / 1024 / 1024
        await status.edit_text(f"📊 النتائج:\n📥 D: {d:.2f} Mbps\n📤 U: {u:.2f} Mbps")
    except Exception as e:
        await status.edit_text(f"❌ خطأ: {e}")

@app.on_message(filters.command(["Videotoolkmd"]))
async def video_tool(client, m: Message):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("1. Video Composer", callback_data="v_comp")],
        [InlineKeyboardButton("2. تحسين جودة الصور", callback_data="v_ai")],
        [InlineKeyboardButton("3. تحويل لمستند", callback_data="v_doc")],
        [InlineKeyboardButton("4. تحويل لـ MP4", callback_data="v_mp4")],
        [InlineKeyboardButton("5. فيديو تجريبي", callback_data="v_test")],
        [InlineKeyboardButton("6. تغيير صورة الخلفية", callback_data="v_bg")]
    ])
    await m.reply_text("🛠 **KMD Video Tools Suite:**", reply_markup=kb)

@app.on_callback_query(filters.regex("v_test"))
async def test_callback(client, cq: CallbackQuery):
    await cq.message.reply_video("https://www.w3schools.com/html/mov_bbb.mp4", caption="🧪 فيديو تجريبي للضغط.")

@app.on_message(filters.regex(r"^/stop_([a-zA-Z0-9]+)$"))
async def stop_command(client, m: Message):
    await m.reply_text("🛑 تم الإيقاف.")

# تشغيل البوت
if __name__ == "__main__":
    print("البوت يعمل الآن...")
    app.run()

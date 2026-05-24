import os
import asyncio
import yt_dlp
import speedtest
import uuid
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv

load_dotenv()
app = Client("KMD_Bot", api_id=int(os.getenv("API_ID")), api_hash=os.getenv("API_HASH"), bot_token=os.getenv("BOT_TOKEN"))

# --- [محرك التحميل والمهام] ---
async def process_download(url, message, format_id):
    try:
        await message.edit_text("📥 **جاري بدء التحميل الفعلي...**")
        ydl_opts = {'format': format_id, 'outtmpl': 'kmd_video.mp4', 'quiet': True}
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
        
        await message.edit_text("✅ **اكتمل التحميل! جاري الإرسال...**")
        await message.reply_video("kmd_video.mp4", caption="تم التحميل بواسطة KMD Professional Suite")
        os.remove("kmd_video.mp4")
    except Exception as e:
        await message.edit_text(f"❌ **فشل التحميل:** `{str(e)}`")

# --- [الأوامر الاحترافية] ---

@app.on_message(filters.command("YtLeechkmd"))
async def yt_leech(client, m: Message):
    if len(m.command) < 2: return await m.reply_text("⚠️ أرسل الرابط.")
    url = m.command[1]
    msg = await m.reply_text("🔍 جاري استخراج الجودات...")
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = [f for f in info.get('formats', []) if f.get('ext') == 'mp4'][:6]
            kb = [[InlineKeyboardButton(f"{f.get('format_note', 'HD')}", callback_data=f"dl_{f['format_id']}_{url}")] for f in formats]
            await msg.edit_text("✅ اختر الجودة:", reply_markup=InlineKeyboardMarkup(kb))
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {e}")

@app.on_callback_query(filters.regex("^dl_"))
async def handle_dl(client, cq: CallbackQuery):
    _, fid, url = cq.data.split("_", 2)
    await process_download(url, cq.message, fid)

@app.on_message(filters.command("Speedtestkmd"))
async def speedtest_cmd(client, m: Message):
    status = await m.reply_text("🚀 جاري اختبار السرعة...")
    try:
        s = speedtest.Speedtest()
        s.get_best_server()
        d = s.download() / 1024 / 1024
        u = s.upload() / 1024 / 1024
        await status.edit_text(f"📊 **النتائج:**\n📥 D: `{d:.2f} Mbps`\n📤 U: `{u:.2f} Mbps`")
    except Exception as e:
        await status.edit_text(f"❌ فشل: {e}")

@app.on_message(filters.command("Videotoolkmd"))
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

@app.on_callback_query(filters.regex("^v_"))
async def v_callback(client, cq: CallbackQuery):
    if cq.data == "v_test":
        await cq.message.reply_video("https://www.w3schools.com/html/mov_bbb.mp4", caption="🧪 فيديو تجريبي للضغط.")
    else:
        await cq.answer("هذه الأداة قيد التطوير...", show_alert=True)

if __name__ == "__main__":
    app.run()

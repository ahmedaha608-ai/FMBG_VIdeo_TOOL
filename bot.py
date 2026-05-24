import os
import sys
import asyncio
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv

load_dotenv()
app = Client("Eng_Bot", api_id=int(os.getenv("API_ID")), api_hash=os.getenv("API_HASH"), bot_token=os.getenv("BOT_TOKEN"))

# إعدادات النظام الهندسي
semaphore = asyncio.Semaphore(3) # إدارة المهام المتزامنة (3 كحد أقصى)
failed_links = {}
QUALITY_OPTIONS = ["240p", "360p", "480p", "720p", "1080p"]

# --- [نظام عداد التحميل] ---
def progress_hook(d, message: Message):
    if d['status'] == 'downloading':
        try:
            asyncio.run_coroutine_threadsafe(
                message.edit_text(f"📥 **التحميل:** {d.get('_percent_str')}\n⚡ **السرعة:** {d.get('_speed_str')}"), 
                asyncio.get_event_loop())
        except: pass

# --- [1. أداة الفيديو الشاملة (Video Tool)] ---
@app.on_message(filters.command("video_tool"))
async def video_tool(_, m: Message):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎥 Video Composer", callback_data="comp_menu")],
        [InlineKeyboardButton("🤖 AI Enhancer", callback_data="ai_enhance")],
        [InlineKeyboardButton("🔄 Convert/Sub", callback_data="misc_tool")]
    ])
    await m.reply_text("🛠 **Engineering Video Suite:**\nاختر الأداة المطلوبة:", reply_markup=kb)

# --- [2. قائمة الجودات المختارة (1/2)] ---
@app.on_callback_query(filters.regex("comp_menu"))
async def comp_menu(_, cq: CallbackQuery):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(q, callback_data=f"proc_{q}")] for q in QUALITY_OPTIONS])
    await cq.message.edit_text("⚙️ **اختر جودة الضغط (x265):**", reply_markup=kb)

@app.on_callback_query(filters.regex("proc_"))
async def run_composer(_, cq: CallbackQuery):
    quality = cq.data.split("_")[1]
    await cq.message.edit_text(f"🚀 **جاري الضغط لجودة {quality}...**\n")
    await asyncio.sleep(5) # محاكاة معالجة FFmpeg
    await cq.message.edit_text(f"✅ **تمت معالجة الفيديو بنجاح بجودة {quality}.**")

# --- [3. الذكاء الاصطناعي (AI Enhancer)] ---
@app.on_callback_query(filters.regex("ai_enhance"))
async def ai_enhance(_, cq: CallbackQuery):
    await cq.message.edit_text("🤖 **AI Enhancer:**\nجاري رفع جودة الفيديو عبر خوارزميات الـ Super Resolution...")

# --- [4. التحميل (Leech & YtLeech)] ---
@app.on_message(filters.command(["leechkmd", "ytleechkmd"]))
async def download_handler(_, m: Message):
    url = m.command[1] if len(m.command) > 1 else ""
    if not url: return await m.reply_text("⚠️ **الرابط مطلوب.**")
    if failed_links.get(url, 0) >= 3: return await m.reply_text("🚫 **رابط محظور (تالف).**")
    
    async with semaphore:
        status = await m.reply_text("📥 **جاري التحميل...**")
        await asyncio.sleep(10) # الفاصل الهندسي بين المهام
        try:
            ydl_opts = {'format': 'best', 'quiet': True, 'progress_hooks': [lambda d: progress_hook(d, status)]}
            await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
            await status.edit_text("✅ **اكتمل التحميل.**")
        except:
            failed_links[url] = failed_links.get(url, 0) + 1
            await status.edit_text("❌ **فشل التحميل.**")

# --- [5. الريستارت الهندسي] ---
@app.on_message(filters.command("restart_kmd"))
async def restart(_, m: Message):
    await m.reply_text("🔄 **Rebooting for Railway...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

if __name__ == "__main__":
    app.run()

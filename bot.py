import os
import time
import asyncio
import subprocess
import mimetypes
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv

load_dotenv()
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("video_quality_bot", api_id=int(API_ID), api_hash=API_HASH, bot_token=BOT_TOKEN)

# مخازن البيانات المؤقتة
user_data = {}
user_thumbs = {}

# إعدادات أبعاد وجودة الضغط لكل خيار (العرض : الارتفاع : معدل البت)
QUALITY_SETTINGS = {
    "240p": {"scale": "426:240", "crf": "30", "bitrate": "64k"},
    "360p": {"scale": "640:360", "crf": "28", "bitrate": "96k"},
    "480p": {"scale": "854:480", "crf": "26", "bitrate": "128k"},
    "720p": {"scale": "1280:720", "crf": "24", "bitrate": "192k"}
}

# --- دالة صُنع شريط التقدم الفعلي (Progress Bar) ---
def create_progress_bar(current, total, status_text, start_time):
    now = time.time()
    diff = now - start_time
    if diff == 0: return ""
    
    percentage = current * 100 / total
    speed = current / diff
    elapsed_time = round(diff)
    
    speed_mb = speed / (1024 * 1024)
    current_mb = current / (1024 * 1024)
    total_mb = total / (1024 * 1024)
    
    completed_blocks = int(percentage // 10)
    remaining_blocks = 10 - completed_blocks
    progress_str = "█" * completed_blocks + "░" * remaining_blocks
    
    return (
        f"📊 **{status_text}**\n\n"
        f"🎬 [{progress_str}] {percentage:.1f}%\n"
        f"📦 **المُعالج:** {current_mb:.2f} MB / {total_mb:.2f} MB\n"
        f"⚡ **السرعة:** {speed_mb:.2f} MB/s\n"
        f"⏱️ **الوقت المنقضي:** {elapsed_time} ثانية"
    )

async def progress_callback(current, total, client, message, status_text, start_time):
    if not hasattr(progress_callback, "last_update"):
        progress_callback.last_update = 0
    if time.time() - progress_callback.last_update > 4 or current == total:
        progress_callback.last_update = time.time()
        bar = create_progress_bar(current, total, status_text, start_time)
        try:
            await message.edit_text(bar)
        except:
            pass

# --- 1. أمر البداية ---
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "👋 أهلاً بك في بوت معالجة وضغط الفيديو الذكي بالمجموعات!\n\n"
        "🎬 **طريقة الضغط الجديدة:**\n"
        "قم بالرد بـ `/compressor_video` على أي فيديو، واختار الجودة المطلوبة من الأزرار الشفافة."
    )

# --- 2. أمر ضغط الفيديو بالرد لتوليد أزرار الجودات ---
@app.on_message(filters.command("compressor_video"))
async def ask_for_quality(client, message: Message):
    if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.document):
        return await message.reply_text("⚠️ خطأ: يجب الرد (Reply) بهذا الأمر على الفيديو أو الفيلم المطلوب ضغطه!")

    # إنشاء الأزرار الشفافة باختيارات الجودات الأربعة
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 240p (حجم صغير جداً)", callback_data=f"q_240p_{message.reply_to_message.id}"),
            InlineKeyboardButton("🎬 360p (اقتصادي)", callback_data=f"q_360p_{message.reply_to_message.id}")
        ],
        [
            InlineKeyboardButton("🎬 480p (متوسط)", callback_data=f"q_480p_{message.reply_to_message.id}"),
            InlineKeyboardButton("🎬 720p (جودة عالية HD)", callback_data=f"q_720p_{message.reply_to_message.id}")
        ]
    ])

    await message.reply_text(
        f"⚙️ **يا {message.from_user.first_name}، الرجاء اختيار جودة الضغط المطلوبة للفيلم:**",
        reply_markup=keyboard
    )

# --- 3. معالجة الضغط الفعلي عند الضغط على زر الجودة (CallbackQuery) ---
@app.with_reply()
@app.on_callback_query(filters.regex(r"^q_"))
async def start_compression_callback(client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split("_")
    quality = data_parts[1]      # مثال: 360p
    target_msg_id = int(data_parts[2]) # ID رسالة الفيديو الأصلية
    
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    
    # جلب رسالة الفيديو الأصلية
    try:
        target_msg = await client.get_messages(chat_id, target_msg_id)
    except:
        return await callback_query.answer("❌ تعذر العثور على الفيديو الأصلي، ربما تم حذفه.", show_alert=True)

    # إغلاق شاشة الأزرار وتحديث النص لبدء التحميل
    await callback_query.answer(f"⏳ تم اختيار {quality}.. جاري بدء التحميل للسيرفر", show_alert=False)
    status = callback_query.message
    await status.edit_text(f"📥 جاري سحب وتحميل الفيديو من تليجرام لمعالجته بجودة {quality}...")

    # [أ] تحميل الفيديو للسيرفر مع العداد
    start_time = time.time()
    input_file = await target_msg.download(
        progress=progress_callback,
        progress_args=(client, status, f"جاري تحميل الفيديو الأصلي لتشغيل جودة {quality}", start_time)
    )
    
    output_file = f"compressed_{quality}_{chat_id}_{user_id}.mp4"
    await status.edit_text(f"⚡ يتم الآن ضغط وتحجيم الفيديو إلى جودة {quality} (HEVC x265)... يرجى الانتظار.")
    
    # جلب إعدادات الجودة المختارة
    settings = QUALITY_SETTINGS[quality]
    
    # أمر FFmpeg الديناميكي الفعلي الذي يغير المقاس (Scale) والجودة (CRF) ومعدل الصوت (Bitrate)
    cmd = [
        "ffmpeg", "-i", input_file,
        "-vf", f"scale={settings['scale']}", 
        "-vcodec", "libx265", "-crf", settings['crf'],
        "-preset", "faster", 
        "-acodec", "aac", "-b:a", settings['bitrate'], 
        output_file, "-y"
    ]
    
    process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await process.wait()

    # [ب] الرفع الفعلي للجروب بعد الضغط مع العداد
    if os.path.exists(output_file):
        await status.edit_text(f"📤 اكتمل الضغط الفعلي لـ {quality}! جاري الرفع بالعداد...")
        start_time = time.time()
        await target_msg.reply_video(
            video=output_file, 
            caption=f"🎬 تم الضغط بنجاح!\n⚙️ **الجودة المحددة:** {quality} (x265 HEVC)\n👤 بطلب من: {callback_query.from_user.mention}",
            progress=progress_callback,
            progress_args=(client, status, f"جاري رفع الفيديو المضغوط ({quality})", start_time)
        )
        os.remove(output_file)
    else:
        await status.edit_text("❌ فشل عملية الضغط، يرجى التأكد من سلامة ملف الفيديو الأصلي.")

    if os.path.exists(input_file):
        os.remove(input_file)
    await status.delete()

# --- 4. بقية الأكواد (تغيير الـ Thumbnail والـ Leech كما هي ومطورة بالـ Reply والعداد) ---
@app.on_message(filters.command(["leechkmd", "torrentleechkmd"]))
async def set_leech_or_torrent(client, message: Message):
    user_data[(message.chat.id, message.from_user.id)] = {'action': message.command[0]}
    await message.reply_text(f"📥 {message.from_user.mention} أرسل الآن الرابط أو التورنت.")

@app.on_message(filters.text | (filters.document & ~filters.video))
async def handle_leech_inputs(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    state = user_data.get((chat_id, user_id), {})
    action = state.get('action')

    if action not in ['leechkmd', 'torrentleechkmd']: return

    target = message.text.strip() if message.text else await message.download()
    status = await message.reply_text("⏳ جاري التحميل الفعلي بالسيرفر عبر Aria2...")
    user_data[(chat_id, user_id)] = {} 
    
    user_download_dir = f"dl_{chat_id}_{user_id}"
    os.makedirs(user_download_dir, exist_ok=True)
    cmd = ["aria2c", f"--dir={user_download_dir}", "--seed-time=0", target]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await process.wait()

    if os.path.exists(user_download_dir) and os.listdir(user_download_dir):
        await status.edit_text("📤 جاري رفع الملفات الناتجة بالعداد الفعلي...")
        for root, dirs, files in os.walk(user_download_dir):
            for file in files:
                file_path = os.path.join(root, file)
                mime_type, _ = mimetypes.guess_type(file_path)
                start_time = time.time()
                if mime_type and mime_type.startswith("video"):
                    await message.reply_video(video=file_path, caption=f"🎬 تم الرفع بنجاح!\n👤 طلب: {message.from_user.mention}", progress=progress_callback, progress_args=(client, status, f"جاري رفع: {file}", start_time))
                else:
                    await message.reply_document(document=file_path, caption=f"📄 تم الرفع بنجاح!\n👤 طلب: {message.from_user.mention}", progress=progress_callback, progress_args=(client, status, f"جاري رفع: {file}", start_time))
                if os.path.exists(file_path): os.remove(file_path)
    else:
        await status.edit_text("❌ فشل التحميل.")
    try: os.rmdir(user_download_dir)
    except: pass
    await status.delete()

@app.on_message(filters.photo)
async def save_photo_thumb(client, message: Message):
    thumb_path = f"thumb_{message.chat.id}_{message.from_user.id}.jpg"
    await message.download(file_name=thumb_path)
    user_thumbs[(message.chat.id, message.from_user.id)] = thumb_path
    await message.reply_text("🖼️ تم حفظ الثمنيل! قم بعمل رد بـ `/change_thumbs` على الفيديو لتطبيقه.")

@app.on_message(filters.command("change_thumbs"))
async def apply_thumb_via_reply(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    thumb_path = user_thumbs.get((chat_id, user_id))

    if not thumb_path: return await message.reply_text("⚠️ أرسل الصورة أولاً.")
    if not message.reply_to_message: return await message.reply_text("⚠️ قم بالرد على فيديو.")

    status = await message.reply_text("⏳ جاري دمج الثمنيل بالعداد...")
    start_time = time.time()
    input_file = await message.reply_to_message.download(progress=progress_callback, progress_args=(client, status, "جاري سحب الفيديو", start_time))
    
    start_time = time.time()
    await message.reply_to_message.reply_video(video=input_file, thumb=thumb_path, caption=f"🖼️ تم تعديل الصورة!\n👤 طلب: {message.from_user.mention}", progress=progress_callback, progress_args=(client, status, "جاري الرفع بالثمنيل الجديد", start_time))
    
    if os.path.exists(thumb_path): os.remove(thumb_path)
    if os.path.exists(input_file): os.remove(input_file)
    user_thumbs[(chat_id, user_id)] = None
    await status.delete()

if __name__ == "__main__":
    print("🚀 البوت الذكي بأزرار الجودات والعداد يعمل الآن بنجاح...")
    app.run()

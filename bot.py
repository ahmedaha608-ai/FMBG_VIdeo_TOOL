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

app = Client("video_ultimate_bot", api_id=int(API_ID), api_hash=API_HASH, bot_token=BOT_TOKEN)

user_thumbs = {}
MAX_TG_SIZE = 2000 * 1024 * 1024  # حد تليجرام الافتراضي (2 جيجابايت)

QUALITY_SETTINGS = {
    "240p": {"scale": "426:240", "crf": "30", "bitrate": "64k"},
    "360p": {"scale": "640:360", "crf": "28", "bitrate": "96k"},
    "480p": {"scale": "854:480", "crf": "26", "bitrate": "128k"},
    "720p": {"scale": "1280:720", "crf": "24", "bitrate": "192k"}
}

# --- دالة شريط التقدم الفعلي ---
def create_progress_bar(current, total, status_text, start_time):
    now = time.time()
    diff = now - start_time
    if diff == 0: return ""
    percentage = current * 100 / total
    speed = current / diff
    speed_mb = speed / (1024 * 1024)
    current_mb = current / (1024 * 1024)
    total_mb = total / (1024 * 1024)
    progress_str = "█" * int(percentage // 10) + "░" * (10 - int(percentage // 10))
    return f"📊 **{status_text}**\n\n🎬 [{progress_str}] {percentage:.1f}%\n📦 **المُعالج:** {current_mb:.2f} MB / {total_mb:.2f} MB\n⚡ **السرعة:** {speed_mb:.2f} MB/s\n⏱️ **الوقت:** {round(diff)} ثانية"

async def progress_callback(current, total, client, message, status_text, start_time):
    if not hasattr(progress_callback, "last_update"): progress_callback.last_update = 0
    if time.time() - progress_callback.last_update > 4 or current == total:
        progress_callback.last_update = time.time()
        bar = create_progress_bar(current, total, status_text, start_time)
        try: await message.edit_text(bar)
        except: pass

# --- دالة التقطيع والرفع التلقائي للأحجام الضخمة ---
async def split_and_upload_video(client, message, status, file_path, caption_text):
    file_size = os.path.getsize(file_path)
    if file_size <= MAX_TG_SIZE:
        start_time = time.time()
        await message.reply_video(video=file_path, caption=caption_text, progress=progress_callback, progress_args=(client, status, "جاري الرفع", start_time))
        return

    await status.edit_text("✂️ حجم الملف تخطى 2GB! جاري تقطيع الفيلم تلقائياً...")
    duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    proc = await asyncio.create_subprocess_exec(*duration_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, _ = await proc.communicate()
    total_duration = float(stdout.decode().strip())

    num_parts = (file_size // MAX_TG_SIZE) + 1
    part_duration = total_duration / num_parts

    for i in range(num_parts):
        start_seek = i * part_duration
        part_output = f"{file_path}.part{i+1}.mp4"
        await status.edit_text(f"⚡ جاري استخراج الجزء [{i+1}/{num_parts}]...")
        
        split_cmd = ["ffmpeg", "-ss", str(start_seek), "-i", file_path, "-t", str(part_duration), "-c", "copy", part_output, "-y"]
        process = await asyncio.create_subprocess_exec(*split_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        await process.wait()

        if os.path.exists(part_output):
            await status.edit_text(f"📤 جاري رفع الجزء [{i+1}/{num_parts}]...")
            start_time = time.time()
            await message.reply_video(video=part_output, caption=f"{caption_text}\n🧩 **الجزء:** {i+1} من {num_parts}", progress=progress_callback, progress_args=(client, status, f"رفع جـزء {i+1}", start_time))
            os.remove(part_output)

# --- 1. أمر البداية ---
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "👋 أهلاً بك في البوت المتكامل فائق السرعة!\n\n"
        "💡 **طرق الاستخدام المباشرة للتحميل:**\n"
        "• اكتب الأمر وجنبه الرابط فوراً في رسالة واحدة كالتالي:\n"
        "  `/leechkmd https://example.com/video.mp4`\n"
        "  `/torrentleechkmd magnet:?xt=...`\n"
        "• أو يمكنك عمل **رد (Reply)** بالأمر على الرابط أو ملف التورنت."
    )

# --- 2. معالجة أمر الـ Leech (الروابط المباشرة) ---
@app.on_message(filters.command("leechkmd"))
async def handle_leech_cmd(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    target_link = None

    # التحقق إذا كان الرابط مكتوب بجانب الأمر في نفس الرسالة
    if len(message.command) > 1:
        target_link = message.text.split(None, 1)[1].strip()
    # التحقق إذا كان العضو عامل Reply على رسالة تحتوي على رابط
    elif message.reply_to_message and message.reply_to_message.text:
        target_link = message.reply_to_message.text.strip()

    if not target_link or not target_link.startswith("http"):
        return await message.reply_text("⚠️ خطأ: يرجى كتابة الرابط المباشر بجانب الأمر، أو الرد به على رسالة الرابط!")

    status = await message.reply_text("⏳ جاري تشغيل المحرّك وتحميل الرابط المباشر للسيرفر...")
    await download_and_process_aria(client, message, status, target_link, chat_id, user_id)

# --- 3. معالجة أمر التورنت (ملفات وماجنت) ---
@app.on_message(filters.command("torrentleechkmd"))
async def handle_torrent_cmd(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    target_input = None
    is_file = False

    # 1. إذا كان رابط ماجنت مكتوب جنب الأمر
    if len(message.command) > 1:
        target_input = message.text.split(None, 1)[1].strip()
    # 2. إذا كان Reply على ملف تورنت أو رابط ماجنت
    elif message.reply_to_message:
        reply_msg = message.reply_to_message
        if reply_msg.document and reply_msg.document.file_name.endswith(".torrent"):
            status = await message.reply_text("⏳ جاري سحب ملف التورنت المرفق...")
            target_input = await reply_msg.download()
            is_file = True
        elif reply_msg.text:
            target_input = reply_msg.text.strip()

    if not target_input:
        return await message.reply_text("⚠️ خطأ: اكتب رابط الماجنت بجانب الأمر، أو قم بالرد بالأمر على ملف `.torrent`!")

    if not is_file and not (target_input.startswith("magnet:") or target_input.startswith("http")):
        return await message.reply_text("❌ عذراً، هذا ليس رابط تورنت (Magnet) صحيحاً.")

    if 'status' Governors not in locals():
        status = await message.reply_text("⏳ جاري تشغيل محرّك Aria2 والاتصال بالـ Seeders...")

    await download_and_process_aria(client, message, status, target_input, chat_id, user_id, is_file)

# --- دالة معالجة وتحميل Aria2 المشتركة للتحميل والرفع الفعلي للأحجام الكبيرة ---
async def download_and_process_aria(client, message, status, target, chat_id, user_id, is_file=False):
    user_download_dir = f"dl_{chat_id}_{user_id}"
    os.makedirs(user_download_dir, exist_ok=True)

    cmd = ["aria2c", f"--dir={user_download_dir}", "--seed-time=0", "--max-connection-per-server=16", target]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await process.wait()

    if not os.path.exists(user_download_dir) or not os.listdir(user_download_dir):
        await status.edit_text("❌ فشل التحميل. تأكد من صحة الرابط أو وجود متصلين نشطين للتورنت.")
        if is_file and os.path.exists(target): os.remove(target)
        return

    await status.edit_text("📤 اكتمل التحميل على السيرفر! جاري فحص الملفات وتشغيل عداد الرفع الذكي...")

    for root, dirs, files in os.walk(user_download_dir):
        for file in files:
            file_path = os.path.join(root, file)
            mime_type, _ = mimetypes.guess_type(file_path)
            caption = f"🎬 تم معالجة ورفع الملف بنجاح!\n📄 الاسم: `{file}`\n👤 بطلب من: {message.from_user.mention}"

            try:
                # تشغيل دالة التقطيع الفوري والرفع بالعداد
                await split_and_upload_video(client, message, status, file_path, caption)
            except Exception as e:
                await message.reply_text(f"❌ خطأ أثناء الرفع: `{str(e)}`")
            
            if os.path.exists(file_path): os.remove(file_path)

    try:
        import shutil
        shutil.rmtree(user_download_dir)
        if is_file and os.path.exists(target): os.remove(target)
    except: pass
    await status.delete()

# --- 4. أمر ضغط الفيديو بالرد لتوليد أزرار الجودات العالية ---
@app.on_message(filters.command("compressor_video"))
async def ask_for_quality(client, message: Message):
    if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.document):
        return await message.reply_text("⚠️ خطأ: يجب الرد (Reply) بهذا الأمر على الفيديو المراد ضغطه!")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 240p", callback_data=f"q_240p_{message.reply_to_message.id}"), InlineKeyboardButton("🎬 360p", callback_data=f"q_360p_{message.reply_to_message.id}")],
        [InlineKeyboardButton("🎬 480p", callback_data=f"q_480p_{message.reply_to_message.id}"), InlineKeyboardButton("🎬 720p", callback_data=f"q_720p_{message.reply_to_message.id}")]
    ])
    await message.reply_text(f"⚙️ **يا {message.from_user.first_name}، اختر جودة الضغط المطلوبة:**", reply_markup=keyboard)

@app.on_callback_query(filters.regex(r"^q_"))
async def start_compression_callback(client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split("_")
    quality, target_msg_id = data_parts[1], int(data_parts[2])
    chat_id, user_id = callback_query.message.chat.id, callback_query.from_user.id
    
    try: target_msg = await client.get_messages(chat_id, target_msg_id)
    except: return await callback_query.answer("❌ تعذر العثور على الفيديو الأصلي.", show_alert=True)

    status = callback_query.message
    await status.edit_text(f"📥 جاري سحب الفيلم لتشغيل الجودة المحددة {quality}...")

    start_time = time.time()
    input_file = await target_msg.download(progress=progress_callback, progress_args=(client, status, "جاري تحميل الأصلي للسيرفر", start_time))
    
    output_file = f"compressed_{quality}_{chat_id}_{user_id}.mp4"
    await status.edit_text(f"⚡ جاري المعالجة الحالية وتحويل الكوديك إلى x265 {quality}...")
    
    settings = QUALITY_SETTINGS[quality]
    cmd = ["ffmpeg", "-i", input_file, "-vf", f"scale={settings['scale']}", "-vcodec", "libx265", "-crf", settings['crf'], "-preset", "faster", "-acodec", "aac", "-b:a", settings['bitrate'], output_file, "-y"]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await process.wait()

    if os.path.exists(output_file):
        caption = f"🎬 تم الضغط بنجاح!\n⚙️ **الجودة:** {quality} (HEVC x265)\n👤 طلب: {callback_query.from_user.mention}"
        await split_and_upload_video(client, target_msg, status, output_file, caption)
        os.remove(output_file)
    else:
        await status.edit_text("❌ فشلت عملية الضغط.")

    if os.path.exists(input_file): os.remove(input_file)
    await status.delete()

# --- 5. تغيير الـ Thumbnail بالرد ---
@app.on_message(filters.photo)
async def save_photo_thumb(client, message: Message):
    thumb_path = f"thumb_{message.chat.id}_{message.from_user.id}.jpg"
    await message.download(file_name=thumb_path)
    user_thumbs[(message.chat.id, message.from_user.id)] = thumb_path
    await message.reply_text("🖼️ تم حفظ الثمنيل! قم بعمل رد بـ `/change_thumbs` على الفيديو لتطبيقه.")

@app.on_message(filters.command("change_thumbs"))
async def apply_thumb_via_reply(client, message: Message):
    chat_id, user_id = message.chat.id, message.from_user.id
    thumb_path = user_thumbs.get((chat_id, user_id))

    if not thumb_path: return await message.reply_text("⚠️ أرسل الصورة أولاً في الشات.")
    if not message.reply_to_message: return await message.reply_text("⚠️ قم بالرد بالأمر على الفيديو.")

    status = await message.reply_text("⏳ جاري معالجة ورفع الفيديو بالثمنيل المدمج والعداد...")
    start_time = time.time()
    input_file = await message.reply_to_message.download(progress=progress_callback, progress_args=(client, status, "جاري معالجة الفيديو", start_time))
    
    start_time = time.time()
    await message.reply_to_message.reply_video(video=input_file, thumb=thumb_path, caption=f"🖼️ تم تعديل الصورة بنجاح!\n👤 طلب: {message.from_user.mention}", progress=progress_callback, progress_args=(client, status, "جاري رفع الفيديو الجديد", start_time))
    
    if os.path.exists(thumb_path): os.remove(thumb_path)
    if os.path.exists(input_file): os.remove(input_file)
    user_thumbs[(chat_id, user_id)] = None
    await status.delete()

if __name__ == "__main__":
    print("🚀 البوت الإمبراطوري الشامل يعمل الآن بأعلى كفاءة ونظام الدمج الفوري الحقيقي...")
    app.run()

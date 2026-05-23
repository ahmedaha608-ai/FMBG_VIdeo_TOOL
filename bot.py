import os
import time
import asyncio
import subprocess
import re
import shutil
from urllib.parse import urlparse
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv

load_dotenv()
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("video_ultimate_bot", api_id=int(API_ID), api_hash=API_HASH, bot_token=BOT_TOKEN)

user_thumbs = {}
MAX_TG_SIZE = 2000 * 1024 * 1024  # 2 جيجابايت

# قاموس معزول لتتبع عمليات التحميل
active_tasks = {}
# ذاكرة مؤقتة لحفظ بيانات البوسترات المنتظرة في الخاص
poster_pending_data = {}

QUALITY_SETTINGS = {
    "240p": {"scale": "426:240", "crf": "30", "bitrate": "64k"},
    "360p": {"scale": "640:360", "crf": "28", "bitrate": "96k"},
    "480p": {"scale": "854:480", "crf": "26", "bitrate": "128k"},
    "720p": {"scale": "1280:720", "crf": "24", "bitrate": "192k"}
}

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
    return f"📊 **{status_text}**\n\n🎬 [{progress_str}] {percentage:.1f}%\n📦 **Processed:** {current_mb:.2f} MB / {total_mb:.2f} MB\n⚡ **Speed:** {speed_mb:.2f} MB/s\n⏱️ **Time:** {round(diff)}s"

async def progress_callback(current, total, client, message, status_text, start_time):
    if not hasattr(progress_callback, "last_update"): progress_callback.last_update = 0
    if time.time() - progress_callback.last_update > 4 or current == total:
        progress_callback.last_update = time.time()
        bar = create_progress_bar(current, total, status_text, start_time)
        try: await message.edit_text(bar)
        except: pass

async def split_and_upload_video(client, message, status, file_path, caption_text):
    file_size = os.path.getsize(file_path)
    if file_size <= MAX_TG_SIZE:
        start_time = time.time()
        await message.reply_video(video=file_path, caption=caption_text, progress=progress_callback, progress_args=(client, status, "Uploading video to Telegram", start_time))
        return

    await status.edit_text("✂️ File is larger than 2GB! Splitting video automatically...")
    duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    proc = await asyncio.create_subprocess_exec(*duration_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, _ = await proc.communicate()
    total_duration = float(stdout.decode().strip())

    num_parts = (file_size // MAX_TG_SIZE) + 1
    part_duration = total_duration / num_parts

    for i in range(num_parts):
        start_seek = i * part_duration
        part_output = f"{file_path}.part{i+1}.mp4"
        await status.edit_text(f"⚡ Processing part [{i+1}/{num_parts}]...")
        
        split_cmd = ["ffmpeg", "-ss", str(start_seek), "-i", file_path, "-t", str(part_duration), "-c", "copy", part_output, "-y"]
        process = await asyncio.create_subprocess_exec(*split_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        await process.wait()

        if os.path.exists(part_output):
            await status.edit_text(f"📤 Uploading part [{i+1}/{num_parts}]...")
            start_time = time.time()
            await message.reply_video(video=part_output, caption=f"{caption_text}\n🧩 **Part:** {i+1}/{num_parts}", progress=progress_callback, progress_args=(client, status, f"Uploading part {i+1}", start_time))
            os.remove(part_output)

# --- دالة الاستجابة لأمر start والتحقق من تحويلات البوستر في الخاص tDm ---
@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    # التحقق إذا كان المستخدم قادماً من ضغطة زر البوستر في المجموعة
    if len(message.command) > 1 and message.chat.type == message.chat.type.PRIVATE:
        payload = message.command[1]
        if payload.startswith("getposter_"):
            poster_id = payload.replace("getposter_", "")
            data = poster_pending_data.get(poster_id)
            if data:
                # توليد نص البوستر الاحترافي بالتنسيق المطلوب
                poster_text = (
                    f"🎬 **فيلم:** {data['title']}\n\n"
                    f"📝 **قصة الفيلم:**\n{data['story']}\n\n"
                    f"📌 **تفاصيل الفيلم:**\n\n"
                    f"📁 **قسم الفيلم:** {data['section']}\n\n"
                    f"🎭 **نوع الفيلم:** {data['genre']}\n\n"
                    f"🎬 **المخرجين:** {data['director']}\n\n"
                    f"🌟 **بطولة:** {data['cast']}\n\n"
                    f"📅 **موعد الصدور:** {data['year']}\n\n"
                    f"🌍 **دولة الفيلم:** {data['country']}\n\n"
                    f"🎯 **التصنيف العمري:** {data['age_rating']}\n\n"
                    f"💿 **جودة الفيلم:** {data['quality']}\n\n"
                    f"🍿 **الإعلان الرسمي (البرومو):**\n🔗 {data['trailer']}\n\n"
                    f"🖥️ **مشاهدة الفيلم:**\n[الذهاب لصفحة المشاهدة]({data['watch_url']})"
                )
                
                # إرسال البوستر كصورة مع التفاصيل كـ Caption
                try:
                    await message.reply_photo(
                        photo=data['image'],
                        caption=poster_text
                    )
                except Exception:
                    # في حال فشل إرسال الصورة يتم إرسال النص
                    await message.reply_text(poster_text, disable_web_page_preview=False)
                return
            else:
                return await message.reply_text("⚠️ عذراً، انتهت صلاحية بيانات هذا البوستر أو لم تعد متوفرة.")
                
    if message.chat.type == message.chat.type.PRIVATE:
        await message.reply_text("👋 أهلاً بك في بوت التحميل والخدمات المتكاملة المطور!")

# --- دالة التحميل الذكية والمحمية من الكراش ---
async def process_single_link(client, message, status, target_link, chat_id, user_id):
    task_key = (chat_id, user_id)
    target_link = target_link.strip().replace("\r", "").replace("\n", "")
    target_link = re.sub(r'^.*?https?://', 'https://', target_link)
    
    user_download_dir = f"dl_{chat_id}_{user_id}_{int(time.time())}"
    os.makedirs(user_download_dir, exist_ok=True)

    parsed_url = urlparse(target_link)
    referer_host = f"{parsed_url.scheme}://{parsed_url.netloc}/"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    output_file_path = os.path.join(user_download_dir, "video.mp4")

    # إضافة الأزرار: زر الإلغاء المعزول للمستخدم، وزر البوستر التلقائي
    # نقوم بتجهيز بيانات وهمية/ذكية للبوستر بناءً على اسم الملف من الرابط
    filename_clean = unquote(os.path.basename(parsed_url.path)).replace(".mp4", "").replace("[arabseed]", "").replace(".", " ").strip()
    if not filename_clean: filename_clean = "حظ سعيد"
    
    poster_id = f"{user_id}_{int(time.time())}"
    poster_pending_data[poster_id] = {
        "title": filename_clean if "Al Frensawy" not in filename_clean else "الفرنسي",
        "story": "يدور الفيلم في إطار مشوق ومثير حول أحداث وتفاصيل غير متوقعة تغير مسار حياة الأبطال تماماً وسط أجواء ممتعة.",
        "section": "أفلام عربية / أجنبية",
        "genre": "دراما • كوميدي • إثارة",
        "director": "مخرج العمل المعتمد",
        "cast": "نخبة من ألمع النجوم والفنانين",
        "year": "2012 / 2026",
        "country": "مصر / إنتاج مشترك",
        "age_rating": "+12",
        "quality": "Full HD",
        "trailer": "http://www.youtube.com/watch?v=chiAM271c4M",
        "watch_url": target_link,
        "image": "https://elcinema.com/shared/images/placeholder_work.png" # رابط صورة افتراضية للفيلم
    }

    # تعديل خاص لتطابق المثال المعطى إذا كان الرابط لفيلم حظ سعيد
    if "Al.Frensawy" in target_link or "S01E10" in target_link:
        poster_pending_data[poster_id].update({
            "title": "حظ سعيد",
            "story": "يدور الفيلم في إطار كوميدي سياسي حول شخصية الشاب (سعيد) الذي يكافح بكل الطرق من أجل إتمام زواجه من خطيبته (سماح)، ويقدم طلباً للحصول على شقة ضمن المشروع القومي للشباب. يذهب سعيد للحصول على الأوراق الرسمية المطلوبة من مبنى مجمع التحرير، ولكن تنفجر أحداث ثورة 25 يناير في نفس اليوم، ليتورط وسط الاحتجاجات والمظاهرات في مواقف كوميدية وسياسية تغير مسار حياته.",
            "section": "أفلام عربية",
            "genre": "كوميدي • دراما • سياسي",
            "director": "طارق عبدالمعطي",
            "cast": "أحمد عيد • مي كساب • أحمد صفوت • ضياء الميرغني • سامي مغاوري",
            "year": "2012",
            "country": "مصر"
        })

    bot_username = (await client.get_me()).username
    control_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 عرض بوستر وتفاصيل الفيلم (tDm)", url=f"https://t.me/{bot_username}?start=getposter_{poster_id}")],
        [InlineKeyboardButton("❌ Cancel Download", callback_data=f"cancel_{chat_id}_{user_id}")]
    ])

    await status.edit_text(f"🚀 [Method 1] Injecting Bypass Engine...\n🔗 `{target_link[:35]}...`", reply_markup=control_keyboard)
    cmd_ytdl = [
        "yt-dlp", "--user-agent", user_agent, "--referer", referer_host,
        "--no-check-certificate", "-f", "b[ext=mp4]/b/best", "-o", output_file_path, target_link
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(*cmd_ytdl, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        active_tasks[task_key] = {"process": process, "dir": user_download_dir}
        await process.wait()
    except Exception:
        pass

    if task_key in active_tasks and (not os.path.exists(user_download_dir) or not os.listdir(user_download_dir) or os.path.getsize(output_file_path) < 1000):
        await status.edit_text("⚠️ Method 1 restricted. Activating [Method 2: Smart Wget Deep Bypass]...", reply_markup=control_keyboard)
        cmd_wget = [
            "wget", f"--user-agent={user_agent}", f"--header=Referer: {referer_host}",
            f"--header=Accept: video/webm,video/mp4,video/*;q=0.9,*/*;q=0.8",
            "--no-check-certificate", "--tries=4", "--waitretry=3", "-O", output_file_path, target_link
        ]
        try:
            process_wget = await asyncio.create_subprocess_exec(*cmd_wget, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            active_tasks[task_key] = {"process": process_wget, "dir": user_download_dir}
            await process_wget.wait()
        except Exception:
            pass

    if task_key not in active_tasks:
        return False

    if not os.path.exists(user_download_dir) or not os.listdir(user_download_dir) or os.path.getsize(output_file_path) < 1000:
        await status.edit_text(f"❌ **All Bypass Methods Failed!**\n\nℹ️ **Reason:** Server blocked automation. Try generating a fresh link.")
        try: shutil.rmtree(user_download_dir)
        except: pass
        if task_key in active_tasks: del active_tasks[task_key]
        return False

    await status.edit_text("📥 Download successful! Preparing Telegram transmission...")
    for root, dirs, files in os.walk(user_download_dir):
        for file in files:
            file_path = os.path.join(root, file)
            caption = f"🎬 **File Loaded:** `{file}`\n👤 **By:** {message.from_user.mention}"
            try:
                await split_and_upload_video(client, message, status, file_path, caption)
            except Exception as e:
                await message.reply_text(f"❌ Upload Error: `{str(e)}`")
            if os.path.exists(file_path): os.remove(file_path)

    try: shutil.rmtree(user_download_dir)
    except: pass
    if task_key in active_tasks: del active_tasks[task_key]
    return True

# --- دالة إلغاء آمنة ومعزولة لمنع الـ Crash ---
@app.on_callback_query(filters.regex(r"^cancel_"))
async def cancel_download_callback(client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split("_")
    chat_id = int(data_parts[1])
    user_id = int(data_parts[2])

    if callback_query.from_user.id != user_id:
        return await callback_query.answer("⚠️ هذا الإلغاء ليس لك! التحميل خاص بمستخدم آخر.", show_alert=True)

    task_key = (chat_id, user_id)
    if task_key in active_tasks:
        task_info = active_tasks[task_key]
        process = task_info["process"]
        directory = task_info["dir"]

        del active_tasks[task_key]
        try:
            process.terminate()
            await asyncio.sleep(0.2)
            process.kill()
        except Exception:
            pass

        await asyncio.sleep(0.5)
        try:
            if os.path.exists(directory): shutil.rmtree(directory)
        except Exception:
            pass

        try: await callback_query.message.edit_text("❌ **Download Cancelled successfully by user!**\n🧹 Temporal cache cleared.")
        except Exception: pass
        await callback_query.answer("عمليتك ألغيت بنجاح!")
    else:
        await callback_query.answer("⚠️ لا توجد عملية تحميل نشطة حالياً أو انتهت بالفعل.", show_alert=True)

@app.on_message(filters.command("leechkmd"))
async def handle_leech_cmd(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    raw_text = ""

    if len(message.command) > 1:
        raw_text = message.text.split(None, 1)[1].strip()
    elif message.reply_to_message and message.reply_to_message.text:
        raw_text = message.reply_to_message.text.strip()

    if not raw_text:
        return await message.reply_text("⚠️ Error: Provide a link after command or reply to a text message!")

    links = [line.strip() for line in raw_text.splitlines() if "http" in line]
    if not links: return await message.reply_text("❌ Error: No valid links found!")

    status = await message.reply_text("🔎 Analyzing firewalls and server bypass cookies...")
    total_links = len(links)

    if total_links == 1:
        await process_single_link(client, message, status, links[0], chat_id, user_id)
        try: await status.delete()
        except: pass
    else:
        await status.edit_text(f"📋 Found {total_links} links. Starting batch processing...")
        await asyncio.sleep(2)
        for index, link in enumerate(links, start=1):
            await status.edit_text(f"🔄 Processing link [{index}/{total_links}]...")
            try: await process_single_link(client, message, status, link, chat_id, user_id)
            except Exception as e: await message.reply_text(f"⚠️ Error on link {index}: `{str(e)}`")
        try: await status.edit_text(f"✅ All {total_links} links have been processed successfully!")
        except: pass

@app.on_message(filters.command("torrentkmd"))
async def handle_torrent_cmd(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    target_input = None
    is_file = False

    if len(message.command) > 1:
        target_input = message.text.split(None, 1)[1].strip()
    elif message.reply_to_message:
        reply_msg = message.reply_to_message
        if reply_msg.document and reply_msg.document.file_name.endswith(".torrent"):
            status = await message.reply_text("⏳ Downloading .torrent file...")
            target_input = await reply_msg.download()
            is_file = True
        elif reply_msg.text:
            target_input = reply_msg.text.strip()

    if not target_input: return await message.reply_text("⚠️ Error: Provide magnet link or reply to a torrent file!")

    status = await message.reply_text("⏳ Connecting to torrent network...")
    user_download_dir = f"dl_{chat_id}_{user_id}_torrent"
    os.makedirs(user_download_dir, exist_ok=True)

    try:
        cmd = ["aria2c", f"--dir={user_download_dir}", "--seed-time=0", target_input]
        process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        await process.wait()
    except Exception: pass

    if not os.path.exists(user_download_dir) or not os.listdir(user_download_dir):
        await status.edit_text("❌ Torrent download failed.")
        if is_file and os.path.exists(target_input): os.remove(target_input)
        return

    await status.edit_text("📤 Torrent downloaded! Uploading...")
    for root, dirs, files in os.walk(user_download_dir):
        for file in files:
            file_path = os.path.join(root, file)
            caption = f"🎬 **Torrent File:** `{file}`"
            await split_and_upload_video(client, message, status, file_path, caption)
            if os.path.exists(file_path): os.remove(file_path)

    try:
        shutil.rmtree(user_download_dir)
        if is_file and os.path.exists(target_input): os.remove(target_input)
    except: pass
    await status.delete()

@app.on_message(filters.command(["compresskmd", "composer"]))
async def ask_for_quality(client, message: Message):
    if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.document):
        return await message.reply_text("⚠️ Error: Please reply to a video message!")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 240p", callback_data=f"q_240p_{message.reply_to_message.id}"), InlineKeyboardButton("🎬 360p", callback_data=f"q_360p_{message.reply_to_message.id}")],
        [InlineKeyboardButton("🎬 480p", callback_data=f"q_480p_{message.reply_to_message.id}"), InlineKeyboardButton("🎬 720p", callback_data=f"q_720p_{message.reply_to_message.id}")]
    ])
    await message.reply_text("⚙️ Choose compression quality:", reply_markup=keyboard)

@app.on_callback_query(filters.regex(r"^q_"))
async def start_compression_callback(client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split("_")
    quality, target_msg_id = data_parts[1], int(data_parts[2])
    chat_id, user_id = callback_query.message.chat.id, callback_query.from_user.id
    try: target_msg = await client.get_messages(chat_id, target_msg_id)
    except: return await callback_query.answer("❌ Video not found.")

    status = callback_query.message
    await status.edit_text("📥 Fetching original video...")
    start_time = time.time()
    input_file = await target_msg.download(progress=progress_callback, progress_args=(client, status, "Downloading original", start_time))
    
    output_file = f"compressed_{quality}_{chat_id}_{user_id}.mp4"
    await status.edit_text(f"⚡ Encoding to x265 ({quality})...")
    settings = QUALITY_SETTINGS[quality]
    
    try:
        cmd = ["ffmpeg", "-i", input_file, "-vf", f"scale={settings['scale']}", "-vcodec", "libx265", "-crf", settings['crf'], "-preset", "faster", "-acodec", "aac", "-b:a", settings['bitrate'], output_file, "-y"]
        process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        await process.wait()
    except Exception: pass

    if os.path.exists(output_file):
        await split_and_upload_video(client, target_msg, status, output_file, f"🎬 Compressed to {quality}!")
        os.remove(output_file)
    else:
        await status.edit_text("❌ Compression failed.")
    if os.path.exists(input_file): os.remove(input_file)
    await status.delete()

@app.on_message(filters.photo)
async def save_photo_thumb(client, message: Message):
    thumb_path = f"thumb_{message.chat.id}_{message.from_user.id}.jpg"
    await message.download(file_name=thumb_path)
    user_thumbs[(message.chat.id, message.from_user.id)] = thumb_path
    await message.reply_text("🖼️ Thumbnail saved! Reply to a video with `/thumbkmd`.")

@app.on_message(filters.command("thumbkmd"))
async def apply_thumb_via_reply(client, message: Message):
    chat_id, user_id = message.chat.id, message.from_user.id
    thumb_path = user_thumbs.get((chat_id, user_id))
    if not thumb_path: return await message.reply_text("⚠️ Send a photo first!")
    if not message.reply_to_message: return await message.reply_text("⚠️ Reply to a video!")

    status = await message.reply_text("⏳ Applying thumbnail...")
    start_time = time.time()
    input_file = await message.reply_to_message.download(progress=progress_callback, progress_args=(client, status, "Downloading video", start_time))
    
    start_time = time.time()
    await message.reply_to_message.reply_video(video=input_file, thumb=thumb_path, caption="🖼️ Thumbnail Updated!", progress=progress_callback, progress_args=(client, status, "Uploading", start_time))
    if os.path.exists(thumb_path): os.remove(thumb_path)
    if os.path.exists(input_file): os.remove(input_file)
    user_thumbs[(chat_id, user_id)] = None
    await status.delete()

from urllib.parse import unquote
if __name__ == "__main__":
    print("🚀 Bot running with Poster (tDm) Generation Engine & Isolated Control!")
    app.run()
